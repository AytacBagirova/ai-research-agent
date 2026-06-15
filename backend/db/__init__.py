from backend.db.database import Base, engine
from backend.db.models import ResearchSession, ResearchStep, ResearchSource
from backend.agent.embeddings import ensure_collection


async def init_db():
    """
    Server başlayanda:
    1. PostgreSQL cədvəllərini yaradır
    2. Qdrant collection-u yaradır
    """
    async with engine.begin() as conn:
        # pgvector extension aktivləşdir
        import sqlalchemy
        await conn.execute(
            sqlalchemy.text("CREATE EXTENSION IF NOT EXISTS vector")
        )
        # Cədvəlləri yarat
        await conn.run_sync(Base.metadata.create_all)

    # Qdrant collection yarat
    ensure_collection()