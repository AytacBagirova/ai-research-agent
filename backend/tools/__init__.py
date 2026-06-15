from backend.tools.search_web import SearchWebTool
from backend.tools.read_url import ReadURLTool
from backend.tools.read_arxiv import ReadArxivTool
from backend.tools.read_pdf import ReadPDFTool
from backend.tools.read_wikipedia import ReadWikipediaTool
from backend.tools.compare_sources import CompareSourcesTool

# Bütün alətlər — Claude-a göndəriləcək
ALL_TOOLS = [
    SearchWebTool(),
    ReadURLTool(),
    ReadArxivTool(),
    ReadPDFTool(),
    ReadWikipediaTool(),
    CompareSourcesTool(),  # yeni əlavə
]

# Alət adına görə sürətli axtarış
TOOLS_MAP = {tool.name: tool for tool in ALL_TOOLS}