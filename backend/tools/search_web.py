from tavily import TavilyClient
from backend.config import settings
from backend.tools.base_tool import BaseTool, ToolResult


class SearchWebTool(BaseTool):
    # Alətin adı — agent_loop-da Claude bu adı görəcək
    name = "search_web"

    # Alətin təsviri — Claude bunu oxuyur və
    # "bu aləti nə vaxt işlədim?" qərarını verir
    description = (
        "Search the web for current information about a topic. "
        "Use this tool to find recent articles, news, and general information. "
        "Returns a list of relevant results with titles, URLs, and content snippets."
    )

    def __init__(self):
        # Tavily client-i yaradırıq — API açarını .env-dən alır
        self.client = TavilyClient(api_key=settings.TAVILY_API_KEY)

    async def run(self, query: str, max_results: int = 5) -> ToolResult:
        """
        Tavily ilə internetdə axtarış edir.
        query      → axtarış sorğusu
        max_results → neçə nəticə qaytarsın (default: 5)
        """
        try:
            # Tavily API-yə sorğu göndər
            response = self.client.search(
                query=query,
                max_results=max_results,
                include_answer=True,    # qısa xülasə cavab da qaytar
                include_raw_content=False  # tam HTML lazım deyil
            )

            # Nəticələri oxunaqlı formata çevir
            results = []
            for item in response.get("results", []):
                results.append(
                    f"Title: {item.get('title', 'No title')}\n"
                    f"URL: {item.get('url', '')}\n"
                    f"Content: {item.get('content', '')}\n"
                    f"---"
                )

            # Bütün nəticələri bir mətn kimi birləşdir
            content = "\n".join(results)

            # Tavily-nin öz xülasə cavabı varsa əlavə et
            if response.get("answer"):
                content = f"Summary: {response['answer']}\n\n{content}"

            return ToolResult(
                success=True,
                content=content,
                source_type="web"
            )

        except Exception as e:
            # Xəta baş verdisə — uğursuz nəticə qaytar
            return ToolResult(
                success=False,
                content="",
                error=f"Web search failed: {str(e)}",
                source_type="web"
            )

    def get_input_schema(self) -> dict:
        """
        Claude-a deyirik ki, bu aləti çağıranda
        hansı parametrləri göndərməlidir.
        """
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to look up on the web"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default: 5)",
                    "default": 5
                }
            },
            "required": ["query"]
        }