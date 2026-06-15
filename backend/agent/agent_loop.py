import json
import anthropic
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.agent.prompts import SYSTEM_PROMPT, build_user_prompt
from backend.agent.logger import AgentLogger
from backend.agent.critique import SelfCritique
from backend.agent.token_counter import count_tokens, estimate_cost
from backend.agent.embeddings import embed_and_store, search_similar
from backend.tools import ALL_TOOLS, TOOLS_MAP
from backend.db import crud


class AgentLoop:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.critique = SelfCritique()
        self.tools = [tool.to_claude_tool() for tool in ALL_TOOLS]

    async def run(
        self,
        session_id: int,
        topic: str,
        db: AsyncSession,
        additional_instructions: str = "",
        depth: str = "medium",
        language: str = "en"
    ) -> AsyncGenerator[str, None]:

        logger = AgentLogger(session_id)

        await crud.update_session_status(db, session_id, "running")
        await db.commit()

        # ─────────────────────────────────────────────
        # Qdrant-dan oxsar menbeler tap
        # Əvvəlki axtarışlarda tapılmış oxşar mənbələri
        # agent-ə context kimi ver — token qənaət edir
        # ─────────────────────────────────────────────
        similar_context = ""
        try:
            similar_sources = await search_similar(
                query=topic,
                session_id=None,  # Bütün sessionlarda axtar
                limit=5
            )
            if similar_sources:
                similar_context = "\n\n## Previously Found Related Sources\n"
                similar_context += "These sources were found in previous research sessions on similar topics. "
                similar_context += "You can use this context to avoid redundant searches:\n\n"
                for i, src in enumerate(similar_sources, 1):
                    score = src.get("score", 0)
                    url = src.get("url", "")
                    snippet = src.get("snippet", "")[:200]
                    source_type = src.get("source_type", "web")
                    similar_context += f"{i}. [{source_type}] {url} (similarity: {score:.2f})\n"
                    if snippet:
                        similar_context += f"   Preview: {snippet[:150]}...\n"
                similar_context += "\nUse these sources as additional context. Skip re-reading them unless you need more detail."
                logger.log_thought(f"Qdrant-dan {len(similar_sources)} oxşar mənbə tapıldı")
        except Exception as e:
            logger.log_error(f"Qdrant axtarış xətası: {e}")
            similar_context = ""

        user_prompt = build_user_prompt(
            topic=topic,
            additional_instructions=additional_instructions,
            depth=depth,
            language=language
        )

        # Oxşar mənbələr varsa prompt-a əlavə et
        if similar_context:
            user_prompt += similar_context

        messages = [{"role": "user", "content": user_prompt}]
        total_tokens = 0
        total_tiktoken = 0
        sources_count = 0
        final_report = ""

        visited_read_urls = set()
        saved_source_urls = set()

        max_iterations_map = {"basic": 2, "medium": 3, "deep": 5}
        max_iterations = max_iterations_map.get(depth, 3)
        iteration = 0

        try:
            while iteration < max_iterations:
                iteration += 1

                response = self.client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=2048,
                    system=SYSTEM_PROMPT,
                    tools=self.tools,
                    messages=messages
                )

                total_tokens += response.usage.input_tokens + response.usage.output_tokens

                messages.append({
                    "role": "assistant",
                    "content": response.content
                })

                tool_results = []

                for block in response.content:

                    if block.type == "text" and block.text.strip():
                        block_tokens = count_tokens(block.text)
                        total_tiktoken += block_tokens

                        logger.log_thought(block.text)
                        logger.log_tokens(
                            response.usage.input_tokens,
                            response.usage.output_tokens
                        )

                        await crud.create_step(
                            db=db,
                            session_id=session_id,
                            step_type="thought",
                            content=block.text,
                            tokens_used=block_tokens
                        )
                        await db.commit()

                        yield self._sse({"type": "thought", "content": block.text})

                        if (not final_report and
                            len(block.text) > 300 and
                            "#" in block.text and
                            "##" in block.text):
                            final_report = block.text

                    elif block.type == "tool_use":
                        tool_name = block.name
                        tool_input = block.input

                        if tool_name in ("read_url", "read_pdf"):
                            url = tool_input.get("url") or tool_input.get("source", "")
                            if url in visited_read_urls:
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": block.id,
                                    "content": "Already visited this URL, skipping."
                                })
                                continue
                            visited_read_urls.add(url)

                        logger.log_tool_use(tool_name, tool_input)

                        await crud.create_step(
                            db=db,
                            session_id=session_id,
                            step_type="tool_use",
                            tool_name=tool_name,
                            content=json.dumps(tool_input)
                        )
                        await db.commit()

                        yield self._sse({
                            "type": "tool_use",
                            "tool": tool_name,
                            "input": tool_input
                        })

                        tool = TOOLS_MAP.get(tool_name)
                        result = await tool.run(**tool_input) if tool else None

                        if result and result.success:
                            logger.log_tool_result(tool_name, True, result.content)

                            content_tokens = count_tokens(result.content)
                            total_tiktoken += content_tokens

                            await crud.create_step(
                                db=db,
                                session_id=session_id,
                                step_type="tool_result",
                                tool_name=tool_name,
                                content=result.content,
                                tokens_used=content_tokens
                            )

                            if result.source_url and result.source_url not in saved_source_urls:
                                saved_source_urls.add(result.source_url)
                                sources_count += 1

                                source = await crud.create_source(
                                    db=db,
                                    session_id=session_id,
                                    url=result.source_url,
                                    source_type=result.source_type or "web",
                                    snippet=result.content[:300],
                                    credibility_score=self._credibility(result.source_type)
                                )
                                await db.commit()

                                await embed_and_store(
                                    source_id=source.id,
                                    session_id=session_id,
                                    url=result.source_url,
                                    title=None,
                                    snippet=result.content[:500],
                                    source_type=result.source_type or "web",
                                    credibility_score=self._credibility(result.source_type)
                                )
                            else:
                                await db.commit()

                            yield self._sse({
                                "type": "tool_result",
                                "tool": tool_name,
                                "success": True,
                                "content": result.content[:300]
                            })

                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": result.content
                            })

                        else:
                            error_msg = result.error if result else f"{tool_name} tapilmadi"
                            logger.log_error(error_msg)

                            await crud.create_step(
                                db=db,
                                session_id=session_id,
                                step_type="tool_result",
                                tool_name=tool_name,
                                content=error_msg
                            )
                            await db.commit()

                            yield self._sse({
                                "type": "tool_result",
                                "tool": tool_name,
                                "success": False,
                                "content": error_msg
                            })

                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": f"Error: {error_msg}"
                            })

                if tool_results:
                    messages.append({"role": "user", "content": tool_results})

                if response.stop_reason == "end_turn":
                    if not final_report:
                        for block in response.content:
                            if block.type == "text" and block.text.strip():
                                final_report = block.text
                                break

                    if final_report:
                        async for event in self._finish_report(
                            db, session_id, topic, final_report,
                            total_tokens, total_tiktoken, sources_count,
                            depth, messages, logger
                        ):
                            yield event
                        return
                    else:
                        yield self._sse({"type": "done"})
                        return

                elif final_report and not tool_results:
                    async for event in self._finish_report(
                        db, session_id, topic, final_report,
                        total_tokens, total_tiktoken, sources_count,
                        depth, messages, logger
                    ):
                        yield event
                    return

            if final_report:
                async for event in self._finish_report(
                    db, session_id, topic, final_report,
                    total_tokens, total_tiktoken, sources_count,
                    depth, messages, logger
                ):
                    yield event
                return

            logger.log_error("Agent maksimum iterasiyaya catdi")
            await crud.update_session_status(db, session_id, "failed")
            await db.commit()
            yield self._sse({"type": "error", "content": "Axtarish tamamlana bilmedi."})
            yield self._sse({"type": "done"})

        except Exception as e:
            logger.log_error(str(e))
            try:
                await crud.update_session_status(db, session_id, "failed")
                await db.commit()
            except Exception:
                pass
            yield self._sse({"type": "error", "content": str(e)})
            yield self._sse({"type": "done"})

    async def _finish_report(
        self,
        db, session_id, topic, final_report,
        total_tokens, total_tiktoken, sources_count,
        depth, messages, logger
    ):
        input_t = total_tokens // 2
        output_t = total_tokens // 2
        cost = estimate_cost(input_t, output_t, "claude-haiku")
        logger.log_tokens(input_t, output_t)

        yield self._sse({"type": "critique", "content": "Hesabat yoxlanilir..."})

        approved, critique_result = await self.critique.evaluate(topic, final_report)

        await crud.create_step(
            db=db,
            session_id=session_id,
            step_type="critique",
            content=critique_result
        )
        await db.commit()

        yield self._sse({"type": "critique", "content": critique_result})

        should_save = approved or depth == "basic"

        if should_save:
            logger.log_final_report(final_report)

            await crud.update_session_report(
                db=db,
                session_id=session_id,
                report=final_report,
                token_count=total_tokens,
                sources_count=sources_count,
                tiktoken_count=total_tiktoken,
                estimated_cost=cost
            )
            await db.commit()

            yield self._sse({"type": "final_report", "content": final_report})
            yield self._sse({"type": "done"})

        else:
            messages.append({
                "role": "user",
                "content": f"Improve the report. Issues: {critique_result}\nWrite improved version now."
            })

    def _sse(self, data: dict) -> str:
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

    def _credibility(self, source_type: str | None) -> float:
        scores = {
            "arxiv": 0.95,
            "wikipedia": 0.75,
            "web": 0.60,
            "pdf": 0.70
        }
        return scores.get(source_type or "web", 0.60)