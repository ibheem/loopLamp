# loopLamp

An agentic backend project for document ingestion, retrieval, and domain workflows that is now structured to grow into a LangChain or LangGraph stack.

## What is implemented

- FastAPI backend entry point with `/query` orchestration in `backend/app/main.py`
- Service layer for PDF, CSV, and text ingestion in `backend/services/document_ingestion.py`
- Retrieval workflow with bounded reflection retries in `backend/workflows/query_pipeline.py`
- First concrete domain agent in `backend/agents/telecom_security.py`
- Lightweight in-memory retrieval store so the scaffold works before heavyweight AI dependencies are installed
- Pytest coverage for the API, ingestion flow, retrieval flow, CSV handling, and vector search behavior

## Project structure

```text
loopLamp/
├── backend/
│   ├── core/
│   │   ├── documents.py
│   │   └── models.py
│   ├── guards/
│   │   └── execution.py
│   ├── app/
│   │   └── main.py
│   ├── agents/
│   │   ├── base.py
│   │   ├── ingestion.py
│   │   ├── retrieval.py
│   │   ├── telecom_security.py
│   │   └── vector_db.py
│   ├── services/
│   │   ├── document_ingestion.py
│   │   ├── retrieval.py
│   │   └── vector_store.py
│   ├── workflows/
│   │   └── query_pipeline.py
│   └── tests/
│       ├── test_app.py
│       ├── test_ingestion.py
│       ├── test_retrieval.py
│       └── test_vector_db.py
├── conftest.py
├── pyproject.toml
├── requirements.txt
├── test_data/
└── README.md
```

## Setup

```bash bootstrap.sh```

## Run tests

```bash
cd loopLamp
bash bootstrap.sh
source .venv/bin/activate
pytest -q
```

## Query example

```bash
curl -X POST http://127.0.0.1:8000/query \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "What action is recommended for the SS7 issue?",
    "document_path": "test_data/telecom_incident.txt",
    "domain": "telecom_security",
    "max_results": 2
  }'
```

## Architecture direction

- `backend/services/` contains ingestion, retrieval, and vector-store concerns.
- `backend/workflows/` contains orchestration and loop logic.
- `backend/agents/` is reserved for true domain behavior rather than raw helper functions.
- The current in-memory retrieval layer is the swap point for future LangChain retrievers, embeddings, and vector databases.
- The next clean upgrade is replacing the in-memory retrieval service with LangChain or LangGraph-backed components while keeping the API and workflow contracts stable.

## Notes

- Sample documents are stored in `test_data/` for local testing.
- If you have not installed the Python dependencies yet, the local fallback retrieval path still lets the scaffold run for text, CSV, and simple PDF extraction.
