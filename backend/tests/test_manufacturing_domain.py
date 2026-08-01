import os

from backend.app.main import dashboard_report, query_documents
from backend.core.models import QueryRequest


def test_manufacturing_query_endpoint_with_text_source():
    response = query_documents(
        QueryRequest(
            query="What should happen after a quality defect is reported?",
            document_path=os.path.join("test_data", "manufacturing", "quality_incident.txt"),
            domain="manufacturing",
            max_results=2,
        )
    )

    assert response.domain == "manufacturing"
    assert response.report.domain == "manufacturing"
    assert response.report.metrics
    assert response.sources


def test_manufacturing_dashboard_endpoint_with_markdown_source():
    response = dashboard_report(
        QueryRequest(
            query="What process guidance applies before restarting the line?",
            document_path=os.path.join("test_data", "manufacturing", "sop_guidelines.md"),
            domain="manufacturing",
            max_results=2,
        )
    )

    assert response.domain == "manufacturing"
    assert response.title == "Manufacturing Dashboard Report"
    assert response.source_count > 0
