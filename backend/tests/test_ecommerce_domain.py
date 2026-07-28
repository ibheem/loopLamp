import os

from backend.app.main import dashboard_report, query_documents
from backend.core.models import QueryRequest


def test_ecommerce_query_endpoint_with_text_source():
    response = query_documents(
        QueryRequest(
            query="What should be done for a delayed order with a refund request?",
            document_path=os.path.join("test_data", "ecommerce", "customer_issue.txt"),
            domain="ecommerce",
            max_results=2,
        )
    )

    assert response.domain == "ecommerce"
    assert response.report.domain == "ecommerce"
    assert response.report.metrics
    assert response.sources


def test_ecommerce_dashboard_endpoint_with_markdown_source():
    response = dashboard_report(
        QueryRequest(
            query="What return policy guidance applies for an opened product?",
            document_path=os.path.join("test_data", "ecommerce", "return_policy.md"),
            domain="ecommerce",
            max_results=2,
        )
    )

    assert response.domain == "ecommerce"
    assert response.title == "Ecommerce Dashboard Report"
    assert response.source_count > 0
