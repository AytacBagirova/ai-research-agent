import httpx
import xml.etree.ElementTree as ET
from backend.tools.base_tool import BaseTool, ToolResult


class ReadArxivTool(BaseTool):
    name = "read_arxiv"

    description = (
        "Search and read scientific papers from arXiv.org. "
        "Use this tool when the topic requires academic or scientific sources. "
        "Returns paper titles, authors, abstracts, and links."
    )

    ARXIV_API_URL = "https://export.arxiv.org/api/query"

    async def run(self, query: str, max_results: int = 3) -> ToolResult:
        try:
            params = {
                "search_query": f"all:{query}",
                "start": 0,
                "max_results": max_results,
                "sortBy": "relevance",
                "sortOrder": "descending"
            }

            async with httpx.AsyncClient(
                timeout=15.0,
                follow_redirects=True  # redirect-i izlə
            ) as client:
                response = await client.get(self.ARXIV_API_URL, params=params)
                response.raise_for_status()

            root = ET.fromstring(response.text)

            ns = {
                "atom": "http://www.w3.org/2005/Atom",
                "arxiv": "http://arxiv.org/schemas/atom"
            }

            results = []

            for entry in root.findall("atom:entry", ns):
                title = entry.find("atom:title", ns)
                title = title.text.strip() if title is not None else "No title"

                authors = entry.findall("atom:author", ns)
                author_names = []
                for author in authors[:3]:
                    name = author.find("atom:name", ns)
                    if name is not None:
                        author_names.append(name.text)
                authors_str = ", ".join(author_names)
                if len(entry.findall("atom:author", ns)) > 3:
                    authors_str += " et al."

                summary = entry.find("atom:summary", ns)
                summary = summary.text.strip() if summary is not None else ""
                if len(summary) > 500:
                    summary = summary[:500] + "..."

                link = entry.find("atom:id", ns)
                link = link.text.strip() if link is not None else ""

                published = entry.find("atom:published", ns)
                published = published.text[:10] if published is not None else ""

                results.append(
                    f"Title: {title}\n"
                    f"Authors: {authors_str}\n"
                    f"Published: {published}\n"
                    f"URL: {link}\n"
                    f"Abstract: {summary}\n"
                    f"---"
                )

            if not results:
                return ToolResult(
                    success=False,
                    content="",
                    error=f"arXiv-də '{query}' üçün nəticə tapılmadı",
                    source_type="arxiv"
                )

            content = "\n".join(results)

            return ToolResult(
                success=True,
                content=content,
                source_type="arxiv"
            )

        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=f"arXiv axtarışı uğursuz oldu: {str(e)}",
                source_type="arxiv"
            )

    def get_input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The scientific topic to search for on arXiv"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of papers to return (default: 3)",
                    "default": 3
                }
            },
            "required": ["query"]
        }