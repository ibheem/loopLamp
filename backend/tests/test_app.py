import asyncio
import base64
from io import BytesIO

from backend.app import main as main_module
from backend.app.main import (
    app,
    dashboard_report,
    delete_source,
    list_sources,
    query_documents,
    root,
    upload_source,
)
from backend.core.models import QueryRequest, UploadSourceRequest
from backend.services.source_registry import SourceRegistryService


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


def test_query_endpoint_accepts_source_id():
    sources = list_sources().sources
    telecom_source = next(source for source in sources if source.domain == "telecom_security")
    response = query_documents(
        QueryRequest(
            query="What action is recommended for the SS7 issue?",
            source_id=telecom_source.source_id,
            domain="telecom_security",
            max_results=2,
        )
    )

    assert response.domain == "telecom_security"
    assert response.sources


def test_cors_allows_local_frontend_origin():
    cors_middleware = app.user_middleware[0]

    assert cors_middleware.cls.__name__ == "CORSMiddleware"
    assert "http://localhost:3000" in cors_middleware.options["allow_origins"]
    assert "http://127.0.0.1:3000" in cors_middleware.options["allow_origins"]


def test_list_sources_returns_known_domains():
    response = list_sources()

    assert response.sources
    assert any(source.domain == "telecom_security" for source in response.sources)


def test_upload_source_returns_record():
    response = upload_source(
        UploadSourceRequest(
            filename="upload_note.txt",
            domain="general",
            content_base64=base64.b64encode(b"context note").decode("utf-8"),
        )
    )

    assert response.source.origin == "upload"
    assert response.source.domain == "general"


def test_delete_source_returns_record(tmp_path, monkeypatch):
    uploads_dir = tmp_path / "uploads"
    index_path = uploads_dir / "index.json"
    service = SourceRegistryService(project_root=tmp_path, uploads_dir=uploads_dir, index_path=index_path)
    record = service.save_upload(
        filename="delete_me.txt",
        content=b"context note",
        domain="general",
    )
    monkeypatch.setattr(main_module, "source_registry", service)

    response = delete_source(record.source_id)

    assert response.deleted is True
    assert response.source_id == record.source_id
