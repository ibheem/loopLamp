# loopLamp Architecture and Usage Guide

## Purpose

`loopLamp` is a backend-first domain reporting application that ingests local documents, retrieves relevant context, and returns a dashboard-ready `DomainReport`.

The current design keeps:

- `FastAPI` for the HTTP API
- `services/` for ingestion, retrieval, embeddings, and provider integrations
- `workflows/` for orchestration and retry logic
- `agents/` for domain behavior
- `core/` for shared data contracts

This keeps the system clean while allowing `LangChain` and `LangGraph` to be introduced behind stable interfaces.

## Current Request Flow

1. A client calls `POST /query`.
2. `QueryRequest` validates the payload in `backend/core/models.py`.
3. `QueryPipeline` selects the domain agent in `backend/workflows/query_pipeline.py`.
4. `DocumentIngestionService` loads the local `.txt`, `.md`, `.pdf`, or `.csv` file.
5. `build_vector_db()` creates a retrieval backend.
6. `QueryGraphWorkflow` orchestrates retrieve and generate steps with retry support.
7. The selected agent returns a `DomainReport`.
8. The API returns a `QueryResponse` containing:
   - `answer`
   - `report`
   - `sources`
   - execution metadata
9. `POST /dashboard/report` can transform that response into a UI-friendly dashboard payload.

## Runtime Modes

### Local fallback mode

If no OpenAI credentials are configured:

- the app still runs end to end
- tests still pass
- retrieval uses local fallback behavior when richer dependencies are unavailable
- the deterministic telecom agent is used when the LLM provider is unavailable

### LLM mode

If `OPENAI_API_KEY` is set:

- `OpenAIReportAgent` can generate structured `DomainReport` output through the OpenAI Responses API
- if live generation fails, the system falls back to deterministic logic

## Supported Inputs

Current supported local file types:

- `.txt`
- `.md`
- `.pdf`
- `.csv`

The `document_path` must point to a local file accessible from the running app.

## API Endpoints

### `GET /`

Health-style endpoint that confirms the API is live.

### `POST /query`

Generates a structured domain report.

Example payload:

```json
{
  "query": "What action is recommended for the SS7 issue?",
  "document_path": "test_data/telecom_incident.txt",
  "domain": "telecom_security",
  "max_results": 2
}
```

Example response shape:

```json
{
  "answer": "Telecom summary...",
  "domain": "telecom_security",
  "attempts": 1,
  "used_reflection": false,
  "report": {
    "domain": "telecom_security",
    "summary": "Telecom summary...",
    "metrics": [],
    "insights": [],
    "recommendations": [],
    "source_refs": []
  },
  "sources": []
}
```

### `POST /dashboard/report`

Generates a dashboard-oriented payload for cards, lists, highlights, and chart-ready metrics.

Example payload:

```json
{
  "query": "What action is recommended for the SS7 issue?",
  "document_path": "test_data/telecom_incident.txt",
  "domain": "telecom_security",
  "max_results": 2
}
```

Example response shape:

```json
{
  "domain": "telecom_security",
  "title": "Telecom Security Dashboard Report",
  "summary": "Based on the retrieved context...",
  "status": {
    "level": "info",
    "issues": []
  },
  "metrics": [],
  "highlights": [],
  "actions": [],
  "source_count": 1,
  "execution": {},
  "evaluation": {}
}
```

## Core Contracts

### `DomainReport`

The dashboard-facing contract. Every domain agent should produce this normalized structure:

- `domain`
- `summary`
- `metrics`
- `insights`
- `recommendations`
- `source_refs`

This is the key to keeping the future dashboard dynamic across multiple domains.

### `QueryRequest`

The incoming API payload:

- `query`
- `document_path`
- `domain`
- `max_results`

## Project Layout

### `backend/app`

API entrypoint and route definitions.

### `backend/core`

Shared types and API schemas.

### `backend/services`

Infrastructure and external-integration layer:

- document ingestion
- retrieval backend selection
- vector store construction
- LLM provider integration

### `backend/workflows`

Execution flow and orchestration:

- query pipeline
- graph-ready workflow
- retry and reflection behavior

### `backend/agents`

Domain behavior:

- deterministic telecom agent
- OpenAI-backed report agent

### `backend/tests`

Reference and regression tests for:

- API flow
- ingestion
- retrieval
- graph orchestration
- LLM fallback behavior
- dashboard report contract

## How To Run

```bash
cd /Users/prashant/capstone/loopLamp
bash bootstrap.sh
source .venv/bin/activate
uvicorn backend.app.main:app --reload
```

Open:

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/`

## How To Test From Swagger

Use the `POST /query` endpoint with a real local path, not the placeholder `"string"`.

Recommended example:

```json
{
  "query": "What action is recommended for the SS7 issue?",
  "document_path": "test_data/telecom_incident.txt",
  "domain": "telecom_security",
  "max_results": 2
}
```

Common `400` causes:

- placeholder path like `"string"`
- unsupported extension
- file does not exist
- unsupported domain

## Current Architectural Status

The app is:

- runnable end to end
- dashboard-contract ready
- LangChain-aware in `services/`
- graph-ready in `workflows/`
- LLM-capable with graceful fallback
- dashboard-endpoint ready

The app is not yet:

- multi-domain complete
- production-observability complete
- evaluation-heavy
- frontend/dashboard-complete

## Recommended Next Steps

1. Add observability metadata to reports and workflow logs.
2. Add evaluator checks for grounding and empty evidence.
3. Introduce a second domain agent using the same `DomainReport` contract.
4. Add frontend visualization on top of `/dashboard/report`.
5. Containerize after the frontend/backend contract is stable.
