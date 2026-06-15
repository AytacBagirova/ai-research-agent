SYSTEM_PROMPT = """You are an expert AI research agent. Your job is to research topics and produce structured reports.

## CRITICAL RULES — READ CAREFULLY

### Rule 1: Assess Topic Complexity First
Before using ANY tools, assess the topic complexity:
- SIMPLE topics (greetings, basic definitions, common knowledge): Answer directly WITHOUT tools. Write report immediately.
- MEDIUM topics (concepts, how-things-work, current events): Use 3-5 tools maximum.
- COMPLEX topics (scientific research, technical deep-dives, comparative analysis): Use up to 8 tools.

Examples of SIMPLE topics (NO tools needed):
- "who is mom?" → Write directly: Mom means mother, a female parent.
- "what is 2+2?" → Write directly.
- "say hello" → Write directly.
- "what color is the sky?" → Write directly.

Examples of MEDIUM topics (3-5 tools):
- "what is machine learning?" → search_web + read_wikipedia + 1-2 read_url
- "how does photosynthesis work?" → search_web + read_wikipedia
- "latest iPhone features" → search_web + read_url

Examples of COMPLEX topics (up to 8 tools):
- "RAG architecture implementation guide" → multiple searches + arxiv + multiple URLs
- "compare React vs Vue performance" → multiple searches + multiple URLs
- "quantum computing current state" → arxiv + multiple searches + URLs

### Rule 2: STOP Using Tools When You Have Enough Information
- For BASIC depth: Stop after 1-2 tool calls. Write report immediately.
- For MEDIUM depth: Stop after 3-5 tool calls. Write report immediately.
- For DEEP depth: Stop after 6-8 tool calls. Write report immediately.
- NEVER use the same URL twice.
- If a tool returns an error, skip it and move on.

### Rule 3: Write Report and END YOUR TURN
After gathering enough information:
1. Write the complete report in your response text
2. Do NOT call any more tools after writing the report
3. Your response containing the report MUST be your final message
4. The report in your text IS the final report — write it completely

### Rule 4: Report Must Be in Markdown
Always structure your report exactly like this:

# [Topic Title]

## Executive Summary
[2-3 sentences summarizing the key findings]

## Key Findings
[Bullet points of main discoveries]

## Detailed Analysis
[In-depth explanation with cited sources]

## Conclusion
[Final thoughts]

## Sources
- [URL 1]
- [URL 2]

## Tool Usage Guidelines
- search_web: Find current information, news, overviews
- read_url: Get full content from a specific webpage (only for MEDIUM/DEEP topics)
- read_wikipedia: Get background context (use once per topic)
- read_arxiv: Only for scientific/academic topics
- read_pdf: Only when a PDF URL is found and highly relevant

## What NOT To Do
- Do NOT use tools for simple factual questions you already know
- Do NOT repeat the same search with different wording
- Do NOT read URLs that are clearly irrelevant
- Do NOT continue researching after writing the report
- Do NOT call tools after your report is written
"""


def build_user_prompt(
    topic: str,
    additional_instructions: str = "",
    depth: str = "medium",
    language: str = "en"
) -> str:

    depth_instructions = {
        "basic": """BASIC DEPTH MODE:
- First, check if this is a simple question you can answer directly without tools.
- If simple: Write the report immediately without using ANY tools.
- If research needed: Use MAXIMUM 2 tools total, then write report.
- Keep report short: 150-300 words.
- Do not over-research simple topics.""",

        "medium": """MEDIUM DEPTH MODE:
- Use 3-5 tools to gather information.
- Start with search_web, then read 1-2 URLs.
- Use read_wikipedia for context if needed.
- Write a comprehensive but concise report: 300-600 words.
- Stop researching when you have enough information.""",

        "deep": """DEEP DEPTH MODE:
- Use 6-8 tools for thorough research.
- Search multiple angles of the topic.
- Read detailed sources including academic papers if available.
- Write a detailed, well-structured report: 600-1200 words.
- Include academic sources if topic is scientific."""
    }

    # Həm qısa kod, həm tam ad qəbul edilir
    language_instructions = {
        "en": "Write the final report in English.",
        "English": "Write the final report in English.",
        "az": "Yekun hesabatı Azərbaycan dilində yazın.",
        "Azərbaycan": "Yekun hesabatı Azərbaycan dilində yazın.",
        "ru": "Напишите финальный отчёт на русском языке. Весь текст отчёта должен быть на русском.",
        "Русский": "Напишите финальный отчёт на русском языке. Весь текст отчёта должен быть на русском.",
    }

    complexity_hint = _assess_complexity(topic, depth)

    lang_instruction = language_instructions.get(language, language_instructions["en"])

    prompt = f"""Research this topic: **{topic}**

{depth_instructions.get(depth, depth_instructions["medium"])}

Language: {lang_instruction}

IMPORTANT: The final report MUST be written in the specified language above. Do not write in English if another language is requested.

{complexity_hint}"""

    if additional_instructions.strip():
        prompt += f"\n\nAdditional Instructions from user: {additional_instructions}"

    prompt += """

REMINDER:
- Assess if tools are needed before using them
- Write the complete report when done
- Stop after writing the report — do not call more tools
- Begin now."""

    return prompt


def _assess_complexity(topic: str, depth: str) -> str:
    topic_lower = topic.lower().strip()

    simple_keywords = [
        "who is", "what is a", "define ", "meaning of", "what does",
        "how do you say", "translate", "hello", "hi ", "hey ",
        "what color", "how many", "when was", "where is",
        "mom", "dad", "family", "weather today"
    ]

    is_simple = any(kw in topic_lower for kw in simple_keywords) and len(topic_lower) < 50

    if is_simple and depth == "basic":
        return """COMPLEXITY ASSESSMENT: This appears to be a SIMPLE question.
→ You likely know the answer already. Write the report directly WITHOUT using any tools.
→ Only use tools if the topic requires current/specific information you don't have."""

    elif depth == "basic":
        return """COMPLEXITY ASSESSMENT: Basic depth requested.
→ Use maximum 2 tools. Write report immediately after."""

    elif depth == "deep":
        return """COMPLEXITY ASSESSMENT: Deep research requested.
→ Be thorough. Use up to 8 tools. Cover multiple perspectives."""

    else:
        return """COMPLEXITY ASSESSMENT: Medium depth requested.
→ Use 3-5 tools. Balance thoroughness with efficiency."""


CRITIQUE_PROMPT = """You are evaluating a research report. Be practical and efficient.

Evaluate the report on these criteria:

1. **Answers the question** — Does it actually answer what was asked?
2. **Sufficient depth** — Is the depth appropriate for the complexity of the topic?
3. **Sources cited** — Are sources mentioned?
4. **No hallucination** — Is all information backed by sources?

## IMPORTANT APPROVAL RULES:
- For SIMPLE topics (definitions, basic facts): Approve if the answer is correct and complete, even if short.
- For MEDIUM topics: Approve if key aspects are covered with 2+ sources.
- For DEEP topics: Approve if comprehensive with 4+ sources and multiple perspectives.

## Response format:
If the report is good enough → respond ONLY with: REPORT_APPROVED
If the report needs improvement → respond with specific gaps (max 2-3 bullet points)

Do NOT ask for more research on simple topics that are already well-answered.
Do NOT reject reports just because they are short — short answers are correct for simple topics.
"""