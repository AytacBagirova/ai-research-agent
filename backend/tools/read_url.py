import httpx
from bs4 import BeautifulSoup
from backend.tools.base_tool import BaseTool, ToolResult


class ReadURLTool(BaseTool):
    # Alətin adı
    name = "read_url"

    # Alətin təsviri — Claude nə vaxt işlədəcəyini bilir
    description = (
        "Read and extract the main text content from a webpage URL. "
        "Use this after search_web to get the full content of a specific page. "
        "Returns the cleaned text content of the webpage."
    )

    async def run(self, url: str) -> ToolResult:
        """
        URL-dən məzmun oxuyur.
        url → oxunacaq səhifənin ünvanı
        """
        try:
            # httpx ilə URL-ə sorğu göndər
            # async with — sorğu bitəndə bağlantı avtomatik bağlanır
            async with httpx.AsyncClient(
                timeout=15.0,           # 15 saniyə gözlə, cavab gəlməsə keç
                follow_redirects=True   # redirect varsa izlə
            ) as client:
                response = await client.get(url)
                response.raise_for_status()  # xəta kodu gələrsə exception at

            # HTML-i parse et — BeautifulSoup ilə
            soup = BeautifulSoup(response.text, "html.parser")

            # Lazımsız elementləri sil
            # script, style, nav — məzmun deyil, lazım deyil
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()

            # Təmiz mətni götür
            text = soup.get_text(separator="\n")

            # Boş sətirləri təmizlə
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            clean_text = "\n".join(lines)

            # Çox uzun olmasın — ilk 3000 simvolu götür
            # Token limitini aşmamaq üçün
            if len(clean_text) > 3000:
                clean_text = clean_text[:3000] + "\n...[məzmun kəsildi]"

            return ToolResult(
                success=True,
                content=clean_text,
                source_url=url,
                source_type="web"
            )

        except httpx.TimeoutException:
            return ToolResult(
                success=False,
                content="",
                error=f"Timeout: {url} cavab vermədi",
                source_url=url,
                source_type="web"
            )

        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=f"URL oxunmadı: {str(e)}",
                source_url=url,
                source_type="web"
            )

    def get_input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL of the webpage to read"
                }
            },
            "required": ["url"]
        }