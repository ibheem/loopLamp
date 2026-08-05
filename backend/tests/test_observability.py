from backend.agents.openai_report_agent import OpenAIReportAgent
from backend.agents.telecom_security import TelecomSecurityAgent
from backend.agents.tool_calling_report_agent import ToolCallingReportAgent
from backend.core.documents import Document
from backend.core.models import DomainInsight, DomainReport, QueryRequest
from backend.services.llm_provider import (
    EvidenceReview,
    EvidenceSummary,
    ProviderUnavailableError,
    ReportLLMProvider,
    RetrievalPlan,
    SourceComparison,
)
from backend.services.report_evaluator import evaluate_report
from backend.services.vector_store import InMemoryVectorStore
from backend.workflows import query_pipeline as query_pipeline_module
from backend.workflows.query_pipeline import QueryPipeline


class FailingProvider(ReportLLMProvider):
    model = "gpt-5-mini"

    def is_available(self) -> bool:
        return False

    def generate_report(self, domain, query, context_documents, source_refs):
        raise ProviderUnavailableError("missing credentials")


class ToolLoopProvider(ReportLLMProvider):
    model = "gpt-5-mini"

    def is_available(self) -> bool:
        return True

    def plan_retrieval(self, domain, query, context_documents, source_refs):
        return RetrievalPlan(
            should_retrieve=True,
            search_query="isolate route action",
            max_results=2,
            rationale="Need the action-oriented chunk.",
            compare_sources=True,
            summarize_evidence=True,
        )

    def compare_sources(self, domain, query, context_documents, source_refs):
        return SourceComparison(
            summary="The retrieved evidence agrees on route isolation and control validation.",
            compared_sources=["test_data/telecom_incident.txt"],
            consensus_points=["Route isolation is the immediate action."],
        )

    def summarize_evidence(self, domain, query, context_documents, source_refs):
        return EvidenceSummary(
            summary="The evidence synthesis supports isolation first, then control validation.",
            key_points=["Isolate the route.", "Validate controls after containment."],
            cited_sources=["test_data/telecom_incident.txt"],
        )

    def inspect_evidence(self, domain, query, context_documents, source_refs):
        return EvidenceReview(
            grounded=True,
            summary="The evidence now includes both impact and action.",
        )

    def generate_report(self, domain, query, context_documents, source_refs, comparison=None, evidence_summary=None):
        return DomainReport(
            domain=domain,
            summary="Based on the retrieved context, isolate the route and validate controls.",
            insights=[DomainInsight(title="Action grounded", severity="high", detail="Action guidance is present.")],
            source_refs=source_refs,
        )


class FinancialRiskToolLoopProvider(ReportLLMProvider):
    model = "gpt-5-mini"

    def is_available(self) -> bool:
        return True

    def plan_retrieval(self, domain, query, context_documents, source_refs):
        return RetrievalPlan(
            should_retrieve=True,
            search_query="approval authority audit traceability release control",
            max_results=3,
            rationale="Need explicit approval authority and audit clauses before final finance guidance.",
            compare_sources=True,
            summarize_evidence=True,
        )

    def compare_sources(self, domain, query, context_documents, source_refs):
        return SourceComparison(
            summary="The financial sources align on delegated approval authority and audit-ready release controls.",
            compared_sources=["policy_a.pdf", "policy_b.pdf"],
            consensus_points=["Fund release requires sanctioned authority."],
            conflicts=["One clause leaves exception escalation less explicit."],
            control_themes=["delegated_authority", "audit_traceability", "release_governance"],
            obligations=["Validate approver authority", "Preserve documentary audit trail"],
        )

    def summarize_evidence(self, domain, query, context_documents, source_refs):
        return EvidenceSummary(
            summary="The finance evidence supports approval validation first, then audit-traceable release execution.",
            key_points=["Approval authority must be verified.", "Audit documentation must be retained."],
            cited_sources=["policy_a.pdf", "policy_b.pdf"],
            decision_basis=["Delegated authority clauses are explicit.", "Audit retention language is consistent."],
            recommended_controls=["Check sanction matrix", "Record release approvals"],
            follow_up_checks=["Confirm exception escalation owner", "Validate audit evidence completeness"],
        )

    def inspect_evidence(self, domain, query, context_documents, source_refs):
        return EvidenceReview(
            grounded=True,
            summary="The retrieved finance evidence now supports approval-gated release and audit traceability.",
        )

    def generate_report(self, domain, query, context_documents, source_refs, comparison=None, evidence_summary=None):
        return DomainReport(
            domain=domain,
            summary="Based on the retrieved context, validate delegated authority before release and retain audit-ready evidence.",
            insights=[DomainInsight(title="Control path grounded", severity="high", detail="Approval and audit controls are explicit.")],
            source_refs=source_refs,
        )


