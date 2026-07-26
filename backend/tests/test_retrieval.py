import os
from backend.agents.ingestion import ingest_pdf
from backend.agents.vector_db import build_vector_db
from backend.agents.retrieval import retrieve_context

def test_retrieve_context():
    # Use the sample PDF from earlier steps
    pdf_path = os.path.join("test_data", "ecommerce-full-100products.pdf")
    chunks = ingest_pdf(pdf_path)
    db = build_vector_db(chunks)

    # Run retrieval on a query
    results = retrieve_context(db, "refund policy", k=3)

    # Validation: should return at least one relevant chunk
    assert len(results) > 0
    # Check that the chunk has text content
    assert hasattr(results[0], "page_content")
    # Optional: check keyword presence
    assert "policy" in results[0].page_content.lower()
