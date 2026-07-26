from backend.agents.ingestion import ingest_pdf
import os

def test_ingest_pdf():
    # Use a sample PDF placed in sample_docs
    pdf_path = os.path.join("test_data", "ecommerce-full-100products.pdf")
    chunks = ingest_pdf(pdf_path)
    # Validation: ingestion returns non-empty chunks
    assert len(chunks) > 0
    # Optional: check chunk type
    assert hasattr(chunks[0], "page_content")