class MedicalToolLoopProvider(ReportLLMProvider):
    model = "gpt-5-mini"

    def is_available(self) -> bool:
        return True

    def plan_retrieval(self, domain, query, context_documents, source_refs):
        return RetrievalPlan(
            should_retrieve=True,
            search_query="chest pain red flags escalation contraindications",
            max_results=3,
            rationale="Need explicit red-flag and escalation evidence before a clinical response.",
            compare_sources=True,
            summarize_evidence=True,
        )

    def compare_sources(self, domain, query, context_documents, source_refs):
        return SourceComparison(
            summary="The medical sources align on chest pain red flags and the need for escalation if symptoms persist.",
            compared_sources=["clinical_guide.pdf", "triage_notes.txt"],
            consensus_points=["Persistent chest pain needs escalation."],
            symptoms=["chest pain", "persistent discomfort"],
            red_flags=["persistent chest pain", "worsening symptoms"],
            escalation_criteria=["ongoing chest pain despite rest", "progressive severity"],
            care_constraints=["not a substitute for clinician assessment", "medication contraindications must be reviewed"],
        )

    def summarize_evidence(self, domain, query, context_documents, source_refs):
        return EvidenceSummary(
            summary="The medical evidence supports urgent escalation for persistent chest pain and cautious review of contraindications.",
            key_points=["Persistent chest pain requires escalation.", "Contraindications should be reviewed before advice."],
            cited_sources=["clinical_guide.pdf", "triage_notes.txt"],
            symptom_summary=["Chest pain is persistent rather than transient."],
            escalation_path=["Escalate for urgent clinical assessment", "Do not rely on self-management alone"],
            patient_safety_notes=["Review contraindications before applying medication guidance"],
        )

    def inspect_evidence(self, domain, query, context_documents, source_refs):
        return EvidenceReview(
            grounded=True,
            summary="The medical evidence now supports symptom escalation and safety caveats.",
        )

    def generate_report(self, domain, query, context_documents, source_refs, comparison=None, evidence_summary=None):
        return DomainReport(
            domain=domain,
            summary="Based on the retrieved context, persistent chest pain warrants escalation and contraindications must be reviewed.",
            insights=[DomainInsight(title="Clinical escalation grounded", severity="high", detail="Red flags are present in the evidence.")],
            source_refs=source_refs,
        )


class BankingToolLoopProvider(ReportLLMProvider):
    model = "gpt-5-mini"

    def is_available(self) -> bool:
        return True

    def plan_retrieval(self, domain, query, context_documents, source_refs):
        return RetrievalPlan(
            should_retrieve=True,
            search_query="duplicate debit complaint transaction reference fraud review next steps",
            max_results=3,
            rationale="Need transaction and fraud follow-up evidence before customer guidance.",
            compare_sources=True,
            summarize_evidence=True,
        )

    def compare_sources(self, domain, query, context_documents, source_refs):
        return SourceComparison(
            summary="The banking sources align on collecting transaction references first and checking for duplicate debit or fraud indicators.",
            compared_sources=["transactions.csv", "atm_notice.txt"],
            consensus_points=["Transaction reference review is required first."],
            transaction_signals=["duplicate debit", "failed ATM cash withdrawal"],
            customer_impact_checks=["confirm debit status", "check customer cash receipt outcome"],
            fraud_indicators=["unexpected repeat debits", "unrecognized ATM usage"],
            next_actions=["capture transaction reference", "escalate suspicious activity review"],
        )

    def summarize_evidence(self, domain, query, context_documents, source_refs):
        return EvidenceSummary(
            summary="The banking evidence supports validating the transaction trail, communicating status clearly, and escalating fraud review when indicators persist.",
            key_points=["Validate transaction reference.", "Escalate suspicious repeat debits."],
            cited_sources=["transactions.csv", "atm_notice.txt"],
            service_actions=["log the complaint with transaction reference", "check ATM debit reversal window"],
            customer_message_points=["Explain review status clearly", "Advise when to expect reversal or escalation"],
            fraud_follow_ups=["review suspicious repeat debit pattern", "confirm whether card usage was authorized"],
        )

    def inspect_evidence(self, domain, query, context_documents, source_refs):
        return EvidenceReview(
            grounded=True,
            summary="The banking evidence now supports transaction validation, customer communication, and fraud follow-up.",
        )

    def generate_report(self, domain, query, context_documents, source_refs, comparison=None, evidence_summary=None):
        return DomainReport(
            domain=domain,
            summary="Based on the retrieved context, validate the transaction reference, explain the review path, and escalate fraud checks if duplicate debit indicators remain.",
            insights=[DomainInsight(title="Support path grounded", severity="high", detail="Transaction and fraud follow-up actions are present.")],
            source_refs=source_refs,
        )


