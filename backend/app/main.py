from fastapi import FastAPI, HTTPException

from backend.core.models import QueryRequest, QueryResponse
from backend.workflows.query_pipeline import QueryPipeline

app = FastAPI()
pipeline = QueryPipeline()

@app.get("/")
def root():
    return {"message": "Agentic System Backend Ready", "workflow": "query_pipeline"}


@app.post("/query", response_model=QueryResponse)
def query_documents(request: QueryRequest):
    try:
        return pipeline.run(request)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
