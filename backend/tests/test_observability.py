from backend.agents.openai_report_agent import OpenAIReportAgent
from backend.agents.telecom_security import TelecomSecurityAgent
from backend.core.documents import Document
from backend.core.models import DomainInsight, DomainReport, QueryRequest
from backend.services.llm_provider import ProviderUnavailableError, ReportLLMProvider
from backend.services.report_evaluator import evaluate_report
from backend.workflows.query_pipeline import QueryPipeline


class FailingProvider(ReportLLMProvider):
    model = "gpt-5-mini"

    def is_available(self) -> bool:
        return False

    def generate_report(self, domain, query, context_documents, source_refs):
        raise ProviderUnavailableError("missing credentials")


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
