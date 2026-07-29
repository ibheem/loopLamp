from backend.core.models import (
    DashboardResponse,
    DomainInsight,
    DomainMetric,
    DomainRecommendation,
    DomainReport,
    ExecutionMetadata,
    QueryResponse,
    ReportEvaluation,
    SourceDocument,
)
from backend.services.dashboard_transformer import build_dashboard_response


def test_build_dashboard_response_maps_report_to_ui_shape():
    query_response = QueryResponse(
        answer="Based on the retrieved context, isolate the route.",
        domain="telecom_security",
        attempts=1,
        used_reflection=False,
        report=DomainReport(
            domain="telecom_security",
            summary="Based on the retrieved context, isolate the route.",
            metrics=[DomainMetric(name="matched_documents", value="2", unit="documents")],
            insights=[DomainInsight(title="SS7 anomaly", severity="high", detail="Routing instability detected.")],
            recommendations=[DomainRecommendation(priority=1, action="Isolate partner route.")],
        ),
        evaluation=ReportEvaluation(
            grounded=True,
            has_sources=True,
            has_recommendations=True,
            issues=[],
        ),
        execution=ExecutionMetadata(
            workflow_backend="fallback",
            agent_type="OpenAIReportAgent",
            provider_mode="fallback",
            provider_model="gpt-5-mini",
            used_fallback=True,
        ),
        sources=[SourceDocument(content="Route issue details", metadata={"source": "a.txt"})],
    )

    dashboard = build_dashboard_response(query_response)

    assert isinstance(dashboard, DashboardResponse)
    assert dashboard.title == "Telecom Security Dashboard Report"
    assert dashboard.status.level == "info"
    assert dashboard.metrics[0].label == "Matched Documents"
    assert dashboard.highlights[0].severity == "high"
    assert dashboard.actions[0].priority == 1
    assert dashboard.source_count == 1
