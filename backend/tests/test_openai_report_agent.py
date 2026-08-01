from backend.agents.openai_report_agent import OpenAIReportAgent
from backend.agents.telecom_security import TelecomSecurityAgent
from backend.agents.tool_calling_report_agent import ToolCallingReportAgent
from backend.core.documents import Document
from backend.core.models import DomainInsight, DomainMetric, DomainRecommendation, DomainReport, DomainSourceRef
from backend.services.llm_provider import (
    EvidenceReview,
    EvidenceSummary,
    OpenAIResponsesReportProvider,
    ProviderUnavailableError,
    ReportLLMProvider,
    RetrievalPlan,
    SourceComparison,
)


class FakeSuccessProvider(ReportLLMProvider):
    def __init__(self):
        self.last_comparison = None
        self.last_evidence_summary = None

    def is_available(self) -> bool:
        return True

    def generate_report(self, domain, query, context_documents, source_refs, comparison=None, evidence_summary=None):
        self.last_comparison = comparison
        self.last_evidence_summary = evidence_summary
        return DomainReport(
            domain=domain,
            summary="Based on the retrieved context, isolate the SS7 route.",
            metrics=[DomainMetric(name="incident_count", value="1", unit="incident")],
            insights=[
                DomainInsight(
                    title="SS7 route instability",
                    severity="high",
                    detail="Retrieved context confirms a signaling route issue.",
                )
            ],
            recommendations=[
                DomainRecommendation(priority=1, action="Isolate the affected partner route.")
            ],
            source_refs=source_refs,
        )


class FakeUnavailableProvider(ReportLLMProvider):
    def is_available(self) -> bool:
        return False

    def generate_report(self, domain, query, context_documents, source_refs, comparison=None, evidence_summary=None):
        raise ProviderUnavailableError("missing key")


class FakeToolProvider(FakeSuccessProvider):
    model = "gpt-5-mini"

    def plan_retrieval(self, domain, query, context_documents, source_refs):
        return RetrievalPlan(
            should_retrieve=True,
            search_query="isolate affected route action",
            max_results=2,
            rationale="Need a more action-specific chunk before final synthesis.",
            compare_sources=True,
            summarize_evidence=True,
        )

    def compare_sources(self, domain, query, context_documents, source_refs):
        return SourceComparison(
            summary="The incident evidence and playbook both support route isolation first.",
            compared_sources=["telecom_incident.txt", "telecom_playbook.txt"],
            consensus_points=["Isolate the affected route."],
        )

    def summarize_evidence(self, domain, query, context_documents, source_refs):
        return EvidenceSummary(
            summary="The strongest grounded path is isolate first, then review signaling firewall controls.",
            key_points=["Isolate the route.", "Review signaling firewall controls."],
            cited_sources=["telecom_playbook.txt"],
        )

    def inspect_evidence(self, domain, query, context_documents, source_refs):
        return EvidenceReview(
            grounded=True,
            summary="The combined evidence now includes both the anomaly and the recommended action.",
        )


def test_openai_report_agent_returns_structured_report_from_provider():
    provider = FakeSuccessProvider()
    agent = OpenAIReportAgent(provider=provider)
    documents = [
        Document(
            page_content="SS7 anomaly triggered OTP delays. Isolate the affected partner route.",
            metadata={"source": "test_data/telecom_incident.txt", "chunk_index": 0, "file_type": "text"},
        )
    ]

    report = agent.run("What should be done for the SS7 issue?", documents)

    assert report.domain == "telecom_security"
    assert "retrieved context" in report.summary.lower()
    assert report.metrics
    assert report.recommendations
    assert report.source_refs[0].source.endswith("telecom_incident.txt")
    assert provider.last_comparison is None
    assert provider.last_evidence_summary is None


def test_openai_report_agent_passes_graph_artifacts_into_provider():
    provider = FakeSuccessProvider()
    agent = OpenAIReportAgent(provider=provider)
    documents = [
        Document(
            page_content="SS7 anomaly triggered OTP delays. Isolate the affected partner route.",
            metadata={"source": "test_data/telecom_incident.txt", "chunk_index": 0, "file_type": "text"},
        )
    ]

    report = agent.generate_report_from_state(
        "What should be done for the SS7 issue?",
        documents,
        comparison=SourceComparison(
            summary="Both sources agree that route isolation is first.",
            compared_sources=["telecom_incident.txt", "telecom_playbook.txt"],
        ),
        evidence_summary=EvidenceSummary(
            summary="The evidence synthesis favors route isolation followed by control validation.",
            key_points=["Isolate the route."],
            cited_sources=["telecom_playbook.txt"],
        ),
    )

    assert report.domain == "telecom_security"
    assert provider.last_comparison is not None
    assert provider.last_comparison.summary == "Both sources agree that route isolation is first."
    assert provider.last_evidence_summary is not None
    assert provider.last_evidence_summary.cited_sources == ["telecom_playbook.txt"]


