from typing import List

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=3)
    document_path: str = Field(..., min_length=1)
    domain: str = Field(default="telecom_security", min_length=1)
    max_results: int = Field(default=3, ge=1, le=10)


class SourceDocument(BaseModel):
    content: str
    metadata: dict


class QueryResponse(BaseModel):
    answer: str
    domain: str
    attempts: int
    used_reflection: bool
    sources: List[SourceDocument]
