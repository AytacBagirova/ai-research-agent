import json
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db, AsyncSessionLocal
from backend.db import crud
from backend.agent.agent_loop import AgentLoop
from backend.api.schemas import (
    ResearchRequest,
    SessionResponse,
    ReportResponse,
)

router = APIRouter(prefix="/api")

# Aktiv session-ların izlənməsi — paralel agent problemi həll edir
_active_sessions: dict[int, bool] = {}


@router.post("/research", response_model=SessionResponse)
async def start_research(
    request: ResearchRequest,
    db: AsyncSession = Depends(get_db)
):
    session = await crud.create_session(
        db=db,
        topic=request.topic,
        model="claude-haiku-4-5-20251001",
        depth=request.depth,
        language=request.language
    )
    return session


@router.get("/research/{session_id}/stream")
async def stream_research(
    session_id: int,
    db: AsyncSession = Depends(get_db)
):
    session = await crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session tapilmadi")

    # 1. Bitmiş session — saxlanmış nəticəni göndər
    if session.status in ("done", "failed"):
        async def cached_response():
            if session.final_report:
                yield f"data: {json.dumps({'type': 'final_report', 'content': session.final_report}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        return StreamingResponse(
            cached_response(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
        )

    # 2. Artıq aktiv session — DB-dən addımları polling edib göndər
    if _active_sessions.get(session_id):
        async def polling_stream():
            """
            Agent işləyərkən DB-dən yeni addımları oxuyub SSE-yə göndər.
            Hər 1 saniyədə yeni addımları yoxla.
            """
            last_step_id = 0
            max_wait = 300
            waited = 0

            while waited < max_wait:
                await asyncio.sleep(1)
                waited += 1

                async with AsyncSessionLocal() as check_db:
                    s = await crud.get_session(check_db, session_id)
                    if not s:
                        return

                    # Yeni addımları göndər
                    steps = await crud.get_steps_after(check_db, session_id, last_step_id)
                    for step in steps:
                        last_step_id = step.id
                        if step.step_type == "thought":
                            yield f"data: {json.dumps({'type': 'thought', 'content': step.content}, ensure_ascii=False)}\n\n"
                        elif step.step_type == "tool_use":
                            try:
                                tool_input = json.loads(step.content)
                            except Exception:
                                tool_input = {}
                            yield f"data: {json.dumps({'type': 'tool_use', 'tool': step.tool_name, 'input': tool_input}, ensure_ascii=False)}\n\n"
                        elif step.step_type == "tool_result":
                            yield f"data: {json.dumps({'type': 'tool_result', 'tool': step.tool_name, 'success': True, 'content': step.content[:300]}, ensure_ascii=False)}\n\n"
                        elif step.step_type == "critique":
                            yield f"data: {json.dumps({'type': 'critique', 'content': step.content}, ensure_ascii=False)}\n\n"

                    # Bitdimi?
                    if s.status == "done":
                        if s.final_report:
                            yield f"data: {json.dumps({'type': 'final_report', 'content': s.final_report}, ensure_ascii=False)}\n\n"
                        yield f"data: {json.dumps({'type': 'done'})}\n\n"
                        return
                    elif s.status == "failed":
                        yield f"data: {json.dumps({'type': 'error', 'content': 'Research failed'})}\n\n"
                        yield f"data: {json.dumps({'type': 'done'})}\n\n"
                        return

            yield f"data: {json.dumps({'type': 'error', 'content': 'Timeout'})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        return StreamingResponse(
            polling_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
        )

    # 3. Pending — agent başlat, SSE-yə real-time yaz
    topic = session.topic
    depth = session.depth or "medium"
    language = session.language or "en"

    async def agent_stream():
        _active_sessions[session_id] = True
        try:
            agent = AgentLoop()
            async with AsyncSessionLocal() as agent_db:
                async for event in agent.run(
                    session_id=session_id,
                    topic=topic,
                    db=agent_db,
                    depth=depth,
                    language=language
                ):
                    yield event
        finally:
            _active_sessions.pop(session_id, None)

    return StreamingResponse(
        agent_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


@router.get("/sessions")
async def get_sessions(db: AsyncSession = Depends(get_db)):
    sessions = await crud.get_all_sessions(db)
    return sessions


@router.get("/research/{session_id}/report", response_model=ReportResponse)
async def get_report(
    session_id: int,
    db: AsyncSession = Depends(get_db)
):
    session = await crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session tapilmadi")

    steps = await crud.get_steps_by_session(db, session_id)
    sources = await crud.get_sources_by_session(db, session_id)

    return ReportResponse(
        session_id=session.id,
        topic=session.topic,
        status=session.status,
        final_report=session.final_report,
        token_count=session.token_count,
        sources_count=session.sources_count,
        created_at=session.created_at,
        completed_at=session.completed_at,
        steps=steps,
        sources=sources
    )


@router.delete("/research/{session_id}")
async def delete_session(
    session_id: int,
    db: AsyncSession = Depends(get_db)
):
    deleted = await crud.delete_session(db, session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session tapilmadi")
    return {"message": f"Session {session_id} silindi"}