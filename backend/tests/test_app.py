import asyncio
import base64
import json
from io import BytesIO
from types import SimpleNamespace
import zipfile

from fastapi import HTTPException

from backend.app import main as main_module
from backend.app.main import (
    app,
    dashboard_report,
    delete_source,
    list_sources,
    query_documents,
    reindex_source,
    run_startup_source_sync,
    root,
    startup_source_sync,
    upload_source,
)
from backend.core.models import QueryRequest, UploadSourceRequest
from backend.core.models import DomainReport
from backend.services.source_registry import SourceRegistryService
from backend.workflows.query_pipeline import QueryPipeline


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
    assert response.matched_sources
    assert response.evidence_cards


def test_query_endpoint_accepts_source_id():
    sources = list_sources().sources
    telecom_source = next(
        source
        for source in sources
        if source.domain == "telecom_security" and source.label == "telecom_incident.txt"
    )
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


def test_query_request_accepts_domain_mode_without_source_reference():
    request = QueryRequest(
        query="Summarize the main risks across finance.",
        retrieval_mode="domain",
        domain="financial_risk",
        max_results=3,
    )

    assert request.retrieval_mode == "domain"
    assert request.source_id is None
    assert request.document_path is None


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


def test_upload_source_accepts_csv():
    response = upload_source(
        UploadSourceRequest(
            filename="orders.csv",
            domain="ecommerce",
            content_base64=base64.b64encode(b"order_id,status\nEC-1,delayed\n").decode("utf-8"),
        )
    )

    assert response.source.origin == "upload"
    assert response.source.file_type == ".csv"


def test_upload_source_accepts_json():
    payload = json.dumps({"issue": "refund_requested", "order_id": "EC-1042"}).encode("utf-8")
    response = upload_source(
        UploadSourceRequest(
            filename="issue.json",
            domain="ecommerce",
            content_base64=base64.b64encode(payload).decode("utf-8"),
        )
    )

    assert response.source.origin == "upload"
    assert response.source.file_type == ".json"


def test_upload_source_rejects_zip_disguised_as_json():
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, mode="w") as archive:
        archive.writestr("HealthCareMagic-100k.json", '{"ok": true}')

    try:
        upload_source(
            UploadSourceRequest(
                filename="HealthCareMagic-100k.json",
                domain="medical_qa",
                content_base64=base64.b64encode(buffer.getvalue()).decode("utf-8"),
            )
        )
    except HTTPException as exc:
        assert exc.status_code == 400
        assert "appears to be a ZIP archive" in exc.detail
    else:
        raise AssertionError("Expected ZIP-disguised JSON upload to be rejected.")


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


def test_reindex_source_returns_record(monkeypatch):
    monkeypatch.setattr(
        main_module.pipeline,
        "reindex_source",
        lambda source_id: {
            "source_id": source_id,
            "indexed": True,
            "document_count": 3,
            "vector_backend": "qdrant_persistent",
        },
    )

    response = reindex_source("sample:ecommerce:return_policy.md")

    assert response.indexed is True
    assert response.document_count == 3
    assert response.vector_backend == "qdrant_persistent"


def test_run_startup_source_sync_calls_pipeline(monkeypatch):
    monkeypatch.setenv("LOOPLAMP_STARTUP_SOURCE_SYNC", "true")
    monkeypatch.setattr(main_module.pipeline, "sync_saved_sources", lambda: {"indexed_count": 4, "failed_count": 1})

    result = run_startup_source_sync()

    assert result == {"indexed_count": 4, "failed_count": 1}


def test_run_startup_source_sync_can_be_disabled(monkeypatch):
    monkeypatch.setenv("LOOPLAMP_STARTUP_SOURCE_SYNC", "false")

    result = run_startup_source_sync()

    assert result == {"indexed_count": 0, "failed_count": 0, "skipped": True}


def test_startup_source_sync_invokes_runner(monkeypatch):
    calls = []
    monkeypatch.setattr(main_module, "run_startup_source_sync", lambda: calls.append("ran") or {"indexed_count": 1, "failed_count": 0})

    startup_source_sync()

    assert calls == ["ran"]


