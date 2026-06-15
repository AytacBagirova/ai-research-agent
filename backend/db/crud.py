from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.db.models import ResearchSession, ResearchStep, ResearchSource


async def create_session(
    db: AsyncSession,
    topic: str,
    model: str,
    depth: str = "medium",
    language: str = "en"
) -> ResearchSession:
    session = ResearchSession(
        topic=topic,
        model=model,
        status="pending",
        depth=depth,
        language=language
    )
    db.add(session)
    await db.flush()
    return session


async def get_session(db: AsyncSession, session_id: int) -> ResearchSession | None:
    result = await db.execute(
        select(ResearchSession).where(ResearchSession.id == session_id)
    )
    return result.scalar_one_or_none()


async def get_all_sessions(db: AsyncSession) -> list[ResearchSession]:
    result = await db.execute(
        select(ResearchSession).order_by(ResearchSession.created_at.desc())
    )
    return list(result.scalars().all())


async def update_session_status(
    db: AsyncSession, session_id: int, status: str
) -> None:
    session = await get_session(db, session_id)
    if session:
        session.status = status
        if status in ("done", "failed"):
            session.completed_at = datetime.utcnow()


async def update_session_report(
    db: AsyncSession,
    session_id: int,
    report: str,
    token_count: int,
    sources_count: int,
    tiktoken_count: int = 0,
    estimated_cost: float = 0.0
) -> None:
    session = await get_session(db, session_id)
    if session:
        session.final_report = report
        session.token_count = token_count
        session.sources_count = sources_count
        session.tiktoken_count = tiktoken_count
        session.estimated_cost = estimated_cost
        session.status = "done"
        session.completed_at = datetime.utcnow()


async def delete_session(db: AsyncSession, session_id: int) -> bool:
    session = await get_session(db, session_id)
    if session:
        await db.delete(session)
        return True
    return False


async def create_step(
    db: AsyncSession,
    session_id: int,
    step_type: str,
    content: str,
    tool_name: str | None = None,
    tokens_used: int = 0,
    duration_ms: int = 0
) -> ResearchStep:
    step = ResearchStep(
        session_id=session_id,
        step_type=step_type,
        content=content,
        tool_name=tool_name,
        tokens_used=tokens_used,
        duration_ms=duration_ms
    )
    db.add(step)
    await db.flush()
    return step


async def get_steps_by_session(
    db: AsyncSession, session_id: int
) -> list[ResearchStep]:
    result = await db.execute(
        select(ResearchStep)
        .where(ResearchStep.session_id == session_id)
        .order_by(ResearchStep.created_at.asc())
    )
    return list(result.scalars().all())


async def create_source(
    db: AsyncSession,
    session_id: int,
    url: str,
    source_type: str,
    title: str | None = None,
    snippet: str | None = None,
    credibility_score: float = 0.0,
    embedding: list[float] | None = None
) -> ResearchSource:
    source = ResearchSource(
        session_id=session_id,
        url=url,
        source_type=source_type,
        title=title,
        snippet=snippet,
        credibility_score=credibility_score,
        embedding=embedding
    )
    db.add(source)
    await db.flush()
    return source


async def get_sources_by_session(
    db: AsyncSession, session_id: int
) -> list[ResearchSource]:
    result = await db.execute(
        select(ResearchSource)
        .where(ResearchSource.session_id == session_id)
        .order_by(ResearchSource.credibility_score.desc())
    )
    return list(result.scalars().all())


async def find_similar_sources(
    db: AsyncSession,
    session_id: int,
    query_embedding: list[float],
    limit: int = 5
) -> list[ResearchSource]:
    result = await db.execute(
        select(ResearchSource)
        .where(ResearchSource.session_id == session_id)
        .where(ResearchSource.embedding.isnot(None))
        .order_by(ResearchSource.embedding.cosine_distance(query_embedding))
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_steps_after(
    db: AsyncSession,
    session_id: int,
    last_step_id: int
) -> list[ResearchStep]:
    """
    Son göndərilmiş addımdan sonrakı yeni addımları qaytarır.
    Polling stream üçün — hər saniyə yeni addımları yoxla.
    """
    result = await db.execute(
        select(ResearchStep)
        .where(ResearchStep.session_id == session_id)
        .where(ResearchStep.id > last_step_id)
        .order_by(ResearchStep.created_at.asc())
    )
    return list(result.scalars().all())