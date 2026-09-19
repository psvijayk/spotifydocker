from pydantic import BaseModel, Field
from typing import Any


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class Source(BaseModel):
    source: str
    chunk_id: str
    score: float | None = None
    type: str


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]
    graph_context: list[dict[str, Any]]
    guardrail_flags: list[str] = []


class IngestResponse(BaseModel):
    filename: str
    chunks: int
    graph_items: int
    status: str