class AutomotiveToolLoopProvider(ReportLLMProvider):
    model = "gpt-5-mini"

    def is_available(self) -> bool:
        return True

    def plan_retrieval(self, domain, query, context_documents, source_refs):
        return RetrievalPlan(
            should_retrieve=True,
            search_query="dtc brake subsystem inspection prerequisites safety steps",
            max_results=3,
            rationale="Need explicit diagnostic prerequisites and safety checks before repair guidance.",
            compare_sources=True,
            summarize_evidence=True,
        )

    def compare_sources(self, domain, query, context_documents, source_refs):
        return SourceComparison(
            summary="The automotive sources align on validating the DTC first, checking the brake subsystem, and completing safety inspections before repair.",
            compared_sources=["service_manual.txt", "dtc_fault_codes.csv"],
            consensus_points=["Validate the DTC before replacement."],
            fault_signals=["P0420", "brake warning"],
            subsystem_risks=["brake subsystem", "emissions control"],
            repair_prerequisites=["confirm DTC", "inspect pads and rotors"],
            safety_checks=["verify braking response", "inspect coolant and service condition before return"],
        )

    def summarize_evidence(self, domain, query, context_documents, source_refs):
        return EvidenceSummary(
            summary="The automotive evidence supports DTC validation first, targeted brake inspection next, and safety confirmation before release.",
            key_points=["Validate the DTC.", "Inspect brake hardware before replacement."],
            cited_sources=["service_manual.txt", "dtc_fault_codes.csv"],
            diagnosis_summary=["P0420 and brake warning need confirmation against diagnostic steps."],
            repair_plan=["Confirm the DTC", "Inspect brake pads and rotors", "Apply maintenance checks before closure"],
            vehicle_safety_notes=["Verify braking response before return to service"],
        )

    def inspect_evidence(self, domain, query, context_documents, source_refs):
        return EvidenceReview(
            grounded=True,
            summary="The automotive evidence now supports diagnostic validation, brake inspection, and safety checks.",
        )

    def generate_report(self, domain, query, context_documents, source_refs, comparison=None, evidence_summary=None):
        return DomainReport(
            domain=domain,
            summary="Based on the retrieved context, confirm the DTC, inspect the brake subsystem, and complete safety checks before vehicle release.",
            insights=[DomainInsight(title="Repair path grounded", severity="high", detail="Diagnostic and safety actions are explicit.")],
            source_refs=source_refs,
        )


class ManufacturingToolLoopProvider(ReportLLMProvider):
    model = "gpt-5-mini"

    def is_available(self) -> bool:
        return True

    def plan_retrieval(self, domain, query, context_documents, source_refs):
        return RetrievalPlan(
            should_retrieve=True,
            search_query="quality defect containment restart gate sop line impact corrective action",
            max_results=3,
            rationale="Need explicit containment and restart-gate evidence before production guidance.",
            compare_sources=True,
            summarize_evidence=True,
        )

    def compare_sources(self, domain, query, context_documents, source_refs):
        return SourceComparison(
            summary="The manufacturing sources align on defect containment, SOP validation, and restart approval before resuming the line.",
            compared_sources=["quality_incident.txt", "sop_guidelines.md"],
            consensus_points=["Containment must precede restart."],
            defect_signals=["quality defect", "deviation"],
            line_impact=["line restart blocked", "throughput disruption"],
            containment_actions=["isolate affected lot", "assign corrective-action owner"],
            restart_gates=["validate SOP step", "confirm quality approval before restart"],
        )

    def summarize_evidence(self, domain, query, context_documents, source_refs):
        return EvidenceSummary(
            summary="The manufacturing evidence supports immediate containment, SOP confirmation, and quality-approved restart only after corrective ownership is clear.",
            key_points=["Contain the affected material.", "Require quality approval before restart."],
            cited_sources=["quality_incident.txt", "sop_guidelines.md"],
            containment_summary=["The affected lot should be isolated and tracked."],
            production_actions=["Validate the current step against SOP", "Hold restart until corrective ownership is assigned"],
            quality_follow_ups=["Confirm root-cause ownership", "Verify restart approval evidence"],
        )

    def inspect_evidence(self, domain, query, context_documents, source_refs):
        return EvidenceReview(
            grounded=True,
            summary="The manufacturing evidence now supports containment, SOP validation, and restart gates.",
        )

    def generate_report(self, domain, query, context_documents, source_refs, comparison=None, evidence_summary=None):
        return DomainReport(
            domain=domain,
            summary="Based on the retrieved context, contain the defect, validate the SOP step, and restart only after quality approval is documented.",
            insights=[DomainInsight(title="Recovery path grounded", severity="high", detail="Containment and restart controls are explicit.")],
            source_refs=source_refs,
        )


