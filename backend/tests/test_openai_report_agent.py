from backend.agents.openai_report_agent import OpenAIReportAgent
from backend.agents.telecom_security import TelecomSecurityAgent
from backend.agents.tool_calling_report_agent import ToolCallingReportAgent
from backend.core.documents import Document
from backend.core.models import DomainInsight, DomainMetric, DomainRecommendation, DomainReport, DomainSourceRef
from backend.services.llm_provider import EvidenceReview, ProviderUnavailableError, ReportLLMProvider, RetrievalPlan


class FakeSuccessProvider(ReportLLMProvider):
    def is_available(self) -> bool:
        return True

    def generate_report(self, domain, query, context_documents, source_refs):
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

    def generate_report(self, domain, query, context_documents, source_refs):
        raise ProviderUnavailableError("missing key")


class FakeToolProvider(FakeSuccessProvider):
    model = "gpt-5-mini"

    def plan_retrieval(self, domain, query, context_documents, source_refs):
        return RetrievalPlan(
            should_retrieve=True,
            search_query="isolate affected route action",
            max_results=2,
            rationale="Need a more action-specific chunk before final synthesis.",
        )

    def inspect_evidence(self, domain, query, context_documents, source_refs):
        return EvidenceReview(
            grounded=True,
            summary="The combined evidence now includes both the anomaly and the recommended action.",
        )


def test_openai_report_agent_returns_structured_report_from_provider():
    agent = OpenAIReportAgent(provider=FakeSuccessProvider())
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
    assert metadata["tool_calls"] == 1
    assert metadata["agent_loop"] == "plan_retrieve_inspect_generate"
