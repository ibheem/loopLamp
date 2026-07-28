from fastapi import FastAPI, HTTPException

from backend.core.models import ErrorResponse, QueryRequest, QueryResponse
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
