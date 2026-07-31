from backend.agents.openai_report_agent import OpenAIReportAgent
from backend.agents.telecom_security import TelecomSecurityAgent
from backend.agents.tool_calling_report_agent import ToolCallingReportAgent
from backend.core.documents import Document
from backend.core.models import DomainInsight, DomainReport, QueryRequest
from backend.services.llm_provider import EvidenceReview, ProviderUnavailableError, ReportLLMProvider, RetrievalPlan
from backend.services.report_evaluator import evaluate_report
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
        )

    def inspect_evidence(self, domain, query, context_documents, source_refs):
        return EvidenceReview(
            grounded=True,
            summary="The evidence now includes both impact and action.",
        )

    def generate_report(self, domain, query, context_documents, source_refs):
        return DomainReport(
            domain=domain,
            summary="Based on the retrieved context, isolate the route and validate controls.",
            insights=[DomainInsight(title="Action grounded", severity="high", detail="Action guidance is present.")],
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
    assert response.execution.tool_calls == 1
    assert response.execution.agent_loop == "plan_retrieve_inspect_generate"
    assert response.execution.plan is not None
    assert response.execution.plan.search_query == "isolate route action"
    assert response.execution.plan.should_retrieve is True
    assert response.execution.inspection is not None
    assert response.execution.inspection.grounded is True
    assert response.execution.inspection.summary == "The evidence now includes both impact and action."
    assert response.execution.agent_trace.planned_query == "isolate route action"
    assert response.execution.agent_trace.plan_rationale == "Need the action-oriented chunk."
    assert response.execution.agent_trace.evidence_summary == "The evidence now includes both impact and action."
    assert response.execution.agent_trace.grounded is True
    assert response.execution.agent_trace.added_sources == []
    assert [step.label for step in response.execution.agent_trace.steps] == [
        "Initial Retrieval",
        "Plan",
        "Tool Call",
        "Evidence Review",
        "Generate",
    ]
    assert "did not add any new sources" in response.execution.agent_trace.steps[2].detail
    assert response.sources


def test_query_pipeline_promotes_tool_calling_agents_for_priority_domains():
    pipeline = QueryPipeline()

    assert pipeline.agents["telecom_security"].__class__.__name__ == "ToolCallingReportAgent"
    assert pipeline.agents["financial_risk"].__class__.__name__ == "ToolCallingReportAgent"
    assert pipeline.agents["medical_qa"].__class__.__name__ == "ToolCallingReportAgent"
    assert pipeline.agents["banking_assistant"].__class__.__name__ == "ToolCallingReportAgent"
    assert pipeline.agents["automotive"].__class__.__name__ == "ToolCallingReportAgent"
    assert pipeline.agents["manufacturing"].__class__.__name__ == "ToolCallingReportAgent"
    assert pipeline.agents["ecommerce"].__class__.__name__ == "ToolCallingReportAgent"
