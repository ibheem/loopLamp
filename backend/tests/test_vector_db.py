import os
from backend.agents.ingestion import ingest_pdf
from backend.agents.vector_db import build_vector_db

def test_vector_db_retrieval():
    # Use the same sample PDF from Step 1
    pdf_path = os.path.join("test_data", "ecommerce-full-100products.pdf")
    chunks = ingest_pdf(pdf_path)
    db = build_vector_db(chunks)

    # Run a similarity search
    results = db.similarity_search("policy", k=3)

    # Validation: should return at least one relevant chunk
    assert len(results) > 0
    assert hasattr(results[0], "page_content")
