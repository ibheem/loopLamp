from base64 import b64decode
from pathlib import Path

from fastapi import FastAPI, HTTPException, Path as ApiPath
from fastapi.middleware.cors import CORSMiddleware

from backend.core.models import (
    DashboardResponse,
    DeleteSourceResponse,
    ErrorResponse,
    QueryRequest,
    QueryResponse,
    SourceListResponse,
    UploadSourceRequest,
    UploadSourceResponse,
)
from backend.services.dashboard_transformer import build_dashboard_response
from backend.services.source_registry import SourceRegistryService
from backend.workflows.query_pipeline import QueryPipeline

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

@app.get(
    "/",
    summary="Health check",
    tags=["System"],
)
def root():
    return {"message": "Agentic System Backend Ready", "workflow": "query_pipeline"}


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
    suffix = Path(request.filename).suffix.lower()
    if suffix not in {".txt", ".md", ".pdf", ".csv", ".json"}:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix}")
    content = b64decode(request.content_base64.encode("utf-8"))
    record = source_registry.save_upload(filename=request.filename, content=content, domain=request.domain)
    return UploadSourceResponse(source=record)


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
