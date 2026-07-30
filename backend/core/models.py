from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


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


class DashboardMatchedSource(BaseModel):
    source: str
    source_id: str = ""
    domain: str = ""
    origin: str = ""
    evidence_count: int = 0
    file_type: str = ""
    preview: str = ""


class DashboardEvidenceCard(BaseModel):
    title: str
    detail: str
    source: str
    source_id: str = ""
    evidence_count: int = 0
    severity: str = "info"


class DashboardResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "domain": "telecom_security",
                    "title": "Telecom Security Dashboard Report",
                    "summary": "Critical SS7 exposure remains active on the roaming edge and needs immediate signaling firewall enforcement.",
                    "status": {
                        "level": "warning",
                        "issues": [
                            "Grounding confidence reduced because mitigation ownership is implied rather than explicitly assigned."
                        ],
                    },
                    "metrics": [
                        {"label": "Incident Severity", "value": "critical", "unit": ""},
                        {"label": "Affected Nodes", "value": "3", "unit": "sites"},
                    ],
                    "highlights": [
                        {
                            "title": "SS7 filtering gap",
                            "severity": "high",
                            "detail": "Inbound signaling traffic is not consistently screened on interconnect routes.",
                        }
                    ],
                    "actions": [
                        {"priority": 1, "action": "Enable interconnect screening rules and validate with roaming test traffic."},
                        {"priority": 2, "action": "Assign telecom security operations as the mitigation owner for weekly review."},
                    ],
                    "matched_sources": [
                        {
                            "source": "test_data/telecom_incident.txt",
                            "source_id": "sample:telecom_security:telecom_incident.txt",
                            "domain": "telecom_security",
                            "origin": "sample",
                            "evidence_count": 2,
                            "file_type": "text",
                            "preview": "SS7 routing instability and authentication disruption were observed on the roaming edge.",
                        }
                    ],
                    "evidence_cards": [
                        {
                            "title": "SS7 routing evidence",
                            "detail": "The retrieved context points to SS7 routing instability impacting customer authentication flows.",
                            "source": "test_data/telecom_incident.txt",
                            "source_id": "sample:telecom_security:telecom_incident.txt",
                            "evidence_count": 2,
                            "severity": "high",
                        }
                    ],
                    "source_count": 2,
                    "execution": {
                        "workflow_backend": "query_pipeline",
                        "agent_type": "telecom_security",
                        "provider_mode": "fallback",
                        "provider_model": "",
                        "used_fallback": True,
                    },
                    "evaluation": {
                        "grounded": False,
                        "has_sources": True,
                        "has_recommendations": True,
                        "issues": [
                            "Grounding confidence reduced because mitigation ownership is implied rather than explicitly assigned."
                        ],
                    },
                },
                {
                    "domain": "financial_risk",
                    "title": "Financial Risk Dashboard Report",
                    "summary": "The document emphasizes approval control, delegated authority, and audit traceability before fund release.",
                    "status": {"level": "success", "issues": []},
                    "metrics": [
                        {"label": "Control Focus", "value": "pre-approval", "unit": ""},
                        {"label": "Audit Readiness", "value": "high", "unit": ""},
                    ],
                    "highlights": [
                        {
                            "title": "Delegated authority enforced",
                            "severity": "medium",
                            "detail": "Approvals must align with the designated financial authority matrix.",
                        }
                    ],
                    "actions": [
                        {"priority": 1, "action": "Validate sanctioning authority before procurement or release activity."},
                        {"priority": 2, "action": "Retain approval trail and supporting documentation for audit review."},
                    ],
                    "source_count": 3,
                    "execution": {
                        "workflow_backend": "query_pipeline",
                        "agent_type": "financial_risk",
                        "provider_mode": "llm",
                        "provider_model": "gpt-4.1-mini",
                        "used_fallback": False,
                    },
                    "evaluation": {
                        "grounded": True,
                        "has_sources": True,
                        "has_recommendations": True,
                        "issues": [],
                    },
                },
                {
                    "domain": "medical_qa",
                    "title": "Medical Qa Dashboard Report",
                    "summary": "The retrieved context supports triage advice but still indicates escalation for persistent chest pain symptoms.",
                    "status": {"level": "info", "issues": ["Fallback mode used; clinical review still required."]},
                    "metrics": [
                        {"label": "Symptom Risk", "value": "moderate", "unit": ""},
                        {"label": "Escalation Window", "value": "24", "unit": "hours"},
                    ],
                    "highlights": [
                        {
                            "title": "Escalation recommended",
                            "severity": "high",
                            "detail": "Persistent chest discomfort warrants physician follow-up even when initial advice is conservative.",
                        }
                    ],
                    "actions": [
                        {"priority": 1, "action": "Escalate to clinician review if symptoms persist or intensify."},
                        {"priority": 2, "action": "Present response with a clear disclaimer that it is not a final diagnosis."},
                    ],
                    "source_count": 2,
                    "execution": {
                        "workflow_backend": "query_pipeline",
                        "agent_type": "medical_qa",
                        "provider_mode": "fallback",
                        "provider_model": "",
                        "used_fallback": True,
                    },
                    "evaluation": {
                        "grounded": True,
                        "has_sources": True,
                        "has_recommendations": True,
                        "issues": ["Fallback mode used; clinical review still required."],
                    },
                },
                {
                    "domain": "banking_assistant",
                    "title": "Banking Assistant Dashboard Report",
                    "summary": "The retrieved banking context points to ATM complaint logging, withdrawal limits, and fee communication as the key support actions.",
                    "status": {"level": "success", "issues": []},
                    "metrics": [
                        {"label": "Matched Documents", "value": "2", "unit": "documents"},
                        {"label": "Matched Sources", "value": "2", "unit": "sources"},
                    ],
                    "highlights": [
                        {
                            "title": "ATM complaint workflow present",
                            "severity": "medium",
                            "detail": "The banking guidance requires transaction-reference logging and branch follow-up for failed ATM debits.",
                        },
                        {
                            "title": "Fee policy identified",
                            "severity": "high",
                            "detail": "The retrieved material includes service-charge and penalty clauses that should be explained clearly to customers.",
                        },
                    ],
                    "actions": [
                        {"priority": 1, "action": "Log failed ATM debit cases with transaction reference and assign branch follow-up within 24 hours."},
                        {"priority": 2, "action": "Explain applicable service charges or penalties in customer-facing language before resolution."},
                    ],
                    "source_count": 2,
                    "execution": {
                        "workflow_backend": "query_pipeline",
                        "agent_type": "banking_assistant",
                        "provider_mode": "fallback",
                        "provider_model": "",
                        "used_fallback": True,
                    },
                    "evaluation": {
                        "grounded": True,
                        "has_sources": True,
                        "has_recommendations": True,
                        "issues": [],
                    },
                },
                {
                    "domain": "automotive",
                    "title": "Automotive Dashboard Report",
                    "summary": "The retrieved automotive context points to DTC validation, brake inspection, and scheduled maintenance checks as the key next actions.",
                    "status": {"level": "success", "issues": []},
                    "metrics": [
                        {"label": "Matched Documents", "value": "2", "unit": "documents"},
                        {"label": "Matched Sources", "value": "2", "unit": "sources"},
                    ],
                    "highlights": [
                        {
                            "title": "Diagnostic evidence found",
                            "severity": "high",
                            "detail": "The retrieved material includes fault-code and subsystem evidence relevant to repair triage.",
                        },
                        {
                            "title": "Maintenance guidance present",
                            "severity": "medium",
                            "detail": "The service context includes inspection and maintenance actions that should be applied before closure.",
                        },
                    ],
                    "actions": [
                        {"priority": 1, "action": "Validate the DTC against the diagnostic procedure before replacing components."},
                        {"priority": 2, "action": "Apply the cited brake and maintenance inspection steps to the service checklist."},
                    ],
                    "source_count": 2,
                    "execution": {
                        "workflow_backend": "query_pipeline",
                        "agent_type": "automotive",
                        "provider_mode": "fallback",
                        "provider_model": "",
                        "used_fallback": True,
                    },
                    "evaluation": {
                        "grounded": True,
                        "has_sources": True,
                        "has_recommendations": True,
                        "issues": [],
                    },
                },
                {
                    "domain": "manufacturing",
                    "title": "Manufacturing Dashboard Report",
                    "summary": "The retrieved manufacturing context points to corrective action, SOP validation, and line-restart controls as the key next steps.",
                    "status": {"level": "success", "issues": []},
                    "metrics": [
                        {"label": "Matched Documents", "value": "2", "unit": "documents"},
                        {"label": "Matched Sources", "value": "2", "unit": "sources"},
                    ],
                    "highlights": [
                        {
                            "title": "Quality incident evidence found",
                            "severity": "high",
                            "detail": "The retrieved material includes a defect or non-conformance context that should trigger corrective action ownership.",
                        },
                        {
                            "title": "Process guidance present",
                            "severity": "medium",
                            "detail": "The service context includes SOP-aligned restart or execution controls for production.",
                        },
                    ],
                    "actions": [
                        {"priority": 1, "action": "Assign root-cause ownership and update the corrective-action workflow for the quality issue."},
                        {"priority": 2, "action": "Validate the restart steps against the cited SOP before resuming production."},
                    ],
                    "source_count": 2,
                    "execution": {
                        "workflow_backend": "query_pipeline",
                        "agent_type": "manufacturing",
                        "provider_mode": "fallback",
                        "provider_model": "",
                        "used_fallback": True,
                    },
                    "evaluation": {
                        "grounded": True,
                        "has_sources": True,
                        "has_recommendations": True,
                        "issues": [],
                    },
                },
                {
                    "domain": "ecommerce",
                    "title": "Ecommerce Dashboard Report",
                    "summary": "The retrieved ecommerce context points to refund policy validation, order-status confirmation, and stock-aware customer guidance as the key next steps.",
                    "status": {"level": "success", "issues": []},
                    "metrics": [
                        {"label": "Matched Documents", "value": "2", "unit": "documents"},
                        {"label": "Matched Sources", "value": "2", "unit": "sources"},
                    ],
                    "highlights": [
                        {
                            "title": "Returns policy evidence found",
                            "severity": "high",
                            "detail": "The retrieved material includes return or refund rules that should guide support decisions.",
                        },
                        {
                            "title": "Order operations context present",
                            "severity": "medium",
                            "detail": "The service context includes shipment, delivery, or order-status evidence relevant to customer response handling.",
                        },
                    ],
                    "actions": [
                        {"priority": 1, "action": "Validate refund eligibility against the cited return policy before approving customer compensation."},
                        {"priority": 2, "action": "Confirm the order and shipment state against retrieved support evidence before updating the customer."},
                    ],
                    "source_count": 2,
                    "execution": {
                        "workflow_backend": "query_pipeline",
                        "agent_type": "ecommerce",
                        "provider_mode": "fallback",
                        "provider_model": "",
                        "used_fallback": True,
                    },
                    "evaluation": {
                        "grounded": True,
                        "has_sources": True,
                        "has_recommendations": True,
                        "issues": [],
                    },
                },
            ]
        }
    )

    domain: str
    title: str
    summary: str
    status: DashboardStatus
    metrics: List[DashboardMetric] = Field(default_factory=list)
    highlights: List[DashboardHighlight] = Field(default_factory=list)
    actions: List[DashboardAction] = Field(default_factory=list)
    matched_sources: List[DashboardMatchedSource] = Field(default_factory=list)
    evidence_cards: List[DashboardEvidenceCard] = Field(default_factory=list)
    source_count: int
    execution: ExecutionMetadata
    evaluation: ReportEvaluation


