from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class DomainMetric(BaseModel):
    name: str = Field(..., min_length=1)
    value: str = Field(..., min_length=1)
    unit: str = Field(default="", min_length=0)


class DomainInsight(BaseModel):
    title: str = Field(..., min_length=1)
    severity: str = Field(default="info", min_length=1)
    detail: str = Field(..., min_length=1)


class DomainRecommendation(BaseModel):
    priority: int = Field(..., ge=1, le=10)
    action: str = Field(..., min_length=1)


class DomainSourceRef(BaseModel):
    source: str = Field(..., min_length=1)
    chunk_index: Optional[int] = None
    file_type: Optional[str] = None


class DomainReport(BaseModel):
    domain: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)
    metrics: List[DomainMetric] = Field(default_factory=list)
    insights: List[DomainInsight] = Field(default_factory=list)
    recommendations: List[DomainRecommendation] = Field(default_factory=list)
    source_refs: List[DomainSourceRef] = Field(default_factory=list)


class ReportEvaluation(BaseModel):
    grounded: bool
    has_sources: bool
    has_recommendations: bool
    issues: List[str] = Field(default_factory=list)


class ExecutionMetadata(BaseModel):
    workflow_backend: str
    agent_type: str
    provider_mode: str
    provider_model: str = ""
    used_fallback: bool = False


class DashboardMetric(BaseModel):
    label: str
    value: str
    unit: str = ""


class DashboardHighlight(BaseModel):
    title: str
    severity: str
    detail: str


class DashboardAction(BaseModel):
    priority: int
    action: str


class DashboardStatus(BaseModel):
    level: str
    issues: List[str] = Field(default_factory=list)


class DashboardResponse(BaseModel):
    domain: str
    title: str
    summary: str
    status: DashboardStatus
    metrics: List[DashboardMetric] = Field(default_factory=list)
    highlights: List[DashboardHighlight] = Field(default_factory=list)
    actions: List[DashboardAction] = Field(default_factory=list)
    source_count: int
    execution: ExecutionMetadata
    evaluation: ReportEvaluation


class QueryRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "query": "What action is recommended for the SS7 issue?",
                    "document_path": "test_data/telecom_incident.txt",
                    "domain": "telecom_security",
                    "max_results": 2,
                },
                {
                    "query": "What governance control is required before export?",
                    "document_path": "test_data/telecom_incident.txt",
                    "domain": "telecom_security",
                    "max_results": 3,
                },
                {
                    "query": "What refund policy is mentioned?",
                    "document_path": "test_data/ecommerce-full-100products.pdf",
                    "domain": "telecom_security",
                    "max_results": 3,
                },
            ]
        }
    )

    query: str = Field(
        ...,
        min_length=3,
        examples=["What action is recommended for the SS7 issue?"],
    )
    document_path: str = Field(
        ...,
        min_length=1,
        examples=["test_data/telecom_incident.txt"],
    )
    domain: str = Field(
        default="telecom_security",
        min_length=1,
        examples=["telecom_security"],
    )
    max_results: int = Field(default=3, ge=1, le=10, examples=[2])


class SourceDocument(BaseModel):
    content: str
    metadata: dict


class QueryResponse(BaseModel):
    answer: str
    domain: str
    attempts: int
    used_reflection: bool
    report: DomainReport
    evaluation: ReportEvaluation
    execution: ExecutionMetadata
    sources: List[SourceDocument]


class ErrorResponse(BaseModel):
    detail: str
