from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, DateTime, ForeignKey, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from backend.db.database import Base


class ResearchSession(Base):
    __tablename__ = "research_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    topic: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    final_report: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    token_count: Mapped[int] = mapped_column(Integer, default=0)
    sources_count: Mapped[int] = mapped_column(Integer, default=0)
    tiktoken_count: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost: Mapped[float] = mapped_column(Float, default=0.0)

    # Depth ve language saxla — stream endpoint-de lazim olacaq
    depth: Mapped[str] = mapped_column(String(20), default="medium")
    language: Mapped[str] = mapped_column(String(50), default="en")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    steps: Mapped[List["ResearchStep"]] = relationship(
        "ResearchStep", back_populates="session", cascade="all, delete-orphan"
    )
    sources: Mapped[List["ResearchSource"]] = relationship(
        "ResearchSource", back_populates="session", cascade="all, delete-orphan"
    )


class ResearchStep(Base):
    __tablename__ = "research_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("research_sessions.id"), nullable=False
    )
    step_type: Mapped[str] = mapped_column(String(50), nullable=False)
    tool_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped["ResearchSession"] = relationship(
        "ResearchSession", back_populates="steps"
    )


class ResearchSource(Base):
    __tablename__ = "research_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("research_sessions.id"), nullable=False
    )
    url: Mapped[str] = mapped_column(String(2000), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    snippet: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    credibility_score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(1536), nullable=True)

    session: Mapped["ResearchSession"] = relationship(
        "ResearchSession", back_populates="sources"
    )