def test_query_pipeline_sync_saved_sources_indexes_available_records(monkeypatch):
    pipeline = QueryPipeline()
    indexed_keys = []
    state_updates = []
    fake_sources = [
        SimpleNamespace(source_id="sample:telecom_security:telecom_incident.txt", path="first.txt"),
        SimpleNamespace(source_id="upload:20260728061500_field_notes.txt", path="second.txt"),
    ]
    monkeypatch.setattr(pipeline.source_registry, "list_indexable_sources", lambda: fake_sources)
    monkeypatch.setattr(
        pipeline.source_registry,
        "set_source_index_state",
        lambda source_id, index_status, vector_backend="", indexed_document_count=None: state_updates.append(
            (source_id, index_status, vector_backend, indexed_document_count)
        ),
    )
    monkeypatch.setattr(pipeline.ingestion_service, "ingest", lambda path: [SimpleNamespace(page_content=f"content-{path}", metadata={})])

    def fake_build_vector_db(documents, collection_key="", force_reindex=False):
        indexed_keys.append((collection_key, force_reindex, len(documents)))
        return SimpleNamespace(backend_name="qdrant_persistent")

    monkeypatch.setattr("backend.workflows.query_pipeline.build_vector_db", fake_build_vector_db)

    result = pipeline.sync_saved_sources()

    assert result == {"indexed_count": 2, "failed_count": 0}
    assert indexed_keys == [
        ("sample:telecom_security:telecom_incident.txt", False, 1),
        ("upload:20260728061500_field_notes.txt", False, 1),
    ]
    assert state_updates == [
        ("sample:telecom_security:telecom_incident.txt", "indexed", "qdrant_persistent", 1),
        ("upload:20260728061500_field_notes.txt", "indexed", "qdrant_persistent", 1),
    ]


def test_query_pipeline_sync_saved_sources_tracks_failures(monkeypatch):
    pipeline = QueryPipeline()
    state_updates = []
    fake_sources = [
        SimpleNamespace(source_id="sample:telecom_security:telecom_incident.txt", path="ok.txt"),
        SimpleNamespace(source_id="upload:20260728061500_bad.txt", path="bad.txt"),
    ]
    monkeypatch.setattr(pipeline.source_registry, "list_indexable_sources", lambda: fake_sources)
    monkeypatch.setattr(
        pipeline.source_registry,
        "set_source_index_state",
        lambda source_id, index_status, vector_backend="", indexed_document_count=None: state_updates.append(
            (source_id, index_status, vector_backend, indexed_document_count)
        ),
    )

    def fake_ingest(path):
        if path == "bad.txt":
            raise ValueError("unsupported payload")
        return [SimpleNamespace(page_content="content", metadata={})]

    monkeypatch.setattr(pipeline.ingestion_service, "ingest", fake_ingest)
    monkeypatch.setattr(
        "backend.workflows.query_pipeline.build_vector_db",
        lambda documents, collection_key="", force_reindex=False: SimpleNamespace(backend_name="qdrant_persistent"),
    )

    result = pipeline.sync_saved_sources()

    assert result == {"indexed_count": 1, "failed_count": 1}
    assert state_updates == [
        ("sample:telecom_security:telecom_incident.txt", "indexed", "qdrant_persistent", 1),
        ("upload:20260728061500_bad.txt", "failed", "", None),
    ]


def test_query_pipeline_domain_mode_aggregates_domain_sources(monkeypatch):
    pipeline = QueryPipeline()
    state_updates = []
    fake_sources = [
        SimpleNamespace(source_id="sample:financial_risk:first.pdf", path="first.txt", domain="financial_risk", origin="sample"),
        SimpleNamespace(source_id="sample:general:note.txt", path="second.txt", domain="general", origin="sample"),
    ]
    monkeypatch.setattr(pipeline.source_registry, "list_sources_for_domain", lambda domain: fake_sources)
    monkeypatch.setattr(
        pipeline.source_registry,
        "set_source_index_state",
        lambda source_id, index_status, vector_backend="", indexed_document_count=None: state_updates.append(
            (source_id, index_status, vector_backend, indexed_document_count)
        ),
    )

    def fake_ingest(path):
        return [SimpleNamespace(page_content=f"content-{path}", metadata={})]

    monkeypatch.setattr(pipeline.ingestion_service, "ingest", fake_ingest)
    build_calls = []

    def fake_build_vector_db(documents, collection_key="", force_reindex=False):
        build_calls.append((collection_key, force_reindex, len(documents)))
        return SimpleNamespace(
            backend_name="qdrant_persistent",
            similarity_search=lambda query, k=5: documents[:k],
        )

    monkeypatch.setattr("backend.workflows.query_pipeline.build_vector_db", fake_build_vector_db)
    monkeypatch.setattr(
        pipeline.workflow,
        "run",
        lambda agent, vector_db, request: SimpleNamespace(
            answer=DomainReport(
                summary="retrieved context across domain sources",
                domain=request.domain,
                metrics=[],
                insights=[],
                recommendations=[],
                source_refs=[],
            ),
            attempts=1,
            used_reflection=False,
            sources=vector_db.similarity_search(request.query, k=request.max_results),
        ),
    )

    response = pipeline.run(
        QueryRequest(
            query="Summarize financial rules across the domain.",
            retrieval_mode="domain",
            domain="financial_risk",
            max_results=2,
        )
    )

    assert response.domain == "financial_risk"
    assert len(response.sources) == 2
    assert build_calls == [("domain:financial_risk:all_sources", False, 2)]
    assert state_updates == [
        ("sample:financial_risk:first.pdf", "indexed", "qdrant_persistent", 1),
        ("sample:general:note.txt", "indexed", "qdrant_persistent", 1),
    ]