class EcommerceToolLoopProvider(ReportLLMProvider):
    model = "gpt-5-mini"

    def is_available(self) -> bool:
        return True

    def plan_retrieval(self, domain, query, context_documents, source_refs):
        return RetrievalPlan(
            should_retrieve=True,
            search_query="refund eligibility shipment delay policy inventory resolution",
            max_results=3,
            rationale="Need policy, fulfillment, and resolution evidence before customer guidance.",
            compare_sources=True,
            summarize_evidence=True,
        )

    def compare_sources(self, domain, query, context_documents, source_refs):
        return SourceComparison(
            summary="The ecommerce sources align on delayed-shipment refund review, policy-window constraints, and stock-aware resolution handling.",
            compared_sources=["customer_issue.txt", "return_policy.md", "orders.csv"],
            consensus_points=["Refund handling depends on policy window and shipment state."],
            order_signals=["delayed shipment", "refund requested"],
            policy_constraints=["7-day exchange window", "refund review required before approval"],
            fulfillment_risks=["shipment delay", "inventory-dependent replacement path"],
            customer_resolution_actions=["validate policy eligibility", "confirm shipment status before promising resolution"],
        )

    def summarize_evidence(self, domain, query, context_documents, source_refs):
        return EvidenceSummary(
            summary="The ecommerce evidence supports validating refund eligibility against the return window, checking shipment status, and using inventory-aware resolution steps.",
            key_points=["Refund approval depends on policy eligibility.", "Shipment status must be confirmed before resolution."],
            cited_sources=["customer_issue.txt", "return_policy.md", "orders.csv"],
            refund_basis=["Return policy defines eligibility window.", "Delayed shipment alone does not bypass policy review."],
            resolution_plan=["Validate the policy window", "Confirm shipment state", "Offer exchange only if stock allows"],
            inventory_notes=["Replacement path depends on stock availability"],
        )

    def inspect_evidence(self, domain, query, context_documents, source_refs):
        return EvidenceReview(
            grounded=True,
            summary="The ecommerce evidence supports refund validation, shipment confirmation, and inventory-aware resolution.",
        )

    def generate_report(self, domain, query, context_documents, source_refs, comparison=None, evidence_summary=None):
        return DomainReport(
            domain=domain,
            summary="Based on the retrieved context, validate refund eligibility against policy, confirm shipment status, and choose a stock-aware resolution path.",
            insights=[DomainInsight(title="Resolution path grounded", severity="high", detail="Policy and fulfillment evidence are explicit.")],
            source_refs=source_refs,
        )


def test_report_evaluator_flags_missing_recommendations():
    report = DomainReport(
        domain="telecom_security",
        summary="Based on the retrieved context, there is an SS7 anomaly.",
        insights=[DomainInsight(title="Signal issue", severity="high", detail="SS7 instability observed.")],
        source_refs=[],
    )

    evaluation = evaluate_report(report)

    assert evaluation.grounded is True
    assert evaluation.has_recommendations is False
    assert "missing_recommendations" in evaluation.issues
    assert "missing_source_refs" in evaluation.issues


def test_openai_agent_runtime_metadata_reflects_fallback():
    agent = OpenAIReportAgent(provider=FailingProvider())
    documents = [
        Document(
            page_content="SS7 anomaly caused delayed OTP delivery. Isolate route.",
            metadata={"source": "test_data/telecom_incident.txt", "chunk_index": 0, "file_type": "text"},
        )
    ]

    agent.run("What should be done?", documents)
    metadata = agent.runtime_metadata()

    assert metadata["provider_mode"] == "fallback"
    assert metadata["provider_model"] == "gpt-5-mini"
    assert metadata["used_fallback"] == "true"


def test_query_pipeline_returns_evaluation_and_execution_metadata():
    pipeline = QueryPipeline()
    pipeline.agents["telecom_security"] = OpenAIReportAgent(
        provider=FailingProvider(),
        fallback_agent=TelecomSecurityAgent(),
    )
    response = pipeline.run(
        QueryRequest(
            query="What action is recommended for the SS7 issue?",
            document_path="test_data/telecom_incident.txt",
            domain="telecom_security",
            max_results=2,
        )
    )

    assert response.evaluation.grounded is True
    assert response.evaluation.has_sources is True
    assert response.execution.workflow_backend in {"fallback", "langgraph"}
    assert response.execution.agent_type == "OpenAIReportAgent"
    assert response.execution.provider_mode == "fallback"
    assert response.execution.provider_model == "gpt-5-mini"
    assert response.execution.used_fallback is True
    assert response.execution.tool_calls == 0
    assert response.execution.agent_loop == "retrieve_generate"


