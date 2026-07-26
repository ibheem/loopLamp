# loopLamp

An agentic backend project for PDF ingestion, retrieval, and vector search workflows.

## What is implemented

- FastAPI backend entry point in `backend/app/main.py`
- PDF ingestion pipeline using LangChain + PyPDFLoader with chunking
- Retrieval helper for similarity-based context lookup
- Vector database builder using Chroma and Hugging Face embeddings
- Pytest coverage for the app, ingestion flow, retrieval flow, and vector DB setup
- Shared pytest bootstrap via `conftest.py` and editable packaging config via `pyproject.toml`

## Project structure

```text
loopLamp/
├── backend/
│   ├── app/
│   │   └── main.py
│   ├── agents/
│   │   ├── ingestion.py
│   │   ├── retrieval.py
│   │   └── vector_db.py
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

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## Run tests

```bash
source .venv/bin/activate
pytest -q
```

## Example usage

```python
from backend.agents.ingestion import ingest_pdf

chunks = ingest_pdf("test_data/ecommerce-full-100products.pdf")
print(len(chunks))
print(chunks[0].page_content[:200])
```

## Notes

- Sample PDF documents are stored in `test_data/` for local testing.
- The ingestion and retrieval modules are designed to be extended for future agent workflows.
