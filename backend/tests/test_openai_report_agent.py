from backend.agents.openai_report_agent import OpenAIReportAgent
from backend.agents.telecom_security import TelecomSecurityAgent
from backend.core.documents import Document
from backend.core.models import DomainInsight, DomainMetric, DomainRecommendation, DomainReport, DomainSourceRef
from backend.services.llm_provider import ProviderUnavailableError, ReportLLMProvider


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