def test_tool_calling_agent_runtime_metadata_is_exposed_through_pipeline():
    pipeline = QueryPipeline()
    pipeline.agents["telecom_security"] = ToolCallingReportAgent(
        provider=ToolLoopProvider(),
        fallback_agent=TelecomSecurityAgent(),
    )
    response = pipeline.run(
        QueryRequest(
            query="What action is recommended for the SS7 issue?",
            document_path="test_data/telecom_incident.txt",
            domain="telecom_security",
            max_results=1,
        )
    )

    assert response.execution.agent_type == "ToolCallingReportAgent"
    assert response.execution.provider_mode == "openai"
    assert response.execution.used_fallback is False
    assert response.execution.tool_calls == 3
    assert response.execution.agent_loop == "plan_retrieve_compare_summarize_inspect_generate"
    assert response.execution.plan is not None
    assert response.execution.plan.search_query == "isolate route action"
    assert response.execution.plan.should_retrieve is True
    assert response.execution.plan.compare_sources is True
    assert response.execution.plan.summarize_evidence is True
    assert response.execution.comparison is not None
    assert response.execution.comparison.summary == "The retrieved evidence agrees on route isolation and control validation."
    assert response.execution.evidence_summary is not None
    assert response.execution.evidence_summary.cited_sources == ["test_data/telecom_incident.txt"]
    assert response.execution.inspection is not None
    assert response.execution.inspection.grounded is True
    assert response.execution.inspection.summary == "The evidence now includes both impact and action."
    assert response.execution.agent_trace.planned_query == "isolate route action"
    assert response.execution.agent_trace.plan_rationale == "Need the action-oriented chunk."
    assert response.execution.agent_trace.comparison_summary == "The retrieved evidence agrees on route isolation and control validation."
    assert response.execution.agent_trace.evidence_summary == "The evidence now includes both impact and action."
    assert response.execution.agent_trace.summary_digest == "The evidence synthesis supports isolation first, then control validation."
    assert response.execution.agent_trace.grounded is True
    assert response.execution.agent_trace.added_sources == []
    assert [step.label for step in response.execution.agent_trace.steps] == [
        "Initial Retrieval",
        "Plan",
        "Retrieve Sources",
        "Compare Sources",
        "Summarize Evidence",
        "Evidence Review",
        "Generate",
    ]
    assert "did not add any new sources" in response.execution.agent_trace.steps[2].detail
    assert response.sources


def test_query_pipeline_promotes_tool_calling_agents_for_priority_domains():
    pipeline = QueryPipeline()

    assert pipeline.agents["telecom_security"].__class__.__name__ == "LangChainCreateAgentReportAgent"
    assert pipeline.agents["financial_risk"].__class__.__name__ == "LangChainCreateAgentReportAgent"
    assert pipeline.agents["medical_qa"].__class__.__name__ == "LangChainCreateAgentReportAgent"
    assert pipeline.agents["banking_assistant"].__class__.__name__ == "LangChainCreateAgentReportAgent"
    assert pipeline.agents["ecommerce"].__class__.__name__ == "LangChainCreateAgentReportAgent"
    assert pipeline.agents["automotive"].__class__.__name__ == "LangChainCreateAgentReportAgent"
    assert pipeline.agents["manufacturing"].__class__.__name__ == "LangChainCreateAgentReportAgent"


def test_financial_risk_pipeline_exposes_domain_specific_comparison_and_summary_state(monkeypatch):
    monkeypatch.setattr(
        query_pipeline_module,
        "build_vector_db",
        lambda documents, collection_key=None: InMemoryVectorStore(documents),
    )
    pipeline = QueryPipeline()
    pipeline.agents["financial_risk"] = ToolCallingReportAgent(
        provider=FinancialRiskToolLoopProvider(),
        fallback_agent=pipeline.agents["financial_risk"].fallback_agent,
        domain_name="financial_risk",
    )

    response = pipeline.run(
        QueryRequest(
            query="What controls should be checked before funds are released?",
            document_path="test_data/telecom_incident.txt",
            domain="financial_risk",
            max_results=1,
        )
    )

    assert response.execution.plan is not None
    assert response.execution.plan.compare_sources is True
    assert response.execution.comparison is not None
    assert response.execution.comparison.control_themes == [
        "delegated_authority",
        "audit_traceability",
        "release_governance",
    ]
    assert response.execution.comparison.obligations == [
        "Validate approver authority",
        "Preserve documentary audit trail",
    ]
    assert response.execution.evidence_summary is not None
    assert response.execution.evidence_summary.decision_basis == [
        "Delegated authority clauses are explicit.",
        "Audit retention language is consistent.",
    ]
    assert response.execution.evidence_summary.recommended_controls == [
        "Check sanction matrix",
        "Record release approvals",
    ]
    assert response.execution.evidence_summary.follow_up_checks == [
        "Confirm exception escalation owner",
        "Validate audit evidence completeness",
    ]