class SourceRecord(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source_id": "sample:telecom_security:telecom_incident.txt",
                "label": "telecom_incident.txt",
                "domain": "telecom_security",
                "path": "test_data/telecom_incident.txt",
                "file_type": ".txt",
                "origin": "sample",
                "uploaded_at": None,
                "index_status": "not_indexed",
                "indexed_at": None,
                "vector_backend": "",
                "indexed_document_count": None,
            }
        }
    )

    source_id: str
    label: str
    domain: str
    path: str
    file_type: str
    origin: str
    uploaded_at: Optional[str] = None
    index_status: str = "not_indexed"
    indexed_at: Optional[str] = None
    vector_backend: str = ""
    indexed_document_count: Optional[int] = None


class SourceListResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sources": [
                    {
                        "source_id": "sample:telecom_security:telecom_incident.txt",
                        "label": "telecom_incident.txt",
                        "domain": "telecom_security",
                        "path": "test_data/telecom_incident.txt",
                        "file_type": ".txt",
                        "origin": "sample",
                        "uploaded_at": None,
                        "index_status": "indexed",
                        "indexed_at": "2026-07-29T08:30:00+00:00",
                        "vector_backend": "qdrant_persistent",
                        "indexed_document_count": 2,
                    },
                    {
                        "source_id": "upload:20260728061500_field_notes.txt",
                        "label": "field_notes.txt",
                        "domain": "general",
                        "path": "uploaded_sources/20260728061500_field_notes.txt",
                        "file_type": ".txt",
                        "origin": "upload",
                        "uploaded_at": "2026-07-28T06:15:00+00:00",
                        "index_status": "not_indexed",
                        "indexed_at": None,
                        "vector_backend": "",
                        "indexed_document_count": None,
                    },
                ]
            }
        }
    )

    sources: List[SourceRecord]


class UploadSourceResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source": {
                    "source_id": "upload:20260728061500_field_notes.txt",
                    "label": "field_notes.txt",
                    "domain": "general",
                    "path": "uploaded_sources/20260728061500_field_notes.txt",
                    "file_type": ".txt",
                    "origin": "upload",
                    "uploaded_at": "2026-07-28T06:15:00+00:00",
                    "index_status": "not_indexed",
                    "indexed_at": None,
                    "vector_backend": "",
                    "indexed_document_count": None,
                }
            }
        }
    )

    source: SourceRecord


class DeleteSourceResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source_id": "upload:20260728061500_field_notes.txt",
                "deleted": True,
            }
        }
    )

    source_id: str
    deleted: bool = True


class ReindexSourceResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source_id": "sample:ecommerce:return_policy.md",
                "indexed": True,
                "document_count": 4,
                "vector_backend": "qdrant_persistent",
            }
        }
    )

    source_id: str
    indexed: bool = True
    document_count: int
    vector_backend: str


class UploadSourceRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "filename": "field_notes.txt",
                    "domain": "general",
                    "content_base64": "U1M3IG1pdGlnYXRpb24gYWN0aW9ucyBmb3IgdGhlIG9wZXJhdGlvbnMgdGVhbS4=",
                },
                {
                    "filename": "medical_case_summary.json",
                    "domain": "medical_qa",
                    "content_base64": "eyJjYXNlIjogIkNhcmRpYWMgcmV2aWV3IiwgIm5vdGVzIjogWyJjaGVzdCBwYWluIiwgImVjZyJdfQ==",
                },
            ]
        }
    )

    filename: str = Field(..., min_length=1)
    domain: str = Field(default="general", min_length=1)
    content_base64: str = Field(..., min_length=1)


class QueryRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "query": "What action is recommended for the SS7 issue?",
                    "retrieval_mode": "source",
                    "source_id": "sample:telecom_security:telecom_incident.txt",
                    "domain": "telecom_security",
                    "max_results": 2,
                },
                {
                    "query": "What governance control is required before export?",
                    "retrieval_mode": "source",
                    "document_path": "test_data/telecom_incident.txt",
                    "domain": "telecom_security",
                    "max_results": 3,
                },
                {
                    "query": "What are the most important healthcare escalations across this domain?",
                    "retrieval_mode": "domain",
                    "domain": "medical_qa",
                    "max_results": 4,
                },
                {
                    "query": "Summarize financial accountability rules.",
                    "retrieval_mode": "source",
                    "source_id": "sample:financial_risk:FInal_GFR_upto_31_07_2024.pdf",
                    "domain": "financial_risk",
                    "max_results": 3,
                },
                {
                    "query": "What should be done for a failed ATM debit complaint?",
                    "retrieval_mode": "source",
                    "source_id": "sample:banking_assistant:atm_notice.txt",
                    "domain": "banking_assistant",
                    "max_results": 2,
                },
                {
                    "query": "What action is associated with DTC P0420?",
                    "retrieval_mode": "source",
                    "source_id": "sample:automotive:dtc_fault_codes.csv",
                    "domain": "automotive",
                    "max_results": 2,
                },
                {
                    "query": "What should happen after a quality defect is reported?",
                    "retrieval_mode": "source",
                    "source_id": "sample:manufacturing:quality_incident.txt",
                    "domain": "manufacturing",
                    "max_results": 2,
                },
                {
                    "query": "What should be done for a delayed order with a refund request?",
                    "retrieval_mode": "source",
                    "source_id": "sample:ecommerce:customer_issue.txt",
                    "domain": "ecommerce",
                    "max_results": 2,
                },
            ]
        }
    )

    query: str = Field(
        ...,
        min_length=3,
        examples=["What action is recommended for the SS7 issue?"],
    )
    retrieval_mode: str = Field(
        default="source",
        examples=["source"],
    )
    document_path: Optional[str] = Field(
        default=None,
        min_length=1,
        examples=["test_data/telecom_incident.txt"],
    )
    source_id: Optional[str] = Field(
        default=None,
        min_length=1,
        examples=["sample:telecom_security:telecom_incident.txt"],
    )
    domain: str = Field(
        default="telecom_security",
        min_length=1,
        examples=["telecom_security"],
    )
    max_results: int = Field(default=3, ge=1, le=10, examples=[2])

    @model_validator(mode="after")
    def validate_source_reference(self):
        if self.retrieval_mode not in {"source", "domain"}:
            raise ValueError("retrieval_mode must be either 'source' or 'domain'.")
        if self.retrieval_mode == "source" and not self.document_path and not self.source_id:
            raise ValueError("Either document_path or source_id must be provided for source retrieval.")
        if self.retrieval_mode == "domain" and not self.domain:
            raise ValueError("domain must be provided for domain retrieval.")
        return self


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
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"detail": "Unsupported file type: .exe"},
                {"detail": "Only uploaded sources can be deleted."},
                {"detail": "Unknown source_id: upload:missing.txt"},
            ]
        }
    )

    detail: str
