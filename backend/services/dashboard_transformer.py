from backend.core.models import (
    DashboardAction,
    DashboardHighlight,
    DashboardMetric,
    DashboardResponse,
    DashboardStatus,
    QueryResponse,
)


def build_dashboard_response(query_response: QueryResponse) -> DashboardResponse:
    issues = list(query_response.evaluation.issues)
    if not query_response.evaluation.grounded:
        level = "warning"
    elif query_response.execution.used_fallback:
        level = "info"
    else:
        level = "success"

    return DashboardResponse(
        domain=query_response.domain,
        title=f"{query_response.domain.replace('_', ' ').title()} Dashboard Report",
        summary=query_response.report.summary,
        status=DashboardStatus(level=level, issues=issues),
        metrics=[
            DashboardMetric(label=metric.name.replace("_", " ").title(), value=metric.value, unit=metric.unit)
            for metric in query_response.report.metrics
        ],
        highlights=[
            DashboardHighlight(
                title=insight.title,
                severity=insight.severity,
                detail=insight.detail,
            )
            for insight in query_response.report.insights
        ],
        actions=[
            DashboardAction(priority=recommendation.priority, action=recommendation.action)
            for recommendation in query_response.report.recommendations
        ],
        source_count=len(query_response.sources),
        execution=query_response.execution,
        evaluation=query_response.evaluation,
    )