def test_medical_pipeline_exposes_domain_specific_comparison_and_summary_state(monkeypatch):
    monkeypatch.setattr(
        query_pipeline_module,
        "build_vector_db",
        lambda documents, collection_key=None: InMemoryVectorStore(documents),
    )
    pipeline = QueryPipeline()
    pipeline.agents["medical_qa"] = ToolCallingReportAgent(
        provider=MedicalToolLoopProvider(),
        fallback_agent=pipeline.agents["medical_qa"].fallback_agent,
        domain_name="medical_qa",
    )
    medical_documents = [
        Document(
            page_content="Persistent chest pain with worsening symptoms requires escalation and contraindication review.",
            metadata={"source": "clinical_guide.pdf", "chunk_index": 0, "file_type": "pdf"},
        ),
        Document(
            page_content="Ongoing pain despite rest should not rely on self-management alone.",
            metadata={"source": "triage_notes.txt", "chunk_index": 1, "file_type": "txt"},
        ),
    ]
    pipeline.workflow.retrieval_service.retrieve = lambda vector_db, query, k: medical_documents[:k]

    response = pipeline.run(
        QueryRequest(
            query="What should be done for persistent chest pain?",
            document_path="test_data/telecom_incident.txt",
            domain="medical_qa",
            max_results=1,
        )
    )

    assert response.execution.comparison is not None
    assert response.execution.comparison.symptoms == ["chest pain", "persistent discomfort"]
    assert response.execution.comparison.red_flags == ["persistent chest pain", "worsening symptoms"]
    assert response.execution.comparison.escalation_criteria == [
        "ongoing chest pain despite rest",
        "progressive severity",
    ]
    assert response.execution.comparison.care_constraints == [
        "not a substitute for clinician assessment",
        "medication contraindications must be reviewed",
    ]
    assert response.execution.evidence_summary is not None
    assert response.execution.evidence_summary.symptom_summary == [
        "Chest pain is persistent rather than transient."
    ]
    assert response.execution.evidence_summary.escalation_path == [
        "Escalate for urgent clinical assessment",
        "Do not rely on self-management alone",
    ]
    assert response.execution.evidence_summary.patient_safety_notes == [
        "Review contraindications before applying medication guidance"
    ]


def test_banking_pipeline_exposes_domain_specific_comparison_and_summary_state(monkeypatch):
    monkeypatch.setattr(
        query_pipeline_module,
        "build_vector_db",
        lambda documents, collection_key=None: InMemoryVectorStore(documents),
    )
    pipeline = QueryPipeline()
    pipeline.agents["banking_assistant"] = ToolCallingReportAgent(
        provider=BankingToolLoopProvider(),
        fallback_agent=pipeline.agents["banking_assistant"].fallback_agent,
        domain_name="banking_assistant",
    )
    banking_documents = [
        Document(
            page_content="Duplicate debit complaints require transaction reference capture.",
            metadata={"source": "transactions.csv", "chunk_index": 0, "file_type": "csv"},
        ),
        Document(
            page_content="Failed ATM cash withdrawals require review for possible fraud or reversal handling.",
            metadata={"source": "atm_notice.txt", "chunk_index": 1, "file_type": "txt"},
        ),
    ]
    pipeline.workflow.retrieval_service.retrieve = lambda vector_db, query, k: banking_documents[:k]

    response = pipeline.run(
        QueryRequest(
            query="What should be done for a duplicate debit complaint?",
            document_path="test_data/telecom_incident.txt",
            domain="banking_assistant",
            max_results=1,
        )
    )

    assert response.execution.comparison is not None
    assert response.execution.comparison.transaction_signals == [
        "duplicate debit",
        "failed ATM cash withdrawal",
    ]
    assert response.execution.comparison.customer_impact_checks == [
        "confirm debit status",
        "check customer cash receipt outcome",
    ]
    assert response.execution.comparison.fraud_indicators == [
        "unexpected repeat debits",
        "unrecognized ATM usage",
    ]
    assert response.execution.comparison.next_actions == [
        "capture transaction reference",
        "escalate suspicious activity review",
    ]
    assert response.execution.evidence_summary is not None
    assert response.execution.evidence_summary.service_actions == [
        "log the complaint with transaction reference",
        "check ATM debit reversal window",
    ]
    assert response.execution.evidence_summary.customer_message_points == [
        "Explain review status clearly",
        "Advise when to expect reversal or escalation",
    ]
    assert response.execution.evidence_summary.fraud_follow_ups == [
        "review suspicious repeat debit pattern",
        "confirm whether card usage was authorized",
    ]


