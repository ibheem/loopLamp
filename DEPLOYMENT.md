# loopLamp Deployment Guide

## Purpose

This guide explains how to run `loopLamp` locally, which environment variables matter today, and what is already in place for future containerization.

For Swagger testing flows, use `API_USAGE.md`.

## Current deployment shape

Today the app is best treated as two local services:

- a `FastAPI` backend on `http://127.0.0.1:8000`
- a `Next.js` frontend on `http://localhost:3000`

This is the current recommended setup because:

- it is already tested in the repo
- the frontend is configured to call the backend over HTTP
- the backend stores uploaded source files locally in `uploaded_sources/`

## Prerequisites

### Backend

- Python `3.9+`
- virtual environment support

### Frontend

- Node.js `18+`
- `npm`

## Backend local run

From the project root:

```bash
cd loopLamp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.app.main:app --reload
```

Backend URLs:

- API root: `http://127.0.0.1:8000/`
- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI schema: `http://127.0.0.1:8000/openapi.json`

## Frontend local run

Open a second terminal:

```bash
cd loopLamp/frontend
npm install
npm run dev
```

Frontend URL:

- UI: `http://localhost:3000`

By default the frontend already calls:

```text
http://127.0.0.1:8000
```

## Environment variables

These are the active environment variables used by the app today.

### Backend

#### `OPENAI_API_KEY`

Optional.

If set, the backend can use the OpenAI-backed report provider for the true LLM agent path.

If not set:

- the backend still runs
- tests still pass
- the app falls back to deterministic or local behavior

Example:

```bash
export OPENAI_API_KEY="your-key-here"
uvicorn backend.app.main:app --reload
```

### Frontend

#### `NEXT_PUBLIC_API_BASE_URL`

Optional.

Overrides the backend base URL used by the Next.js app.

Default:

```text
http://127.0.0.1:8000
```

Example:

```bash
cd loopLamp/frontend
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 npm run dev
```

## Local data and persistence

These folders matter at runtime:

- `test_data/` for bundled sample sources
- `uploaded_sources/` for files uploaded through the API

Important behavior:

- uploaded files are persisted on local disk
- uploaded source metadata is stored in `uploaded_sources/index.json`
- deleting `uploaded_sources/` removes uploaded source state

If you want uploads to survive restarts in a server deployment, this directory should be backed by a persistent volume.

## Smoke-test sequence

After starting both services:

1. open `http://127.0.0.1:8000/docs`
2. run `GET /`
3. run `GET /sources`
4. run `POST /dashboard/report`
5. open `http://localhost:3000`
6. generate a dashboard from the UI

For copy-paste request bodies, use `API_USAGE.md`.

## Test commands

### Backend tests

```bash
cd loopLamp
source .venv/bin/activate
pytest -q
```

### Frontend tests

```bash
cd loopLamp/frontend
npm test
```

## Production-minded notes

The project is not fully containerized yet, but the architecture is already moving in a container-friendly direction:

- backend and frontend are clearly separated
- API URL is configurable from the frontend
- source uploads are isolated to one directory
- FastAPI app entrypoint is explicit
- Next.js app entrypoint is explicit

## Containerization readiness

If we containerize next, the clean split is:

### Backend container

- base image with Python
- installs `requirements.txt`
- runs `uvicorn backend.app.main:app --host 0.0.0.0 --port 8000`
- mounts `uploaded_sources/` as a writable volume
- optionally mounts `test_data/` as read-only

### Frontend container

- base image with Node.js
- installs `frontend/package.json` dependencies
- sets `NEXT_PUBLIC_API_BASE_URL`
- runs `next dev` for development or `next start` after build for production-like mode

### Compose-level wiring

A future `docker-compose.yml` would likely define:

- `backend`
- `frontend`
- optional vector store or database later, if retrieval moves beyond local persistence

## Recommended next container step

The next best deployment step is:

1. add `Dockerfile` for backend
2. add `Dockerfile` for frontend
3. add `docker-compose.yml`
4. mount `uploaded_sources/` as a volume
5. keep `test_data/` available to the backend container

That gives us reproducible local startup without changing the current architecture.

## Known limitations today

- no Docker files are committed yet
- uploaded sources are local-disk only
- no external database is required yet
- no cloud storage integration exists yet
- no reverse proxy or TLS setup is defined yet

## Recommended deployment posture right now

Right now, the best approach is:

- continue local development with the current split backend and frontend
- finish a couple more product-level features before introducing deployment complexity
- add containerization immediately after that as an operational packaging step, not as an architecture rewrite

That keeps the system clean and avoids overcomplicating it too early.
