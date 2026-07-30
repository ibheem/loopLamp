# loopLamp Windows Setup

## Purpose

This guide is for Windows teammates who want to run `loopLamp` locally, run tests, and use the Docker setup.

## Prerequisites

Install these first:

- Python `3.9+`
- Node.js `18+`
- `npm`
- Git
- Optional: Docker Desktop

## Project layout

From the repo root:

```powershell
cd loopLamp
```

Backend lives in:

```text
backend/
```

Frontend lives in:

```text
frontend/
```

## Backend setup

### PowerShell

```powershell
cd loopLamp
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

### Command Prompt

```cmd
cd loopLamp
python -m venv .venv
.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Run backend

With the virtual environment active:

```powershell
uvicorn backend.app.main:app --reload
```

Backend URLs:

- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`
- Health check: `http://127.0.0.1:8000/`

## Frontend setup

Open a second terminal:

```powershell
cd loopLamp\frontend
npm install
```

## Run frontend

```powershell
cd loopLamp\frontend
npm run dev
```

Frontend URL:

- UI: `http://localhost:3000`

## Environment variables

### Backend

Optional example in PowerShell:

```powershell
$env:OPENAI_API_KEY="your-key-here"
$env:LOOPLAMP_STARTUP_SOURCE_SYNC="false"
uvicorn backend.app.main:app --reload
```

### Frontend

Optional example in PowerShell:

```powershell
cd loopLamp\frontend
$env:NEXT_PUBLIC_API_BASE_URL="http://127.0.0.1:8000"
npm run dev
```

## Recommended local run flow

### Terminal 1

```powershell
cd loopLamp
.venv\Scripts\Activate.ps1
uvicorn backend.app.main:app --reload
```

### Terminal 2

```powershell
cd loopLamp\frontend
npm run dev
```

## Backend tests

From the project root:

```powershell
cd loopLamp
.venv\Scripts\Activate.ps1
pytest -q
```

Run only selected backend tests:

```powershell
pytest -q backend/tests/test_app.py
pytest -q backend/tests/test_source_registry.py
pytest -q backend/tests/test_docs_schema.py
```

## Frontend tests

```powershell
cd loopLamp\frontend
npm test
```

## Helpful dev commands

### Reinstall backend dependencies

```powershell
cd loopLamp
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Clean frontend cache and restart

```powershell
cd loopLamp\frontend
npm run dev:clean
```

### Compile-check backend

```powershell
cd loopLamp
.venv\Scripts\Activate.ps1
python -m compileall backend
```

## Docker option

If Docker Desktop is installed:

```powershell
cd loopLamp
Copy-Item .env.example .env
docker compose up --build
```

URLs:

- Backend: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`
- Frontend: `http://localhost:3000`

Stop containers:

```powershell
docker compose down
```

Stop and remove named volumes too:

```powershell
docker compose down -v
```

## Notes for this project

- Uploaded files are stored in `uploaded_sources/`
- Vector storage is persisted in `qdrant_storage/`
- Source metadata and index status are persisted in SQLite
- Startup source sync is disabled by default to keep backend boot fast

## Common issues

### PowerShell blocks activation

Run this once in a PowerShell window opened as your user:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then reopen the terminal and activate:

```powershell
.venv\Scripts\Activate.ps1
```

### Port already in use

If `8000` or `3000` is already in use, stop the old process or start the service on another port.

### Frontend cache issues

Use:

```powershell
cd loopLamp\frontend
npm run dev:clean
```

### Missing Python packages

Re-activate the virtual environment and reinstall:

```powershell
cd loopLamp
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