def test_automotive_pipeline_exposes_domain_specific_comparison_and_summary_state(monkeypatch):
    monkeypatch.setattr(
        query_pipeline_module,
        "build_vector_db",
        lambda documents, collection_key=None: InMemoryVectorStore(documents),
    )
    pipeline = QueryPipeline()
    pipeline.agents["automotive"] = ToolCallingReportAgent(
        provider=AutomotiveToolLoopProvider(),
        fallback_agent=pipeline.agents["automotive"].fallback_agent,
        domain_name="automotive",
    )
    automotive_documents = [
        Document(
            page_content="DTC P0420 should be confirmed before replacement and brake pads plus rotors should be inspected.",
            metadata={"source": "service_manual.txt", "chunk_index": 0, "file_type": "txt"},
        ),
        Document(
            page_content="Brake warning checks require subsystem validation and safety confirmation before return to service.",
            metadata={"source": "dtc_fault_codes.csv", "chunk_index": 1, "file_type": "csv"},
        ),
    ]
    pipeline.workflow.retrieval_service.retrieve = lambda vector_db, query, k: automotive_documents[:k]

    response = pipeline.run(
        QueryRequest(
            query="What should be checked for a brake-related warning?",
            document_path="test_data/telecom_incident.txt",
            domain="automotive",
            max_results=1,
        )
    )

    assert response.execution.comparison is not None
    assert response.execution.comparison.fault_signals == ["P0420", "brake warning"]
    assert response.execution.comparison.subsystem_risks == ["brake subsystem", "emissions control"]
    assert response.execution.comparison.repair_prerequisites == ["confirm DTC", "inspect pads and rotors"]
    assert response.execution.comparison.safety_checks == [
        "verify braking response",
        "inspect coolant and service condition before return",
    ]
    assert response.execution.evidence_summary is not None
    assert response.execution.evidence_summary.diagnosis_summary == [
        "P0420 and brake warning need confirmation against diagnostic steps."
    ]
    assert response.execution.evidence_summary.repair_plan == [
        "Confirm the DTC",
        "Inspect brake pads and rotors",
        "Apply maintenance checks before closure",
    ]
    assert response.execution.evidence_summary.vehicle_safety_notes == [
        "Verify braking response before return to service"
    ]


def test_manufacturing_pipeline_exposes_domain_specific_comparison_and_summary_state(monkeypatch):
    monkeypatch.setattr(
        query_pipeline_module,
        "build_vector_db",
        lambda documents, collection_key=None: InMemoryVectorStore(documents),
    )
    pipeline = QueryPipeline()
    pipeline.agents["manufacturing"] = ToolCallingReportAgent(
        provider=ManufacturingToolLoopProvider(),
        fallback_agent=pipeline.agents["manufacturing"].fallback_agent,
        domain_name="manufacturing",
    )
    manufacturing_documents = [
        Document(
            page_content="A quality defect requires isolating the affected lot and assigning corrective-action ownership.",
            metadata={"source": "quality_incident.txt", "chunk_index": 0, "file_type": "txt"},
        ),
        Document(
            page_content="Restart should wait until the SOP step is validated and quality approval is documented.",
            metadata={"source": "sop_guidelines.md", "chunk_index": 1, "file_type": "md"},
        ),
    ]
    pipeline.workflow.retrieval_service.retrieve = lambda vector_db, query, k: manufacturing_documents[:k]

    response = pipeline.run(
        QueryRequest(
            query="What should happen after a quality defect is reported?",
            document_path="test_data/telecom_incident.txt",
            domain="manufacturing",
            max_results=1,
        )
    )

    assert response.execution.comparison is not None
    assert response.execution.comparison.defect_signals == ["quality defect", "deviation"]
    assert response.execution.comparison.line_impact == ["line restart blocked", "throughput disruption"]
    assert response.execution.comparison.containment_actions == [
        "isolate affected lot",
        "assign corrective-action owner",
    ]
    assert response.execution.comparison.restart_gates == [
        "validate SOP step",
        "confirm quality approval before restart",
    ]
    assert response.execution.evidence_summary is not None
    assert response.execution.evidence_summary.containment_summary == [
        "The affected lot should be isolated and tracked."
    ]
    assert response.execution.evidence_summary.production_actions == [
        "Validate the current step against SOP",
        "Hold restart until corrective ownership is assigned",
    ]
    assert response.execution.evidence_summary.quality_follow_ups == [
        "Confirm root-cause ownership",
        "Verify restart approval evidence",
    ]


