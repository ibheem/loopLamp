from backend.app.main import query_documents, root
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
