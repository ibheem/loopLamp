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
    graph_state_score: int = 0
    graph_state_expected_fields: List[str] = Field(default_factory=list)
    graph_state_present_fields: List[str] = Field(default_factory=list)
    graph_state_missing_fields: List[str] = Field(default_factory=list)


class ExecutionMetadata(BaseModel):
    class RetrievalDecision(BaseModel):
        should_retrieve: bool = False
        search_query: str = ""
        max_results: int = 0
        rationale: str = ""
        compare_sources: bool = False
        summarize_evidence: bool = False

    class InspectionDecision(BaseModel):
        grounded: bool = False
        summary: str = ""

    class ComparisonDecision(BaseModel):
        summary: str = ""
        compared_sources: List[str] = Field(default_factory=list)
        consensus_points: List[str] = Field(default_factory=list)
        conflicts: List[str] = Field(default_factory=list)
        control_themes: List[str] = Field(default_factory=list)
        obligations: List[str] = Field(default_factory=list)
        symptoms: List[str] = Field(default_factory=list)
        red_flags: List[str] = Field(default_factory=list)
        escalation_criteria: List[str] = Field(default_factory=list)
        care_constraints: List[str] = Field(default_factory=list)
        transaction_signals: List[str] = Field(default_factory=list)
        customer_impact_checks: List[str] = Field(default_factory=list)
        fraud_indicators: List[str] = Field(default_factory=list)
        next_actions: List[str] = Field(default_factory=list)
        order_signals: List[str] = Field(default_factory=list)
        policy_constraints: List[str] = Field(default_factory=list)
        fulfillment_risks: List[str] = Field(default_factory=list)
        customer_resolution_actions: List[str] = Field(default_factory=list)
        fault_signals: List[str] = Field(default_factory=list)
        subsystem_risks: List[str] = Field(default_factory=list)
        repair_prerequisites: List[str] = Field(default_factory=list)
        safety_checks: List[str] = Field(default_factory=list)
        defect_signals: List[str] = Field(default_factory=list)
        line_impact: List[str] = Field(default_factory=list)
        containment_actions: List[str] = Field(default_factory=list)
        restart_gates: List[str] = Field(default_factory=list)

    class EvidenceSummaryDecision(BaseModel):
        summary: str = ""
        key_points: List[str] = Field(default_factory=list)
        cited_sources: List[str] = Field(default_factory=list)
        decision_basis: List[str] = Field(default_factory=list)
        recommended_controls: List[str] = Field(default_factory=list)
        follow_up_checks: List[str] = Field(default_factory=list)
        symptom_summary: List[str] = Field(default_factory=list)
        escalation_path: List[str] = Field(default_factory=list)
        patient_safety_notes: List[str] = Field(default_factory=list)
        service_actions: List[str] = Field(default_factory=list)
        customer_message_points: List[str] = Field(default_factory=list)
        fraud_follow_ups: List[str] = Field(default_factory=list)
        refund_basis: List[str] = Field(default_factory=list)
        resolution_plan: List[str] = Field(default_factory=list)
        inventory_notes: List[str] = Field(default_factory=list)
        diagnosis_summary: List[str] = Field(default_factory=list)
        repair_plan: List[str] = Field(default_factory=list)
        vehicle_safety_notes: List[str] = Field(default_factory=list)
        containment_summary: List[str] = Field(default_factory=list)
        production_actions: List[str] = Field(default_factory=list)
        quality_follow_ups: List[str] = Field(default_factory=list)

    class AgentTraceStep(BaseModel):
        label: str
        detail: str
        status: str = "info"

    class AgentTrace(BaseModel):
        planned_query: str = ""
        plan_rationale: str = ""
        comparison_summary: str = ""
        evidence_summary: str = ""
        summary_digest: str = ""
        grounded: bool = False
        added_sources: List[str] = Field(default_factory=list)
        steps: List["ExecutionMetadata.AgentTraceStep"] = Field(default_factory=list)

    workflow_backend: str
    agent_type: str
    requested_provider: str = "auto"
    requested_model: str = ""
    provider_mode: str
    provider_model: str = ""
    llm_generated: bool = False
    used_fallback: bool = False
    tool_calls: int = 0
    agent_loop: str = "retrieve_generate"
    plan: Optional[RetrievalDecision] = None
    comparison: Optional[ComparisonDecision] = None
    evidence_summary: Optional[EvidenceSummaryDecision] = None
    inspection: Optional[InspectionDecision] = None
    agent_trace: AgentTrace = Field(default_factory=AgentTrace)


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


