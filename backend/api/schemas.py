from datetime import datetime
from pydantic import BaseModel, Field


# ==================================================
# REQUEST SCHEMALAR — frontend-dən gələn məlumatlar
# ==================================================

class ResearchRequest(BaseModel):
    topic: str
    additional_instructions: str = ""
    depth: str = "medium"
    language: str = "en"


# ==================================================
# RESPONSE SCHEMALAR — backend-dən gedən məlumatlar
# ==================================================

class SessionResponse(BaseModel):
    session_id: int = Field(alias="id")
    topic: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


class StepResponse(BaseModel):
    id: int
    step_type: str
    tool_name: str | None
    content: str
    tokens_used: int
    duration_ms: int
    created_at: datetime

    class Config:
        from_attributes = True


class SourceResponse(BaseModel):
    id: int
    url: str
    title: str | None
    source_type: str
    snippet: str | None
    credibility_score: float

    class Config:
        from_attributes = True


class ReportResponse(BaseModel):
    session_id: int
    topic: str
    status: str
    final_report: str | None
    token_count: int
    sources_count: int
    created_at: datetime
    completed_at: datetime | None
    steps: list[StepResponse] = []
    sources: list[SourceResponse] = []

    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    sessions: list[SessionResponse]
    total: int


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None