import os
from backend.agents.ingestion import ingest_pdf
from backend.agents.vector_db import build_vector_db


def test_vector_db_retrieval():
    pdf_path = os.path.join("test_data", "ecommerce-full-100products.pdf")
    chunks = ingest_pdf(pdf_path)
    db = build_vector_db(chunks)
    results = db.similarity_search("policy", k=3)
    assert len(results) > 0
    assert hasattr(results[0], "page_content")
    assert "policy" in " ".join(result.page_content.lower() for result in results)
