from base64 import b64decode
from io import BytesIO
import logging
import os
from pathlib import Path
import zipfile

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Path as ApiPath
from fastapi.middleware.cors import CORSMiddleware

from backend.core.models import (
    DashboardResponse,
    DeleteSourceResponse,
    ErrorResponse,
    LLMProviderCatalogResponse,
    QueryRequest,
    QueryResponse,
    ReindexSourceResponse,
    SourceListResponse,
    UploadSourceRequest,
    UploadSourceResponse,
)
from backend.services.dashboard_transformer import build_dashboard_response
from backend.services.source_registry import SourceRegistryService
from backend.workflows.query_pipeline import QueryPipeline

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

logger = logging.getLogger(__name__)

app = FastAPI(
    title="loopLamp API",
    description=(
        "Document-driven domain reporting API. "
        "Use `/sources` to browse registered datasets, `/sources/upload` to add new files, "
        "and `/query` or `/dashboard/report` to generate structured domain outputs."
    ),
    version="0.1.0",
    openapi_tags=[
        {"name": "System", "description": "Health and service metadata."},
        {"name": "LLM", "description": "Inspect configured LLM providers and model choices."},
        {"name": "Sources", "description": "Browse, upload, and delete reusable source documents."},
        {"name": "Reports", "description": "Generate structured domain reports from saved or local sources."},
        {"name": "Dashboard", "description": "Build dashboard-friendly payloads for the frontend."},
    ],
)
pipeline = QueryPipeline()
source_registry = SourceRegistryService()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def run_startup_source_sync():
    startup_sync_enabled = os.getenv("LOOPLAMP_STARTUP_SOURCE_SYNC", "false").strip().lower()
    if startup_sync_enabled in {"0", "false", "no", "off"}:
        return {"indexed_count": 0, "failed_count": 0, "skipped": True}
    return pipeline.sync_saved_sources()


def validate_upload_content(filename: str, content: bytes):
    suffix = Path(filename).suffix.lower()
    if suffix not in {".txt", ".md", ".pdf", ".csv", ".json"}:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix}")

    if suffix in {".txt", ".md", ".csv", ".json"} and zipfile.is_zipfile(BytesIO(content)):
        raise HTTPException(
            status_code=400,
            detail=f"Uploaded file content does not match {suffix} and appears to be a ZIP archive.",
        )


@app.on_event("startup")
def startup_source_sync():
    run_startup_source_sync()
    pipeline.provider_registry.log_startup_health()


@app.get(
    "/",
    summary="Health check",
    tags=["System"],
)
def root():
    return {"message": "Agentic System Backend Ready", "workflow": "query_pipeline"}


@app.get(
    "/llm/providers",
    response_model=LLMProviderCatalogResponse,
    summary="List configured LLM providers",
    description="Returns the selectable provider catalog for request-level LLM choice in the UI or API clients.",
    tags=["LLM"],
)
def list_llm_providers():
    return LLMProviderCatalogResponse(
        default_provider_id=pipeline.provider_registry.default_provider_id(),
        providers=pipeline.provider_registry.list_provider_records(),
    )


@app.get(
    "/sources",
    response_model=SourceListResponse,
    summary="List saved and uploaded sources",
    description="Returns sample datasets and uploaded sources available for domain queries.",
    tags=["Sources"],
)
def list_sources():
    return SourceListResponse(sources=source_registry.list_sources())


@app.delete(
    "/sources/{source_id:path}",
    response_model=DeleteSourceResponse,
    summary="Delete an uploaded source document",
    description="Removes a previously uploaded source. Sample sources are read-only and cannot be deleted.",
    tags=["Sources"],
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Sample sources cannot be deleted.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Source was not found.",
        },
    },
)
def delete_source(
    source_id: str = ApiPath(
        ...,
        description="Uploaded source identifier returned by `/sources` or `/sources/upload`.",
        examples=["upload:20260728061500_field_notes.txt"],
    )
):
    try:
        record = source_registry.delete_source(source_id)
        return DeleteSourceResponse(source_id=record.source_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post(
    "/sources/upload",
    response_model=UploadSourceResponse,
    summary="Upload a new source document",
    description="Accepts a base64-encoded file payload and registers it as a reusable source for future queries.",
    tags=["Sources"],
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Unsupported file type or invalid upload request.",
        }
    },
)
def upload_source(request: UploadSourceRequest):
    content = b64decode(request.content_base64.encode("utf-8"))
    validate_upload_content(request.filename, content)
    record = source_registry.save_upload(filename=request.filename, content=content, domain=request.domain)
    return UploadSourceResponse(source=record)


@app.post(
    "/sources/{source_id:path}/reindex",
    response_model=ReindexSourceResponse,
    summary="Reindex a saved source into persistent vector storage",
    description="Rebuilds the vector index for a saved source using the active vector backend. When Qdrant is available, this refreshes the persistent collection.",
    tags=["Sources"],
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Source could not be ingested or indexed.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Source was not found.",
        },
    },
)
def reindex_source(
    source_id: str = ApiPath(
        ...,
        description="Sample or uploaded source identifier returned by `/sources`.",
        examples=["sample:ecommerce:return_policy.md"],
    )
):
    try:
        result = pipeline.reindex_source(source_id)
        return ReindexSourceResponse(**result)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post(
    "/query",
    response_model=QueryResponse,
    summary="Generate a domain report from a local document",
    description="Use either a saved `source_id` or a direct `document_path` to retrieve context and build a DomainReport.",
    tags=["Reports"],
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Invalid domain, unsupported file type, or missing document path.",
        }
    },
)
def query_documents(request: QueryRequest):
    try:
        return pipeline.run(request)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post(
    "/dashboard/report",
    response_model=DashboardResponse,
    summary="Generate a dashboard-friendly report payload",
    description="Uses the same query pipeline as `/query`, then transforms the report into a frontend-friendly dashboard shape.",
    tags=["Dashboard"],
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Invalid domain, unsupported file type, or missing document path.",
        }
    },
)
def dashboard_report(request: QueryRequest):
    try:
        query_response = pipeline.run(request)
        return build_dashboard_response(query_response)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
