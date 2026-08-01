from typing import List, Optional

from backend.core.models import DomainReport, ExecutionMetadata, ReportEvaluation


GRAPH_STATE_EXPECTATIONS = {
    "financial_risk": [
        ("comparison", "control_themes"),
        ("comparison", "obligations"),
        ("evidence_summary", "decision_basis"),
        ("evidence_summary", "recommended_controls"),
    ],
    "medical_qa": [
        ("comparison", "symptoms"),
        ("comparison", "red_flags"),
        ("comparison", "escalation_criteria"),
        ("evidence_summary", "symptom_summary"),
        ("evidence_summary", "escalation_path"),
    ],
    "banking_assistant": [
        ("comparison", "transaction_signals"),
        ("comparison", "fraud_indicators"),
        ("comparison", "next_actions"),
        ("evidence_summary", "service_actions"),
        ("evidence_summary", "fraud_follow_ups"),
    ],
    "automotive": [
        ("comparison", "fault_signals"),
        ("comparison", "repair_prerequisites"),
        ("comparison", "safety_checks"),
        ("evidence_summary", "repair_plan"),
        ("evidence_summary", "vehicle_safety_notes"),
    ],
    "manufacturing": [
        ("comparison", "defect_signals"),
        ("comparison", "containment_actions"),
        ("comparison", "restart_gates"),
        ("evidence_summary", "production_actions"),
        ("evidence_summary", "quality_follow_ups"),
    ],
    "ecommerce": [
        ("comparison", "order_signals"),
        ("comparison", "policy_constraints"),
        ("comparison", "customer_resolution_actions"),
        ("evidence_summary", "refund_basis"),
        ("evidence_summary", "resolution_plan"),
    ],
}


def evaluate_report(
    report: DomainReport,
    execution: Optional[ExecutionMetadata] = None,
) -> ReportEvaluation:
    issues: List[str] = []
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

    expected_fields, present_fields, missing_fields = _evaluate_graph_state(
        domain=report.domain,
        execution=execution,
    )
    if missing_fields:
        issues.append("graph_state_incomplete")

    score = 0
    if expected_fields:
        score = int(round((len(present_fields) / len(expected_fields)) * 100))

    return ReportEvaluation(
        grounded=grounded,
        has_sources=has_sources,
        has_recommendations=has_recommendations,
        issues=issues,
        graph_state_score=score,
        graph_state_expected_fields=expected_fields,
        graph_state_present_fields=present_fields,
        graph_state_missing_fields=missing_fields,
    )


def _evaluate_graph_state(
    domain: str,
    execution: Optional[ExecutionMetadata],
) -> tuple[List[str], List[str], List[str]]:
    requirements = GRAPH_STATE_EXPECTATIONS.get(domain, [])
    expected_fields = [f"{section}.{field}" for section, field in requirements]
    if not requirements or execution is None:
        return expected_fields, [], expected_fields

    present_fields: List[str] = []
    missing_fields: List[str] = []
    for section_name, field_name in requirements:
        section = getattr(execution, section_name, None)
        value = getattr(section, field_name, None) if section is not None else None
        qualified_name = f"{section_name}.{field_name}"
        if _has_meaningful_value(value):
            present_fields.append(qualified_name)
        else:
            missing_fields.append(qualified_name)

    return expected_fields, present_fields, missing_fields


def _has_meaningful_value(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return len(value) > 0
    return True
