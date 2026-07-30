from backend.core.models import (
    DomainReport,
    ExecutionMetadata,
    QueryResponse,
    ReportEvaluation,
    SourceDocument,
)
from backend.services.dashboard_transformer import build_dashboard_response


def _make_query_response(domain: str, contents: list[str]) -> QueryResponse:
    return QueryResponse(
        answer="retrieved context",
        domain=domain,
        attempts=1,
        used_reflection=False,
        report=DomainReport(domain=domain, summary="retrieved context"),
        evaluation=ReportEvaluation(
            grounded=True,
            has_sources=True,
            has_recommendations=True,
            issues=[],
        ),
        execution=ExecutionMetadata(
            workflow_backend="query_pipeline",
            agent_type=domain,
            provider_mode="fallback",
            provider_model="",
            used_fallback=True,
        ),
        sources=[
            SourceDocument(
                content=content,
                metadata={
                    "source": f"test_data/{domain}/{index}.txt",
                    "source_id": f"sample:{domain}:{index}.txt",
                    "source_domain": domain,
                    "source_origin": "sample",
                    "file_type": "text",
                },
            )
            for index, content in enumerate(contents, start=1)
        ],
    )


def test_build_dashboard_response_adds_financial_risk_domain_cards():
    response = _make_query_response(
        "financial_risk",
        [
            "approval authority audit compliance controls are required before release",
            "kyc review and audit trail must be retained",
        ],
    )

    dashboard = build_dashboard_response(response)

    assert dashboard.domain_cards
    assert any(card.title == "Control Families" for card in dashboard.domain_cards)
    assert any(card.title == "Primary Theme" for card in dashboard.domain_cards)


def test_build_dashboard_response_adds_ecommerce_domain_cards():
    response = _make_query_response(
        "ecommerce",
        [
            "delayed shipment refund requested after 5 days",
            "refund review is required and 7 days exchange policy applies",
        ],
    )

    dashboard = build_dashboard_response(response)

    assert dashboard.domain_cards
    assert any(card.title == "Refund Pressure" for card in dashboard.domain_cards)
    assert any(card.title == "Fulfillment Risk" for card in dashboard.domain_cards)


def test_build_dashboard_response_adds_manufacturing_domain_cards():
    response = _make_query_response(
        "manufacturing",
        [
            "downtime reported because of seal defect",
            "restart requires containment and supervisor approval",
        ],
    )

    dashboard = build_dashboard_response(response)

    assert dashboard.domain_cards
    assert any(card.title == "Production Interruptions" for card in dashboard.domain_cards)
    assert any(card.title == "Quality Containment" for card in dashboard.domain_cards)