def test_openai_report_agent_falls_back_when_provider_unavailable():
    fallback_agent = TelecomSecurityAgent()
    agent = OpenAIReportAgent(provider=FakeUnavailableProvider(), fallback_agent=fallback_agent)
    documents = [
        Document(
            page_content="SS7 anomaly caused delayed OTP delivery. Isolate the affected route.",
            metadata={"source": "test_data/telecom_incident.txt", "chunk_index": 0, "file_type": "text"},
        )
    ]

    report = agent.run("What should be done for the SS7 issue?", documents)

    assert report.domain == "telecom_security"
    assert any(metric.name == "matched_documents" for metric in report.metrics)
    assert any(ref.source.endswith("telecom_incident.txt") for ref in report.source_refs)


def test_tool_calling_report_agent_uses_retrieval_tool_before_generation():
    agent = ToolCallingReportAgent(provider=FakeToolProvider())
    initial_documents = [
        Document(
            page_content="SS7 anomaly triggered OTP delays on the roaming edge.",
            metadata={"source": "test_data/telecom_incident.txt", "chunk_index": 0, "file_type": "text"},
        )
    ]
    extra_documents = [
        Document(
            page_content="Isolate the affected partner route and review signaling firewall controls.",
            metadata={"source": "test_data/telecom_playbook.txt", "chunk_index": 1, "file_type": "text"},
        )
    ]

    report, used_documents = agent.run_with_tools(
        "What should be done for the SS7 issue?",
        initial_documents,
        retrieve_tool=lambda tool_query, k: extra_documents,
    )
    metadata = agent.runtime_metadata()

    assert report.domain == "telecom_security"
    assert len(used_documents) == 2
    assert any(ref.source.endswith("telecom_playbook.txt") for ref in report.source_refs)
    assert metadata["provider_mode"] == "openai"
    assert metadata["tool_calls"] == 3
    assert metadata["agent_loop"] == "plan_retrieve_compare_summarize_inspect_generate"
    assert agent.provider.last_comparison is not None
    assert agent.provider.last_evidence_summary is not None


def test_financial_risk_prompt_guidance_mentions_control_specific_fields():
    provider = OpenAIResponsesReportProvider(api_key=None)
    documents = [
        Document(
            page_content="Release requires sanctioning authority and audit trail retention.",
            metadata={"source": "finance_policy.pdf", "chunk_index": 0, "file_type": "pdf"},
        )
    ]
    source_refs = [DomainSourceRef(source="finance_policy.pdf", chunk_index=0, file_type="pdf")]

    comparison_prompt = provider._build_comparison_prompt(
        domain="financial_risk",
        query="What should be checked before release?",
        context_documents=documents,
        source_refs=source_refs,
    )
    summary_prompt = provider._build_evidence_summary_prompt(
        domain="financial_risk",
        query="What should be checked before release?",
        context_documents=documents,
        source_refs=source_refs,
    )

    assert "control_themes" in comparison_prompt
    assert "obligations" in comparison_prompt
    assert "decision_basis" in summary_prompt
    assert "recommended_controls" in summary_prompt
    assert "follow_up_checks" in summary_prompt


def test_medical_prompt_guidance_mentions_clinical_specific_fields():
    provider = OpenAIResponsesReportProvider(api_key=None)
    documents = [
        Document(
            page_content="Persistent chest pain with worsening symptoms requires escalation and contraindication review.",
            metadata={"source": "clinical_guide.pdf", "chunk_index": 0, "file_type": "pdf"},
        )
    ]
    source_refs = [DomainSourceRef(source="clinical_guide.pdf", chunk_index=0, file_type="pdf")]

    comparison_prompt = provider._build_comparison_prompt(
        domain="medical_qa",
        query="What should be done for persistent chest pain?",
        context_documents=documents,
        source_refs=source_refs,
    )
    summary_prompt = provider._build_evidence_summary_prompt(
        domain="medical_qa",
        query="What should be done for persistent chest pain?",
        context_documents=documents,
        source_refs=source_refs,
    )

    assert "symptoms" in comparison_prompt
    assert "red_flags" in comparison_prompt
    assert "escalation_criteria" in comparison_prompt
    assert "care_constraints" in comparison_prompt
    assert "symptom_summary" in summary_prompt
    assert "escalation_path" in summary_prompt
    assert "patient_safety_notes" in summary_prompt


