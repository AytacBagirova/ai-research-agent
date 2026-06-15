import httpx
import google.generativeai as genai
from backend.config import settings
from backend.tools.base_tool import BaseTool, ToolResult


genai.configure(api_key=settings.GEMINI_API_KEY)


class ReadPDFTool(BaseTool):
    name = "read_pdf"

    description = (
        "Read and extract text content from a PDF file using AI. "
        "Can read PDFs from a URL or from a local file path. "
        "Use this when you find a PDF link or when the user uploads a PDF document."
    )

    def __init__(self):
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    async def run(self, source: str) -> ToolResult:
        try:
            if source.startswith("https://"):
                pdf_bytes = await self._download_pdf(source)
            else:
                pdf_bytes = await self._read_local_pdf(source)

            if pdf_bytes is None:
                return ToolResult(
                    success=False,
                    content="",
                    error="PDF yüklənə bilmədi",
                    source_type="pdf"
                )

            text = await self._extract_with_gemini(pdf_bytes)

            if not text:
                return ToolResult(
                    success=False,
                    content="",
                    error="PDF-dən mətn çıxarıla bilmədi",
                    source_type="pdf"
                )

            return ToolResult(
                success=True,
                content=text,
                source_url=source if source.startswith("https://") else None,
                source_type="pdf"
            )

        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=f"PDF oxunmadı: {str(e)}",
                source_type="pdf"
            )

    async def _download_pdf(self, url: str) -> bytes | None:
        try:
            async with httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.content
        except Exception:
            return None

    async def _read_local_pdf(self, path: str) -> bytes | None:
        try:
            with open(path, "rb") as f:
                return f.read()
        except Exception:
            return None

    async def _extract_with_gemini(self, pdf_bytes: bytes) -> str:
        pdf_part = {
            "mime_type": "application/pdf",
            "data": pdf_bytes
        }

        response = self.model.generate_content([
            pdf_part,
            "Extract and summarize the main content of this PDF. "
            "Include key findings, arguments, and conclusions. "
            "Keep it concise but comprehensive. "
            "Maximum 1000 words."
        ])

        return response.text

    def get_input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "PDF file URL (https only) or local file path"
                }
            },
            "required": ["source"]
        }