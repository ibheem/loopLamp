from backend.core.models import (
    DashboardAction,
    DashboardEvidenceCard,
    DashboardHighlight,
    DashboardMetric,
    DashboardMatchedSource,
    DashboardResponse,
    DashboardStatus,
    QueryResponse,
)


def _compact_preview(text: str, limit: int = 120) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= limit:
        return cleaned
    return f"{cleaned[: limit - 3]}..."


def _build_matched_sources(query_response: QueryResponse):
    grouped = {}
    for source in query_response.sources:
        metadata = source.metadata or {}
        key = metadata.get("source_id") or metadata.get("source") or "unknown"
        record = grouped.setdefault(
            key,
            {
                "source": str(metadata.get("source", "unknown")),
                "source_id": str(metadata.get("source_id", "")),
                "domain": str(metadata.get("source_domain", query_response.domain)),
                "origin": str(metadata.get("source_origin", "")),
                "evidence_count": 0,
                "file_type": str(metadata.get("file_type", "")),
                "preview": "",
            },
        )
        record["evidence_count"] += 1
        if not record["preview"]:
            record["preview"] = _compact_preview(source.content)

    return [
        DashboardMatchedSource(**payload)
        for payload in sorted(grouped.values(), key=lambda item: (-item["evidence_count"], item["source"]))
    ]


def _build_evidence_cards(query_response: QueryResponse):
    cards = []
    for source in query_response.sources[:3]:
        metadata = source.metadata or {}
        cards.append(
            DashboardEvidenceCard(
                title=f"Evidence from {metadata.get('file_type', 'source')}".replace("_", " ").title(),
                detail=_compact_preview(source.content, limit=180),
                source=str(metadata.get("source", "unknown")),
                source_id=str(metadata.get("source_id", "")),
                evidence_count=1,
                severity="high" if any(term in source.content.lower() for term in ("critical", "high", "severe", "ss7")) else "info",
            )
        )
    return cards


def build_dashboard_response(query_response: QueryResponse) -> DashboardResponse:
    issues = list(query_response.evaluation.issues)
    if not query_response.evaluation.grounded:
        level = "warning"
    elif query_response.execution.used_fallback:
        level = "info"
    else:
        level = "success"

    matched_sources = _build_matched_sources(query_response)
    evidence_cards = _build_evidence_cards(query_response)

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
        matched_sources=matched_sources,
        evidence_cards=evidence_cards,
        source_count=len(query_response.sources),
        execution=query_response.execution,
        evaluation=query_response.evaluation,
    )