def test_banking_prompt_guidance_mentions_support_specific_fields():
    provider = OpenAIResponsesReportProvider(api_key=None)
    documents = [
        Document(
            page_content="Duplicate debit complaints require transaction reference validation and fraud review if usage is unrecognized.",
            metadata={"source": "atm_notice.txt", "chunk_index": 0, "file_type": "txt"},
        )
    ]
    source_refs = [DomainSourceRef(source="atm_notice.txt", chunk_index=0, file_type="txt")]

    comparison_prompt = provider._build_comparison_prompt(
        domain="banking_assistant",
        query="What should be done for a duplicate debit complaint?",
        context_documents=documents,
        source_refs=source_refs,
    )
    summary_prompt = provider._build_evidence_summary_prompt(
        domain="banking_assistant",
        query="What should be done for a duplicate debit complaint?",
        context_documents=documents,
        source_refs=source_refs,
    )

    assert "transaction_signals" in comparison_prompt
    assert "customer_impact_checks" in comparison_prompt
    assert "fraud_indicators" in comparison_prompt
    assert "next_actions" in comparison_prompt
    assert "service_actions" in summary_prompt
    assert "customer_message_points" in summary_prompt
    assert "fraud_follow_ups" in summary_prompt


def test_automotive_prompt_guidance_mentions_repair_specific_fields():
    provider = OpenAIResponsesReportProvider(api_key=None)
    documents = [
        Document(
            page_content="DTC P0420 and a brake warning require diagnostic confirmation and safety checks before release.",
            metadata={"source": "service_manual.txt", "chunk_index": 0, "file_type": "txt"},
        )
    ]
    source_refs = [DomainSourceRef(source="service_manual.txt", chunk_index=0, file_type="txt")]

    comparison_prompt = provider._build_comparison_prompt(
        domain="automotive",
        query="What should be checked for a brake-related warning?",
        context_documents=documents,
        source_refs=source_refs,
    )
    summary_prompt = provider._build_evidence_summary_prompt(
        domain="automotive",
        query="What should be checked for a brake-related warning?",
        context_documents=documents,
        source_refs=source_refs,
    )

    assert "fault_signals" in comparison_prompt
    assert "subsystem_risks" in comparison_prompt
    assert "repair_prerequisites" in comparison_prompt
    assert "safety_checks" in comparison_prompt
    assert "diagnosis_summary" in summary_prompt
    assert "repair_plan" in summary_prompt
    assert "vehicle_safety_notes" in summary_prompt


def test_manufacturing_prompt_guidance_mentions_containment_specific_fields():
    provider = OpenAIResponsesReportProvider(api_key=None)
    documents = [
        Document(
            page_content="Quality defect containment and SOP validation are required before line restart.",
            metadata={"source": "quality_incident.txt", "chunk_index": 0, "file_type": "txt"},
        )
    ]
    source_refs = [DomainSourceRef(source="quality_incident.txt", chunk_index=0, file_type="txt")]

    comparison_prompt = provider._build_comparison_prompt(
        domain="manufacturing",
        query="What should happen after a quality defect is reported?",
        context_documents=documents,
        source_refs=source_refs,
    )
    summary_prompt = provider._build_evidence_summary_prompt(
        domain="manufacturing",
        query="What should happen after a quality defect is reported?",
        context_documents=documents,
        source_refs=source_refs,
    )

    assert "defect_signals" in comparison_prompt
    assert "line_impact" in comparison_prompt
    assert "containment_actions" in comparison_prompt
    assert "restart_gates" in comparison_prompt
    assert "containment_summary" in summary_prompt
    assert "production_actions" in summary_prompt
    assert "quality_follow_ups" in summary_prompt


def test_ecommerce_prompt_guidance_mentions_resolution_specific_fields():
    provider = OpenAIResponsesReportProvider(api_key=None)
    documents = [
        Document(
            page_content="Delayed shipment refund requests depend on return-window policy and stock-aware exchange handling.",
            metadata={"source": "return_policy.md", "chunk_index": 0, "file_type": "md"},
        )
    ]
    source_refs = [DomainSourceRef(source="return_policy.md", chunk_index=0, file_type="md")]

    comparison_prompt = provider._build_comparison_prompt(
        domain="ecommerce",
        query="What should be done for a delayed-shipment refund request?",
        context_documents=documents,
        source_refs=source_refs,
    )
    summary_prompt = provider._build_evidence_summary_prompt(
        domain="ecommerce",
        query="What should be done for a delayed-shipment refund request?",
        context_documents=documents,
        source_refs=source_refs,
    )

    assert "order_signals" in comparison_prompt
    assert "policy_constraints" in comparison_prompt
    assert "fulfillment_risks" in comparison_prompt
    assert "customer_resolution_actions" in comparison_prompt
    assert "refund_basis" in summary_prompt
    assert "resolution_plan" in summary_prompt
    assert "inventory_notes" in summary_prompt
