import httpx
from backend.tools.base_tool import BaseTool, ToolResult


class ReadWikipediaTool(BaseTool):
    # Alətin adı
    name = "read_wikipedia"

    # Alətin təsviri
    description = (
        "Read a Wikipedia article about a topic. "
        "Use this tool to get a quick overview and background information. "
        "Best for general concepts, historical facts, and definitions."
    )

    # Wikipedia API ünvanı — pulsuz, açar lazım deyil
    WIKI_API_URL = "https://en.wikipedia.org/api/rest_v1/page/summary"

    async def run(self, topic: str) -> ToolResult:
        """
        Wikipedia-dan məqalə oxuyur.
        topic → axtarılacaq mövzu
        """
        try:
            # Mövzunu URL formatına çevir
            # "quantum computing" → "quantum_computing"
            formatted_topic = topic.strip().replace(" ", "_")

            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.WIKI_API_URL}/{formatted_topic}",
                    headers={"User-Agent": "ResearchAgent/1.0"}
                )

                # 404 — məqalə tapılmadı
                if response.status_code == 404:
                    return ToolResult(
                        success=False,
                        content="",
                        error=f"Wikipedia-da '{topic}' tapılmadı",
                        source_type="wikipedia"
                    )

                response.raise_for_status()

            data = response.json()

            # Məqalənin başlığı
            title = data.get("title", topic)

            # Məqalənin xülasəsi
            summary = data.get("extract", "")

            if not summary:
                return ToolResult(
                    success=False,
                    content="",
                    error=f"Wikipedia məqaləsi boşdur: {topic}",
                    source_type="wikipedia"
                )

            # Wikipedia səhifəsinin URL-i
            page_url = data.get("content_urls", {}).get("desktop", {}).get("page", "")

            content = (
                f"Title: {title}\n"
                f"URL: {page_url}\n\n"
                f"{summary}"
            )

            return ToolResult(
                success=True,
                content=content,
                source_url=page_url,
                source_type="wikipedia"
            )

        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=f"Wikipedia oxunmadı: {str(e)}",
                source_type="wikipedia"
            )

    def get_input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The topic to look up on Wikipedia"
                }
            },
            "required": ["topic"]
        }