def test_ecommerce_pipeline_exposes_domain_specific_comparison_and_summary_state(monkeypatch):
    monkeypatch.setattr(
        query_pipeline_module,
        "build_vector_db",
        lambda documents, collection_key=None: InMemoryVectorStore(documents),
    )
    pipeline = QueryPipeline()
    pipeline.agents["ecommerce"] = ToolCallingReportAgent(
        provider=EcommerceToolLoopProvider(),
        fallback_agent=pipeline.agents["ecommerce"].fallback_agent,
        domain_name="ecommerce",
    )
    ecommerce_documents = [
        Document(
            page_content="Customer requested a refund after a delayed shipment.",
            metadata={"source": "customer_issue.txt", "chunk_index": 0, "file_type": "txt"},
        ),
        Document(
            page_content="Return policy requires review and a 7-day exchange window.",
            metadata={"source": "return_policy.md", "chunk_index": 1, "file_type": "md"},
        ),
        Document(
            page_content="Replacement depends on shipment state and stock availability.",
            metadata={"source": "orders.csv", "chunk_index": 2, "file_type": "csv"},
        ),
    ]
    pipeline.workflow.retrieval_service.retrieve = lambda vector_db, query, k: ecommerce_documents[:k]

    response = pipeline.run(
        QueryRequest(
            query="What should be done for a delayed-shipment refund request?",
            document_path="test_data/telecom_incident.txt",
            domain="ecommerce",
            max_results=1,
        )
    )

    assert response.execution.comparison is not None
    assert response.execution.comparison.order_signals == ["delayed shipment", "refund requested"]
    assert response.execution.comparison.policy_constraints == [
        "7-day exchange window",
        "refund review required before approval",
    ]
    assert response.execution.comparison.fulfillment_risks == [
        "shipment delay",
        "inventory-dependent replacement path",
    ]
    assert response.execution.comparison.customer_resolution_actions == [
        "validate policy eligibility",
        "confirm shipment status before promising resolution",
    ]
    assert response.execution.evidence_summary is not None
    assert response.execution.evidence_summary.refund_basis == [
        "Return policy defines eligibility window.",
        "Delayed shipment alone does not bypass policy review.",
    ]
    assert response.execution.evidence_summary.resolution_plan == [
        "Validate the policy window",
        "Confirm shipment state",
        "Offer exchange only if stock allows",
    ]
    assert response.execution.evidence_summary.inventory_notes == [
        "Replacement path depends on stock availability"
    ]
    assert response.evaluation.graph_state_score == 100
    assert response.evaluation.graph_state_missing_fields == []


def test_graph_state_evaluation_flags_missing_expected_fields():
    report = DomainReport(
        domain="ecommerce",
        summary="Based on the retrieved context, refund guidance is available.",
        insights=[DomainInsight(title="Policy found", severity="high", detail="Refund policy is present.")],
        recommendations=[],
        source_refs=[],
    )

    evaluation = evaluate_report(report)

    assert evaluation.graph_state_expected_fields == [
        "comparison.order_signals",
        "comparison.policy_constraints",
        "comparison.customer_resolution_actions",
        "evidence_summary.refund_basis",
        "evidence_summary.resolution_plan",
    ]
    assert evaluation.graph_state_score == 0
    assert "graph_state_incomplete" in evaluation.issues


def test_pipeline_supports_request_level_provider_selection():
    class RegistryBackedProvider(ToolLoopProvider):
        def __init__(self, provider_id: str, model: str):
            self.provider_id = provider_id
            self.model = model

    class FakeRegistry:
        def create_provider(self, provider_id="auto", model_override=None):
            return RegistryBackedProvider(provider_id=provider_id, model=model_override or "registry-default")

    pipeline = QueryPipeline()
    pipeline.provider_registry = FakeRegistry()

    response = pipeline.run(
        QueryRequest(
            query="What action is recommended for the SS7 issue?",
            document_path="test_data/telecom_incident.txt",
            domain="telecom_security",
            llm_provider="groq",
            llm_model="llama-3.3-70b-versatile",
            max_results=2,
        )
    )

    assert response.execution.provider_mode == "groq"
    assert response.execution.provider_model == "llama-3.3-70b-versatile"
    assert response.execution.vector_backend in {"memory", "langchain_embedding", "qdrant_persistent", "qdrant_server"}
    assert response.execution.llm_generated is True
    assert response.execution.used_fallback is False
    assert response.execution.requested_provider == "groq"
    assert response.execution.requested_model == "llama-3.3-70b-versatile"
