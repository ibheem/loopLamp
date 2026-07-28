import os

from backend.app.main import dashboard_report, query_documents
from backend.core.models import QueryRequest


def test_automotive_query_endpoint_with_text_source():
    response = query_documents(
        QueryRequest(
            query="What should be checked when a brake warning is reported?",
            document_path=os.path.join("test_data", "automotive", "service_manual.txt"),
            domain="automotive",
            max_results=2,
        )
    )

    assert response.domain == "automotive"
    assert response.report.domain == "automotive"
    assert response.report.metrics
    assert response.sources


def test_automotive_dashboard_endpoint_with_markdown_source():
    response = dashboard_report(
        QueryRequest(
            query="What maintenance guidance is present?",
            document_path=os.path.join("test_data", "automotive", "maintenance_bulletin.md"),
            domain="automotive",
            max_results=2,
        )
    )

    assert response.domain == "automotive"
    assert response.title == "Automotive Dashboard Report"
    assert response.source_count > 0
