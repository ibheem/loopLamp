from backend.agents.ingestion import ingest_pdf
import os


def test_ingest_pdf():
    pdf_path = os.path.join("test_data", "ecommerce-full-100products.pdf")
    chunks = ingest_pdf(pdf_path)
    assert len(chunks) > 0
    assert hasattr(chunks[0], "page_content")
    assert "policy" in " ".join(chunk.page_content.lower() for chunk in chunks[:5])
