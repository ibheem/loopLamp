import os

import pytest

from backend.app.main import dashboard_report, query_documents
from backend.core.models import QueryRequest


pytest.importorskip("pypdf")


def test_financial_risk_query_endpoint_with_finance_pdf():
    response = query_documents(
        QueryRequest(
            query="Summarize financial accountability rules.",
            document_path=os.path.join("test_data", "finance", "FInal_GFR_upto_31_07_2024.pdf"),
            domain="financial_risk",
            max_results=2,
        )
    )

    assert response.domain == "financial_risk"
    assert response.report.domain == "financial_risk"
    assert response.report.metrics
    assert response.sources


def test_financial_risk_dashboard_endpoint_with_finance_pdf():
    response = dashboard_report(
        QueryRequest(
            query="What procurement risk guidance is mentioned?",
            document_path=os.path.join("test_data", "finance", "FInal_GFR_upto_31_07_2024.pdf"),
            domain="financial_risk",
            max_results=2,
        )
    )

    assert response.domain == "financial_risk"
    assert response.title == "Financial Risk Dashboard Report"
    assert response.source_count > 0
