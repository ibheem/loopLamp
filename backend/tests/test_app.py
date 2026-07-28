from backend.app.main import app, dashboard_report, query_documents, root
from backend.core.models import QueryRequest


def test_root_endpoint():
    assert root() == {"message": "Agentic System Backend Ready", "workflow": "query_pipeline"}


def test_query_endpoint():
    response = query_documents(
        QueryRequest(
            query="What action is recommended for the SS7 issue?",
            document_path="test_data/telecom_incident.txt",
            domain="telecom_security",
            max_results=2,
        )
    )

    assert response.domain == "telecom_security"
    assert response.sources
    assert "retrieved context" in response.answer.lower()
    assert response.report.domain == "telecom_security"
    assert response.report.metrics
    assert response.report.insights
    assert response.report.recommendations
    assert response.report.source_refs


def test_dashboard_report_endpoint():
    response = dashboard_report(
        QueryRequest(
            query="What action is recommended for the SS7 issue?",
            document_path="test_data/telecom_incident.txt",
            domain="telecom_security",
            max_results=2,
        )
    )

    assert response.domain == "telecom_security"
    assert response.title == "Telecom Security Dashboard Report"
    assert response.source_count > 0
    assert response.metrics
    assert response.actions


def test_cors_allows_local_frontend_origin():
    cors_middleware = app.user_middleware[0]

    assert cors_middleware.cls.__name__ == "CORSMiddleware"
    assert "http://localhost:3000" in cors_middleware.options["allow_origins"]
    assert "http://127.0.0.1:3000" in cors_middleware.options["allow_origins"]
