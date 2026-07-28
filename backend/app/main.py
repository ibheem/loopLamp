from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.core.models import DashboardResponse, ErrorResponse, QueryRequest, QueryResponse
from backend.services.dashboard_transformer import build_dashboard_response
from backend.workflows.query_pipeline import QueryPipeline

app = FastAPI(
    title="loopLamp API",
    description=(
        "Document-driven domain reporting API. "
        "Use `/query` with a supported local file path to generate a structured DomainReport."
    ),
    version="0.1.0",
)
pipeline = QueryPipeline()

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


@app.post(
    "/query",
    response_model=QueryResponse,
    summary="Generate a domain report from a local document",
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
