from abc import ABC, abstractmethod
from dataclasses import dataclass


# --------------------------------------------------
# TOOL RESULT — hər alətin qaytardığı nəticə
# --------------------------------------------------
# Hər alət işləyəndə bu strukturda nəticə qaytarır
# Agent bu nəticəni oxuyur və növbəti addımı qurur
@dataclass
class ToolResult:
    # Əməliyyat uğurlu oldumu?
    success: bool

    # Alətin qaytardığı məzmun
    # Məsələn: "Quantum computing haqqında 3 məqalə tapıldı..."
    content: str

    # Xəta baş verdisə — xəta mesajı
    # Uğurlu olarsa — None qalır
    error: str | None = None

    # Mənbənin URL-i (varsa)
    # search_web, read_url, read_arxiv üçün doldurulur
    source_url: str | None = None

    # Mənbənin növü
    # "web", "arxiv", "pdf", "wikipedia"
    source_type: str | None = None


# --------------------------------------------------
# BASE TOOL — bütün alətlərin ana class-ı
# --------------------------------------------------
# ABC = Abstract Base Class
# abstractmethod = alt class-lar bu metodu mütləq yazmalıdır
class BaseTool(ABC):

    # Alətin adı — agent bu adı işlədəcək
    # Məsələn: "search_web", "read_url"
    name: str

    # Alətin təsviri — Claude bunu oxuyur və
    # "bu aləti nə vaxt işlədim?" qərarını verir
    description: str

    @abstractmethod
    async def run(self, **kwargs) -> ToolResult:
        """
        Hər alətin əsas funksiyası.
        Alt class-lar bu metodu mütləq implement etməlidir.
        async — asinxron işləyir, server bloklanmır.
        """
        pass

    def to_claude_tool(self) -> dict:
        """
        Aləti Claude API-nin başa düşdüyü formata çevirir.
        Agent loop-da Claude-a göndəriləcək.
        """
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.get_input_schema()
        }

    @abstractmethod
    def get_input_schema(self) -> dict:
        """
        Alətin qəbul etdiyi parametrləri təsvir edir.
        Claude bunu oxuyur və düzgün parametrlərlə çağırır.
        """
        pass