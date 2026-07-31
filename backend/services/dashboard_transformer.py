from backend.core.models import (
    DashboardAction,
    DashboardDomainCard,
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


def _build_financial_risk_cards(query_response: QueryResponse):
    combined = " ".join(source.content.lower() for source in query_response.sources)
    control_hits = sum(keyword in combined for keyword in ("approval", "audit", "authority", "compliance", "kyc"))
    top_theme = "approval control" if "approval" in combined else "audit traceability" if "audit" in combined else "regulatory control"
    severity = "high" if "kyc" in combined or "compliance" in combined else "info"
    return [
        DashboardDomainCard(
            title="Control Families",
            value=str(control_hits or 1),
            detail="Counts the main governance or compliance control themes visible in the retrieved finance evidence.",
            severity=severity,
        ),
        DashboardDomainCard(
            title="Primary Theme",
            value=top_theme,
            detail="Highlights the strongest finance governance pattern referenced by the retrieved sources.",
            severity="info",
        ),
    ]


def _build_ecommerce_cards(query_response: QueryResponse):
    combined = " ".join(source.content.lower() for source in query_response.sources)
    delayed = combined.count("delayed")
    refund = combined.count("refund")
    review = combined.count("review")
    policy_window = "7 days" if "7 days" in combined else "policy-driven"
    return [
        DashboardDomainCard(
            title="Refund Pressure",
            value=str(refund or 0),
            detail="Shows how often refund-related evidence appears across ecommerce sources.",
            severity="high" if refund else "info",
        ),
        DashboardDomainCard(
            title="Fulfillment Risk",
            value=str(delayed or review or 0),
            detail=f"Tracks delayed shipment and review signals, with refund window guidance around {policy_window}.",
            severity="warning" if delayed or review else "info",
        ),
    ]


def _build_manufacturing_cards(query_response: QueryResponse):
    combined = " ".join(source.content.lower() for source in query_response.sources)
    downtime = combined.count("downtime")
    defect = combined.count("defect")
    restart = combined.count("restart")
    containment_required = "yes" if "containment" in combined or "approval" in combined else "no"
    return [
        DashboardDomainCard(
            title="Production Interruptions",
            value=str(downtime + restart),
            detail="Summarizes downtime and restart evidence observed in the manufacturing corpus.",
            severity="warning" if downtime else "info",
        ),
        DashboardDomainCard(
            title="Quality Containment",
            value=containment_required,
            detail=f"Detected {defect or 0} defect-related references and whether containment/approval is explicitly required before restart.",
            severity="high" if containment_required == "yes" else "info",
        ),
    ]


def _build_domain_cards(query_response: QueryResponse):
    if query_response.domain == "financial_risk":
        return _build_financial_risk_cards(query_response)
    if query_response.domain == "ecommerce":
        return _build_ecommerce_cards(query_response)
    if query_response.domain == "manufacturing":
        return _build_manufacturing_cards(query_response)
    return [
        DashboardDomainCard(
            title="Matched Sources",
            value=str(len({(source.metadata or {}).get('source_id') or (source.metadata or {}).get('source') for source in query_response.sources})),
            detail="Counts the distinct sources that contributed evidence to this dashboard response.",
            severity="info",
        )
    ] if query_response.sources else []


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
    domain_cards = _build_domain_cards(query_response)

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
        domain_cards=domain_cards,
        source_count=len(query_response.sources),
        execution=query_response.execution,
        evaluation=query_response.evaluation,
    )
