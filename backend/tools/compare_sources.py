import httpx
from backend.tools.base_tool import BaseTool, ToolResult


class CompareSourcesTool(BaseTool):
    """
    İki URL-in məzmununu oxuyub müqayisə edir.
    Agent fərqli mənbələri bir-biri ilə müqayisə etmək istədikdə işlədir.
    """

    name = "compare_sources"

    description = (
        "Compare the content of two different URLs on the same topic. "
        "Use this when you want to find agreements and disagreements between sources, "
        "or when you need to cross-reference information from multiple sources. "
        "Returns a structured comparison of both sources."
    )

    async def run(self, url1: str, url2: str, topic: str = "") -> ToolResult:
        """
        İki URL oxuyur və müqayisə edir.
        url1, url2 → müqayisə ediləcək URL-lər
        topic      → nə barədə müqayisə edilsin (isteğe bağlı)
        """
        try:
            content1 = await self._fetch_url(url1)
            content2 = await self._fetch_url(url2)

            if not content1 and not content2:
                return ToolResult(
                    success=False,
                    content="",
                    error="Hər iki URL oxunmadı."
                )

            comparison = self._build_comparison(url1, content1, url2, content2, topic)

            return ToolResult(
                success=True,
                content=comparison,
                source_type="web"
            )

        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=f"Müqayisə uğursuz oldu: {str(e)}"
            )

    async def _fetch_url(self, url: str) -> str:
        """URL məzmununu oxuyur."""
        try:
            from bs4 import BeautifulSoup
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()

            text = soup.get_text(separator="\n")
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            clean_text = "\n".join(lines)

            # Hər mənbədən 1500 simvol götür
            return clean_text[:1500] if len(clean_text) > 1500 else clean_text

        except Exception:
            return ""

    def _build_comparison(
        self,
        url1: str, content1: str,
        url2: str, content2: str,
        topic: str
    ) -> str:
        """Müqayisə mətnini qurur."""

        result = []

        if topic:
            result.append(f"## Comparison: {topic}\n")

        result.append(f"### Source 1: {url1}")
        if content1:
            result.append(content1[:800])
        else:
            result.append("(Could not read this source)")

        result.append(f"\n### Source 2: {url2}")
        if content2:
            result.append(content2[:800])
        else:
            result.append("(Could not read this source)")

        result.append("\n### Note for Agent")
        result.append(
            "Compare the above two sources. "
            "Identify: (1) What they agree on, "
            "(2) Where they differ, "
            "(3) Which source seems more authoritative."
        )

        return "\n".join(result)

    def get_input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "url1": {
                    "type": "string",
                    "description": "First URL to compare"
                },
                "url2": {
                    "type": "string",
                    "description": "Second URL to compare"
                },
                "topic": {
                    "type": "string",
                    "description": "The specific aspect to compare (optional)"
                }
            },
            "required": ["url1", "url2"]
        }