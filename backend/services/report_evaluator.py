from backend.core.models import DomainReport, ReportEvaluation


def evaluate_report(report: DomainReport) -> ReportEvaluation:
    issues = []
    grounded = "retrieved context" in report.summary.lower()
    has_sources = bool(report.source_refs)
    has_recommendations = bool(report.recommendations)

    if not grounded:
        issues.append("summary_not_explicitly_grounded")
    if not has_sources:
        issues.append("missing_source_refs")
    if not has_recommendations:
        issues.append("missing_recommendations")
    if not report.insights:
        issues.append("missing_insights")

    return ReportEvaluation(
        grounded=grounded,
        has_sources=has_sources,
        has_recommendations=has_recommendations,
        issues=issues,
    )
