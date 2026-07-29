import os

from backend.app.main import dashboard_report, query_documents
from backend.core.models import QueryRequest


def test_banking_assistant_query_endpoint_with_text_source():
    response = query_documents(
        QueryRequest(
            query="What should be done for a failed ATM debit complaint?",
            document_path=os.path.join("test_data", "banking_assistant", "atm_notice.txt"),
            domain="banking_assistant",
            max_results=2,
        )
    )

    assert response.domain == "banking_assistant"
    assert response.report.domain == "banking_assistant"
    assert response.report.metrics
    assert response.sources


def test_banking_assistant_dashboard_endpoint_with_markdown_source():
    response = dashboard_report(
        QueryRequest(
            query="What service charge guidance is mentioned?",
            document_path=os.path.join("test_data", "banking_assistant", "service_charges.md"),
            domain="banking_assistant",
            max_results=2,
        )
    )

    assert response.domain == "banking_assistant"
    assert response.title == "Banking Assistant Dashboard Report"
    assert response.source_count > 0