class DashboardDomainCard(BaseModel):
    title: str
    value: str
    detail: str
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
                    "domain_cards": [
                        {
                            "title": "Matched Sources",
                            "value": "1",
                            "detail": "One telecom source contributed evidence to this dashboard response.",
                            "severity": "info",
                        }
                    ],
                    "source_count": 2,
                    "execution": {
                        "workflow_backend": "query_pipeline",
                        "agent_type": "telecom_security",
                        "provider_mode": "fallback",
                        "provider_model": "",
                        "used_fallback": True,
                        "tool_calls": 3,
                        "agent_loop": "plan_retrieve_compare_summarize_inspect_generate",
                        "plan": {
                            "should_retrieve": True,
                            "search_query": "ss7 route isolate action",
                            "max_results": 2,
                            "rationale": "The initial evidence shows impact but needs a more action-oriented retrieval.",
                            "compare_sources": True,
                            "summarize_evidence": True,
                        },
                        "comparison": {
                            "summary": "The action chunk and the incident chunk agree that SS7 route isolation is the immediate mitigation.",
                            "compared_sources": ["telecom_incident.txt", "telecom_playbook.txt"],
                            "consensus_points": ["Route isolation is the immediate step."],
                            "conflicts": [],
                        },
                        "evidence_summary": {
                            "summary": "Cross-source evidence supports isolating the route first and validating screening controls next.",
                            "key_points": ["Isolate the affected route.", "Validate interconnect screening controls."],
                            "cited_sources": ["telecom_incident.txt", "telecom_playbook.txt"],
                        },
                        "inspection": {
                            "grounded": True,
                            "summary": "The retrieved evidence now includes the mitigation step for the affected route.",
                        },
                        "agent_trace": {
                            "planned_query": "ss7 route isolate action",
                            "plan_rationale": "The initial evidence shows impact but needs a more action-oriented retrieval.",
                            "comparison_summary": "The action chunk and the incident chunk agree that SS7 route isolation is the immediate mitigation.",
                            "evidence_summary": "The retrieved evidence now includes the mitigation step for the affected route.",
                            "summary_digest": "Cross-source evidence supports isolating the route first and validating screening controls next.",
                            "grounded": True,
                            "added_sources": ["telecom_playbook.txt"],
                            "steps": [
                                {"label": "Initial Retrieval", "detail": "Started with 1 retrieved evidence chunk(s).", "status": "info"},
                                {"label": "Plan", "detail": "The initial evidence shows impact but needs a more action-oriented retrieval.", "status": "info"},
                                {"label": "Retrieve Sources", "detail": "Retrieve tool added 1 source(s): telecom_playbook.txt.", "status": "success"},
                                {"label": "Compare Sources", "detail": "The action chunk and the incident chunk agree that SS7 route isolation is the immediate mitigation.", "status": "success"},
                                {"label": "Summarize Evidence", "detail": "Cross-source evidence supports isolating the route first and validating screening controls next.", "status": "success"},
                                {"label": "Evidence Review", "detail": "The retrieved evidence now includes the mitigation step for the affected route.", "status": "success"},
                                {"label": "Generate", "detail": "Generated the final telecom security report from 2 chunk(s).", "status": "success"},
                            ],
                        },
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
                        "tool_calls": 3,
                        "agent_loop": "plan_retrieve_compare_summarize_inspect_generate",
                        "plan": {
                            "should_retrieve": True,
                            "search_query": "financial authority approval audit control",
                            "max_results": 3,
                            "rationale": "The agent refined retrieval toward approval and audit clauses before summarizing controls.",
                            "compare_sources": True,
                            "summarize_evidence": True,
                        },
                        "comparison": {
                            "summary": "The finance sources align on delegated approval authority and audit-ready release controls.",
                            "compared_sources": ["finance_policy.pdf", "finance_control_policy.pdf"],
                            "consensus_points": ["Fund release requires sanctioned authority."],
                            "conflicts": ["Exception escalation language is less explicit in one source."],
                            "control_themes": ["delegated_authority", "audit_traceability", "release_governance"],
                            "obligations": ["Validate approver authority", "Retain approval trail"],
                        },
                        "evidence_summary": {
                            "summary": "The combined finance evidence supports approval validation first, then audit-traceable release execution.",
                            "key_points": ["Verify sanction authority.", "Retain approval evidence for audit."],
                            "cited_sources": ["finance_policy.pdf", "finance_control_policy.pdf"],
                            "decision_basis": ["Delegated authority clauses are explicit.", "Audit retention language is consistent."],
                            "recommended_controls": ["Check sanction matrix", "Record release approvals"],
                            "follow_up_checks": ["Confirm exception escalation owner", "Validate audit evidence completeness"],
                        },
                        "inspection": {
                            "grounded": True,
                            "summary": "The combined evidence supports approval-gated release and audit traceability.",
                        },
                        "agent_trace": {
                            "planned_query": "financial authority approval audit control",
                            "plan_rationale": "The agent refined retrieval toward approval and audit clauses before summarizing controls.",
                            "comparison_summary": "The finance sources align on delegated approval authority and audit-ready release controls.",
                            "evidence_summary": "The combined evidence supports approval-gated release and audit traceability.",
                            "summary_digest": "The combined finance evidence supports approval validation first, then audit-traceable release execution.",
                            "grounded": True,
                            "added_sources": ["finance_control_policy.pdf"],
                            "steps": [
                                {"label": "Initial Retrieval", "detail": "Started with 2 retrieved evidence chunk(s).", "status": "info"},
                                {"label": "Plan", "detail": "The agent refined retrieval toward approval and audit clauses before summarizing controls.", "status": "info"},
                                {"label": "Retrieve Sources", "detail": "Retrieve tool added 1 source(s): finance_control_policy.pdf.", "status": "success"},
                                {"label": "Compare Sources", "detail": "The finance sources align on delegated approval authority and audit-ready release controls.", "status": "success"},
                                {"label": "Summarize Evidence", "detail": "The combined finance evidence supports approval validation first, then audit-traceable release execution.", "status": "success"},
                                {"label": "Evidence Review", "detail": "The combined evidence supports approval-gated release and audit traceability.", "status": "success"},
                                {"label": "Generate", "detail": "Generated the final financial risk report from 3 chunk(s).", "status": "success"},
                            ],
                        },
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
                        "provider_mode": "llm",
                        "provider_model": "gpt-4.1-mini",
                        "used_fallback": False,
                        "tool_calls": 3,
                        "agent_loop": "plan_retrieve_compare_summarize_inspect_generate",
                        "plan": {
                            "should_retrieve": True,
                            "search_query": "persistent chest pain red flags escalation guidance",
                            "max_results": 3,
                            "rationale": "The agent refined retrieval toward red-flag escalation evidence before final clinical guidance.",
                            "compare_sources": True,
                            "summarize_evidence": True,
                        },
                        "comparison": {
                            "summary": "The clinical sources align on persistent chest pain as a red-flag pattern that warrants escalation.",
                            "compared_sources": ["clinical_guide.pdf", "triage_notes.txt"],
                            "consensus_points": ["Persistent chest pain needs clinician escalation."],
                            "conflicts": [],
                            "symptoms": ["chest pain", "persistent discomfort"],
                            "red_flags": ["persistent chest pain", "worsening symptoms"],
                            "escalation_criteria": ["ongoing pain despite rest", "progressive severity"],
                            "care_constraints": ["not a final diagnosis", "contraindications must be reviewed"],
                        },
                        "evidence_summary": {
                            "summary": "The clinical evidence supports urgent escalation for persistent chest pain and cautious contraindication review.",
                            "key_points": ["Escalate persistent chest pain.", "Review contraindications before applying medication guidance."],
                            "cited_sources": ["clinical_guide.pdf", "triage_notes.txt"],
                            "symptom_summary": ["Persistent chest pain is the dominant symptom pattern."],
                            "escalation_path": ["Escalate for urgent clinician review", "Avoid relying on self-management alone"],
                            "patient_safety_notes": ["Clinical review is required before acting on medication advice"],
                        },
                        "inspection": {
                            "grounded": True,
                            "summary": "The medical evidence supports symptom escalation and safety caveats.",
                        },
                        "agent_trace": {
                            "planned_query": "persistent chest pain red flags escalation guidance",
                            "plan_rationale": "The agent refined retrieval toward red-flag escalation evidence before final clinical guidance.",
                            "comparison_summary": "The clinical sources align on persistent chest pain as a red-flag pattern that warrants escalation.",
                            "evidence_summary": "The medical evidence supports symptom escalation and safety caveats.",
                            "summary_digest": "The clinical evidence supports urgent escalation for persistent chest pain and cautious contraindication review.",
                            "grounded": True,
                            "added_sources": ["triage_notes.txt"],
                            "steps": [
                                {"label": "Initial Retrieval", "detail": "Started with 1 retrieved evidence chunk(s).", "status": "info"},
                                {"label": "Plan", "detail": "The agent refined retrieval toward red-flag escalation evidence before final clinical guidance.", "status": "info"},
                                {"label": "Retrieve Sources", "detail": "Retrieve tool added 1 source(s): triage_notes.txt.", "status": "success"},
                                {"label": "Compare Sources", "detail": "The clinical sources align on persistent chest pain as a red-flag pattern that warrants escalation.", "status": "success"},
                                {"label": "Summarize Evidence", "detail": "The clinical evidence supports urgent escalation for persistent chest pain and cautious contraindication review.", "status": "success"},
                                {"label": "Evidence Review", "detail": "The medical evidence supports symptom escalation and safety caveats.", "status": "success"},
                                {"label": "Generate", "detail": "Generated the final medical qa report from 2 chunk(s).", "status": "success"},
                            ],
                        },
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
                        "provider_mode": "llm",
                        "provider_model": "gpt-4.1-mini",
                        "used_fallback": False,
                        "tool_calls": 3,
                        "agent_loop": "plan_retrieve_compare_summarize_inspect_generate",
                        "plan": {
                            "should_retrieve": True,
                            "search_query": "duplicate debit complaint transaction reference fraud review",
                            "max_results": 3,
                            "rationale": "The agent refined retrieval toward transaction validation and fraud follow-up evidence.",
                            "compare_sources": True,
                            "summarize_evidence": True,
                        },
                        "comparison": {
                            "summary": "The banking sources align on transaction-reference review first, followed by customer impact checks and fraud screening.",
                            "compared_sources": ["transactions.csv", "atm_notice.txt"],
                            "consensus_points": ["Transaction reference validation is required first."],
                            "conflicts": [],
                            "transaction_signals": ["duplicate debit", "failed ATM cash withdrawal"],
                            "customer_impact_checks": ["confirm debit status", "check whether cash was dispensed"],
                            "fraud_indicators": ["unexpected repeat debits", "unrecognized ATM usage"],
                            "next_actions": ["capture transaction reference", "escalate fraud review if indicators persist"],
                        },
                        "evidence_summary": {
                            "summary": "The banking evidence supports transaction validation, clear customer communication, and fraud escalation where suspicious debit patterns remain.",
                            "key_points": ["Validate the transaction trail first.", "Escalate suspicious repeat debits."],
                            "cited_sources": ["transactions.csv", "atm_notice.txt"],
                            "service_actions": ["Log the complaint with transaction reference", "Check the ATM reversal window"],
                            "customer_message_points": ["Explain review status clearly", "Set expectation for reversal or escalation timing"],
                            "fraud_follow_ups": ["Review suspicious repeat debit pattern", "Confirm whether card usage was authorized"],
                        },
                        "inspection": {
                            "grounded": True,
                            "summary": "The banking evidence supports transaction validation, customer communication, and fraud follow-up.",
                        },
                        "agent_trace": {
                            "planned_query": "duplicate debit complaint transaction reference fraud review",
                            "plan_rationale": "The agent refined retrieval toward transaction validation and fraud follow-up evidence.",
                            "comparison_summary": "The banking sources align on transaction-reference review first, followed by customer impact checks and fraud screening.",
                            "evidence_summary": "The banking evidence supports transaction validation, customer communication, and fraud follow-up.",
                            "summary_digest": "The banking evidence supports transaction validation, clear customer communication, and fraud escalation where suspicious debit patterns remain.",
                            "grounded": True,
                            "added_sources": ["atm_notice.txt"],
                            "steps": [
                                {"label": "Initial Retrieval", "detail": "Started with 1 retrieved evidence chunk(s).", "status": "info"},
                                {"label": "Plan", "detail": "The agent refined retrieval toward transaction validation and fraud follow-up evidence.", "status": "info"},
                                {"label": "Retrieve Sources", "detail": "Retrieve tool added 1 source(s): atm_notice.txt.", "status": "success"},
                                {"label": "Compare Sources", "detail": "The banking sources align on transaction-reference review first, followed by customer impact checks and fraud screening.", "status": "success"},
                                {"label": "Summarize Evidence", "detail": "The banking evidence supports transaction validation, clear customer communication, and fraud escalation where suspicious debit patterns remain.", "status": "success"},
                                {"label": "Evidence Review", "detail": "The banking evidence supports transaction validation, customer communication, and fraud follow-up.", "status": "success"},
                                {"label": "Generate", "detail": "Generated the final banking assistant report from 2 chunk(s).", "status": "success"},
                            ],
                        },
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
                        "provider_mode": "llm",
                        "provider_model": "gpt-4.1-mini",
                        "used_fallback": False,
                        "tool_calls": 3,
                        "agent_loop": "plan_retrieve_compare_summarize_inspect_generate",
                        "plan": {
                            "should_retrieve": True,
                            "search_query": "dtc brake inspection corrective action",
                            "max_results": 2,
                            "rationale": "The agent narrowed retrieval toward diagnostic and brake-specific action guidance.",
                            "compare_sources": True,
                            "summarize_evidence": True,
                        },
                        "comparison": {
                            "summary": "The automotive sources align on confirming the DTC first, checking the brake subsystem, and completing safety inspections before repair.",
                            "compared_sources": ["service_manual.txt", "dtc_fault_codes.csv"],
                            "consensus_points": ["Validate the DTC before replacing parts."],
                            "conflicts": [],
                            "fault_signals": ["P0420", "brake warning"],
                            "subsystem_risks": ["brake subsystem", "emissions control"],
                            "repair_prerequisites": ["confirm DTC", "inspect pads and rotors"],
                            "safety_checks": ["verify braking response", "review service-condition checks before release"],
                        },
                        "evidence_summary": {
                            "summary": "The automotive evidence supports DTC validation first, targeted brake inspection next, and safety confirmation before vehicle release.",
                            "key_points": ["Validate the DTC.", "Inspect brake hardware before replacement."],
                            "cited_sources": ["service_manual.txt", "dtc_fault_codes.csv"],
                            "diagnosis_summary": ["P0420 and brake warning need confirmation against diagnostic steps."],
                            "repair_plan": ["Confirm the DTC", "Inspect brake pads and rotors", "Apply maintenance checks before closure"],
                            "vehicle_safety_notes": ["Verify braking response before return to service"],
                        },
                        "inspection": {
                            "grounded": True,
                            "summary": "The evidence supports DTC validation before component replacement.",
                        },
                        "agent_trace": {
                            "planned_query": "dtc brake inspection corrective action",
                            "plan_rationale": "The agent narrowed retrieval toward diagnostic and brake-specific action guidance.",
                            "comparison_summary": "The automotive sources align on confirming the DTC first, checking the brake subsystem, and completing safety inspections before repair.",
                            "evidence_summary": "The evidence supports DTC validation before component replacement.",
                            "summary_digest": "The automotive evidence supports DTC validation first, targeted brake inspection next, and safety confirmation before vehicle release.",
                            "grounded": True,
                            "added_sources": ["dtc_fault_codes.csv"],
                            "steps": [
                                {"label": "Initial Retrieval", "detail": "Started with 1 retrieved evidence chunk(s).", "status": "info"},
                                {"label": "Plan", "detail": "The agent narrowed retrieval toward diagnostic and brake-specific action guidance.", "status": "info"},
                                {"label": "Retrieve Sources", "detail": "Retrieve tool added 1 source(s): dtc_fault_codes.csv.", "status": "success"},
                                {"label": "Compare Sources", "detail": "The automotive sources align on confirming the DTC first, checking the brake subsystem, and completing safety inspections before repair.", "status": "success"},
                                {"label": "Summarize Evidence", "detail": "The automotive evidence supports DTC validation first, targeted brake inspection next, and safety confirmation before vehicle release.", "status": "success"},
                                {"label": "Evidence Review", "detail": "The evidence supports DTC validation before component replacement.", "status": "success"},
                                {"label": "Generate", "detail": "Generated the final automotive report from 2 chunk(s).", "status": "success"},
                            ],
                        },
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
                        "provider_mode": "llm",
                        "provider_model": "gpt-4.1-mini",
                        "used_fallback": False,
                        "tool_calls": 3,
                        "agent_loop": "plan_retrieve_compare_summarize_inspect_generate",
                        "plan": {
                            "should_retrieve": True,
                            "search_query": "manufacturing defect containment restart approval",
                            "max_results": 2,
                            "rationale": "The agent refined toward restart controls and containment evidence.",
                            "compare_sources": True,
                            "summarize_evidence": True,
                        },
                        "comparison": {
                            "summary": "The manufacturing sources align on defect containment, SOP validation, and quality-approved restart before resuming the line.",
                            "compared_sources": ["quality_incident.txt", "sop_guidelines.md"],
                            "consensus_points": ["Containment must precede restart."],
                            "conflicts": [],
                            "defect_signals": ["quality defect", "deviation"],
                            "line_impact": ["line restart blocked", "throughput disruption"],
                            "containment_actions": ["isolate affected lot", "assign corrective-action owner"],
                            "restart_gates": ["validate SOP step", "confirm quality approval before restart"],
                        },
                        "evidence_summary": {
                            "summary": "The manufacturing evidence supports immediate containment, SOP confirmation, and quality-approved restart only after corrective ownership is clear.",
                            "key_points": ["Contain the affected material.", "Require quality approval before restart."],
                            "cited_sources": ["quality_incident.txt", "sop_guidelines.md"],
                            "containment_summary": ["The affected lot should be isolated and tracked."],
                            "production_actions": ["Validate the current step against SOP", "Hold restart until corrective ownership is assigned"],
                            "quality_follow_ups": ["Confirm root-cause ownership", "Verify restart approval evidence"],
                        },
                        "inspection": {
                            "grounded": True,
                            "summary": "The retrieved material supports containment and approval before restart.",
                        },
                        "agent_trace": {
                            "planned_query": "manufacturing defect containment restart approval",
                            "plan_rationale": "The agent refined toward restart controls and containment evidence.",
                            "comparison_summary": "The manufacturing sources align on defect containment, SOP validation, and quality-approved restart before resuming the line.",
                            "evidence_summary": "The retrieved material supports containment and approval before restart.",
                            "summary_digest": "The manufacturing evidence supports immediate containment, SOP confirmation, and quality-approved restart only after corrective ownership is clear.",
                            "grounded": True,
                            "added_sources": ["quality_incident.txt"],
                            "steps": [
                                {"label": "Initial Retrieval", "detail": "Started with 1 retrieved evidence chunk(s).", "status": "info"},
                                {"label": "Plan", "detail": "The agent refined toward restart controls and containment evidence.", "status": "info"},
                                {"label": "Retrieve Sources", "detail": "Retrieve tool added 1 source(s): quality_incident.txt.", "status": "success"},
                                {"label": "Compare Sources", "detail": "The manufacturing sources align on defect containment, SOP validation, and quality-approved restart before resuming the line.", "status": "success"},
                                {"label": "Summarize Evidence", "detail": "The manufacturing evidence supports immediate containment, SOP confirmation, and quality-approved restart only after corrective ownership is clear.", "status": "success"},
                                {"label": "Evidence Review", "detail": "The retrieved material supports containment and approval before restart.", "status": "success"},
                                {"label": "Generate", "detail": "Generated the final manufacturing report from 2 chunk(s).", "status": "success"},
                            ],
                        },
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
                        "provider_mode": "llm",
                        "provider_model": "gpt-4.1-mini",
                        "used_fallback": False,
                        "tool_calls": 3,
                        "agent_loop": "plan_retrieve_compare_summarize_inspect_generate",
                        "plan": {
                            "should_retrieve": True,
                            "search_query": "refund eligibility delayed shipment review",
                            "max_results": 2,
                            "rationale": "The agent refined toward refund and delay evidence before answering support actions.",
                            "compare_sources": True,
                            "summarize_evidence": True,
                        },
                        "comparison": {
                            "summary": "The ecommerce sources align on delayed-shipment refund review, policy-window constraints, and stock-aware resolution handling.",
                            "compared_sources": ["customer_issue.txt", "return_policy.md", "orders.csv"],
                            "consensus_points": ["Refund handling depends on policy window and shipment state."],
                            "conflicts": [],
                            "order_signals": ["delayed shipment", "refund requested"],
                            "policy_constraints": ["7-day exchange window", "refund review required before approval"],
                            "fulfillment_risks": ["shipment delay", "inventory-dependent replacement path"],
                            "customer_resolution_actions": ["validate policy eligibility", "confirm shipment status before promising resolution"],
                        },
                        "evidence_summary": {
                            "summary": "The ecommerce evidence supports validating refund eligibility against the return window, checking shipment status, and using inventory-aware resolution steps.",
                            "key_points": ["Refund approval depends on policy eligibility.", "Shipment status must be confirmed before resolution."],
                            "cited_sources": ["customer_issue.txt", "return_policy.md", "orders.csv"],
                            "refund_basis": ["Return policy defines eligibility window.", "Delayed shipment alone does not bypass policy review."],
                            "resolution_plan": ["Validate the policy window", "Confirm shipment state", "Offer exchange only if stock allows"],
                            "inventory_notes": ["Replacement path depends on stock availability"],
                        },
                        "inspection": {
                            "grounded": True,
                            "summary": "The retrieved evidence supports refund validation against delay and policy windows.",
                        },
                        "agent_trace": {
                            "planned_query": "refund eligibility delayed shipment review",
                            "plan_rationale": "The agent refined toward refund and delay evidence before answering support actions.",
                            "comparison_summary": "The ecommerce sources align on delayed-shipment refund review, policy-window constraints, and stock-aware resolution handling.",
                            "evidence_summary": "The retrieved evidence supports refund validation against delay and policy windows.",
                            "summary_digest": "The ecommerce evidence supports validating refund eligibility against the return window, checking shipment status, and using inventory-aware resolution steps.",
                            "grounded": True,
                            "added_sources": ["return_policy.md"],
                            "steps": [
                                {"label": "Initial Retrieval", "detail": "Started with 1 retrieved evidence chunk(s).", "status": "info"},
                                {"label": "Plan", "detail": "The agent refined toward refund and delay evidence before answering support actions.", "status": "info"},
                                {"label": "Retrieve Sources", "detail": "Retrieve tool added 1 source(s): return_policy.md.", "status": "success"},
                                {"label": "Compare Sources", "detail": "The ecommerce sources align on delayed-shipment refund review, policy-window constraints, and stock-aware resolution handling.", "status": "success"},
                                {"label": "Summarize Evidence", "detail": "The ecommerce evidence supports validating refund eligibility against the return window, checking shipment status, and using inventory-aware resolution steps.", "status": "success"},
                                {"label": "Evidence Review", "detail": "The retrieved evidence supports refund validation against delay and policy windows.", "status": "success"},
                                {"label": "Generate", "detail": "Generated the final ecommerce report from 2 chunk(s).", "status": "success"},
                            ],
                        },
                    },
                    "evaluation": {
                        "grounded": True,
                        "has_sources": True,
                        "has_recommendations": True,
                        "issues": [],
                        "graph_state_score": 100,
                        "graph_state_expected_fields": [
                            "comparison.order_signals",
                            "comparison.policy_constraints",
                            "comparison.customer_resolution_actions",
                            "evidence_summary.refund_basis",
                            "evidence_summary.resolution_plan",
                        ],
                        "graph_state_present_fields": [
                            "comparison.order_signals",
                            "comparison.policy_constraints",
                            "comparison.customer_resolution_actions",
                            "evidence_summary.refund_basis",
                            "evidence_summary.resolution_plan",
                        ],
                        "graph_state_missing_fields": [],
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
    domain_cards: List[DashboardDomainCard] = Field(default_factory=list)
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


class LLMProviderRecord(BaseModel):
    provider_id: str
    label: str
    description: str
    available: bool
    configured: bool = False
    reachable: bool = False
    health_message: str = ""
    default_model: str = ""
    models: List[str] = Field(default_factory=list)
    supports_custom_model: bool = True


class LLMProviderCatalogResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "default_provider_id": "auto",
                "providers": [
                    {
                        "provider_id": "auto",
                        "label": "Auto",
                        "description": "Use the first configured provider in the fallback chain.",
                        "available": True,
                        "configured": True,
                        "reachable": True,
                        "health_message": "Automatic provider resolution is always available.",
                        "default_model": "",
                        "models": [],
                        "supports_custom_model": False,
                    },
                    {
                        "provider_id": "openai",
                        "label": "OpenAI",
                        "description": "Uses the native OpenAI Responses API integration.",
                        "available": True,
                        "configured": True,
                        "reachable": True,
                        "health_message": "Provider responded to the health check.",
                        "default_model": "gpt-5-mini",
                        "models": ["gpt-5-mini", "gpt-5.1", "gpt-4.1-mini"],
                        "supports_custom_model": True,
                    },
                ],
            }
        }
    )

    default_provider_id: str = "auto"
    providers: List[LLMProviderRecord]


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
                    "llm_provider": "auto",
                    "max_results": 2,
                },
                {
                    "query": "What governance control is required before export?",
                    "retrieval_mode": "source",
                    "document_path": "test_data/telecom_incident.txt",
                    "domain": "telecom_security",
                    "llm_provider": "openai",
                    "llm_model": "gpt-5-mini",
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
    llm_provider: str = Field(default="auto", min_length=1, examples=["auto"])
    llm_model: Optional[str] = Field(default=None, min_length=1, examples=["gpt-5-mini"])
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
