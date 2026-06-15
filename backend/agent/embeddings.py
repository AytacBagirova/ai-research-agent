"""
OpenAI Embeddings + Qdrant Vector Database modulu.

Axın:
1. Mənbənin mətni → OpenAI API → 1536 ölçülü vektor
2. Vektor → Qdrant-a yaz (collection: research_sources)
3. Axtarış zamanı → Qdrant-dan oxşarları tap
"""

from openai import AsyncOpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)
from backend.config import settings

# OpenAI async client
_openai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

# Qdrant sync client (async lazım deyil, sürətlidir)
_qdrant = QdrantClient(url=settings.QDRANT_URL)

# Embedding modeli və ölçüsü
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536
COLLECTION_NAME = settings.QDRANT_COLLECTION


def ensure_collection() -> None:
    """
    Qdrant-da 'research_sources' collection-u yoxdursa yaradır.
    Server başlayanda bir dəfə çağırılır.
    """
    existing = [c.name for c in _qdrant.get_collections().collections]
    if COLLECTION_NAME not in existing:
        _qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=EMBEDDING_DIM,
                distance=Distance.COSINE  # cosine oxşarlıq
            )
        )
        print(f"✅ Qdrant collection yaradıldı: {COLLECTION_NAME}")
    else:
        print(f"✅ Qdrant collection mövcuddur: {COLLECTION_NAME}")


async def embed_text(text: str) -> list[float] | None:
    """
    Mətni OpenAI ilə vektora çevirir.
    text → embed ediləcək mətn
    Qaytarır: 1536 ölçülü float siyahısı, xəta olarsa None
    """
    if not text or not text.strip():
        return None

    try:
        # Mətni 8000 simvola qıs
        truncated = text[:8000]

        response = await _openai.embeddings.create(
            model=EMBEDDING_MODEL,
            input=truncated,
            dimensions=EMBEDDING_DIM
        )

        return response.data[0].embedding

    except Exception as e:
        print(f"❌ Embedding xətası: {e}")
        return None


async def embed_and_store(
    source_id: int,
    session_id: int,
    url: str,
    title: str | None,
    snippet: str | None,
    source_type: str,
    credibility_score: float
) -> bool:
    """
    Mənbəni embed edib Qdrant-a yazır.

    source_id       → PostgreSQL-dəki ResearchSource.id
    session_id      → hansı sessiyaya aid
    url             → mənbənin URL-i
    title           → başlıq
    snippet         → qısa məzmun
    source_type     → web/arxiv/pdf/wikipedia
    credibility_score → 0.0-1.0

    Qaytarır: True (uğurlu), False (xəta)
    """
    # Embed ediləcək mətni qur
    parts = []
    if title:
        parts.append(f"Title: {title}")
    if snippet:
        parts.append(f"Content: {snippet}")
    parts.append(f"URL: {url}")
    text = "\n".join(parts)

    # Vektora çevir
    vector = await embed_text(text)
    if not vector:
        return False

    try:
        # Qdrant-a yaz
        _qdrant.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                PointStruct(
                    id=source_id,          # PostgreSQL ID-si ilə eyniləşdiririk
                    vector=vector,
                    payload={              # Əlavə məlumatlar — filter üçün
                        "session_id": session_id,
                        "url": url,
                        "title": title or "",
                        "snippet": snippet or "",
                        "source_type": source_type,
                        "credibility_score": credibility_score,
                    }
                )
            ]
        )
        return True

    except Exception as e:
        print(f"❌ Qdrant yazma xətası: {e}")
        return False


async def search_similar(
    query: str,
    session_id: int | None = None,
    limit: int = 5
) -> list[dict]:
    """
    Sorğuya oxşar mənbələri Qdrant-dan tapır.

    query      → axtarış mətni
    session_id → yalnız bu sessiyada axtar (None = hamısında)
    limit      → neçə nəticə qaytar

    Qaytarır: oxşar mənbələrin siyahısı (payload + score)
    """
    # Sorğunu vektora çevir
    query_vector = await embed_text(query)
    if not query_vector:
        return []

    try:
        # Filter — session_id varsa yalnız ona aid nəticələr
        search_filter = None
        if session_id is not None:
            search_filter = Filter(
                must=[
                    FieldCondition(
                        key="session_id",
                        match=MatchValue(value=session_id)
                    )
                ]
            )

        results = _qdrant.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            query_filter=search_filter,
            limit=limit,
            with_payload=True
        )

        # Nəticələri formatla
        return [
            {
                "score": round(hit.score, 4),
                "url": hit.payload.get("url", ""),
                "title": hit.payload.get("title", ""),
                "snippet": hit.payload.get("snippet", ""),
                "source_type": hit.payload.get("source_type", ""),
                "credibility_score": hit.payload.get("credibility_score", 0.0),
                "session_id": hit.payload.get("session_id"),
            }
            for hit in results
        ]

    except Exception as e:
        print(f"❌ Qdrant axtarış xətası: {e}")
        return []


def get_collection_info() -> dict:
    """
    Qdrant collection-un statistikasını qaytarır.
    Debug üçün istifadə olunur.
    """
    try:
        info = _qdrant.get_collection(COLLECTION_NAME)
        return {
            "name": COLLECTION_NAME,
            "vectors_count": info.vectors_count,
            "points_count": info.points_count,
            "status": str(info.status)
        }
    except Exception as e:
        return {"error": str(e)}