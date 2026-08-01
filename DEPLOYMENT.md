# loopLamp Deployment Guide

## Purpose

This guide explains how to run `loopLamp` locally, which environment variables matter today, and how to run the project with the included Docker setup.

For Swagger testing flows, use `API_USAGE.md`.

## Current deployment shape

Today the app can run in either of these ways:

- as two local dev services
- as two containers via `docker compose`

The same logical split is preserved in both cases:

- a `FastAPI` backend on `http://127.0.0.1:8000`
- a `Next.js` frontend on `http://localhost:3000`

This is the current recommended setup because:

- it is already tested in the repo
- the frontend is configured to call the backend over HTTP
- the backend stores uploaded source files locally in `uploaded_sources/`

## Docker run

From the project root:

```bash
cd loopLamp
cp .env.example .env
docker compose up --build
```

Container URLs:

- API root: `http://127.0.0.1:8000/`
- Swagger UI: `http://127.0.0.1:8000/docs`
- frontend UI: `http://localhost:3000`

To stop:

```bash
docker compose down
```

To stop and remove the uploaded-source volume too:

```bash
docker compose down -v
```

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

Quick start:

```bash
cd loopLamp
cp .env.example .env
```

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

#### Other provider variables

Optional.

If you want multi-provider selection in the UI, configure one or more of:

- `OPENROUTER_API_KEY`
- `GROQ_API_KEY`
- `TOGETHER_API_KEY`
- `LOOPLAMP_ENABLE_OLLAMA=true` for local Ollama

Each provider also has matching optional model/base-URL values in `.env.example`.

For Docker Compose with Ollama running on your Mac host, set:

```text
OLLAMA_BASE_URL=http://host.docker.internal:11434/v1
```

Using `http://127.0.0.1:11434/v1` from inside the backend container will not reach the host Ollama process.

#### `LOOPLAMP_STARTUP_SOURCE_SYNC`

Optional.

Controls whether the backend walks all saved sources at startup and ensures their vector collections exist.

Default:

```text
false
```

If enabled:

- sample and uploaded sources are checked on backend boot
- existing matching Qdrant collections are reused
- missing or outdated collections are rebuilt automatically

If disabled:

- source indexing happens lazily on first query or manual reindex
- backend startup stays fast even when large PDFs or many uploads exist

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

If you prefer file-based frontend config in local development, place the same value in `frontend/.env.local`.

For Docker Compose, the same variables can live in `.env`:

```bash
cp .env.example .env
```

## Local data and persistence

These folders matter at runtime:

- `test_data/` for bundled sample sources
- `uploaded_sources/` for files uploaded through the API
- `qdrant_storage/` for persistent local vector collections

Important behavior:

- uploaded files are persisted on local disk
- uploaded source metadata is stored in SQLite under the upload storage area
- deleting `uploaded_sources/` removes uploaded source state

In the Docker setup, this is already mounted as a named volume called `uploaded_sources`.
Persistent vector collections are mounted as a named volume called `qdrant_storage`.

If you want uploads to survive deployment replacement in a real server environment, keep this path on persistent storage.

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

## Container notes

The included container setup is intentionally small and practical:

- backend and frontend are clearly separated
- API URL is configurable from the frontend
- source uploads are isolated to one directory
- vector collections are isolated to one directory
- FastAPI app entrypoint is explicit
- Next.js app entrypoint is explicit

## Included container assets

The repo now includes:

- `backend/Dockerfile`
- `frontend/Dockerfile`
- `docker-compose.yml`
- `.dockerignore`
- `frontend/.dockerignore`
- `.env.example`

## Container layout

The current split is:

### Backend container

- base image with Python
- installs `requirements.txt`
- runs `uvicorn backend.app.main:app --host 0.0.0.0 --port 8000`
- mounts `uploaded_sources/` as a writable volume
- mounts `qdrant_storage/` as a writable volume
- optionally mounts `test_data/` as read-only

### Frontend container

- base image with Node.js
- installs `frontend/package.json` dependencies
- sets `NEXT_PUBLIC_API_BASE_URL`
- runs `next dev` for development or `next start` after build for production-like mode

### Compose-level wiring

`docker-compose.yml` defines:

- `backend`
- `frontend`
- named volume for `uploaded_sources`
- named volume for `qdrant_storage`

## Known limitations today

- uploaded sources are still local-disk based, even though Docker now preserves them through a named volume
- no external database is required yet
- no cloud storage integration exists yet
- no reverse proxy or TLS setup is defined yet

## Recommended deployment posture right now

Right now, the best approach is:

- use the included Docker setup for demos, onboarding, and reproducible local startup
- continue feature work without changing the architecture
- address persistence of external data feeds as a separate next step

That keeps the system clean and avoids overcomplicating it too early.
