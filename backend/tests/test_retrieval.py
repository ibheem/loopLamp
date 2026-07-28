import os
from backend.agents.ingestion import ingest_pdf
from backend.agents.vector_db import build_vector_db
from backend.agents.retrieval import retrieve_context


def test_retrieve_context():
    pdf_path = os.path.join("test_data", "ecommerce-full-100products.pdf")
    chunks = ingest_pdf(pdf_path)
    db = build_vector_db(chunks)
    results = retrieve_context(db, "refund policy", k=3)
    assert len(results) > 0
    assert hasattr(results[0], "page_content")
    content = " ".join(result.page_content.lower() for result in results)
    assert "refund" in content or "policy" in content
