import logging
import os
from backend.agents.ingestion import ingest_pdf
from backend.agents.vector_db import build_vector_db
from backend.agents.generation import generate_answer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_generate_answer():
    # Use the sample PDF from earlier steps
    pdf_path = os.path.join("test_data", "ecommerce-full-100products.pdf")
    chunks = ingest_pdf(pdf_path)
    db = build_vector_db(chunks)

    # Run generation on a query
    response = generate_answer(db, "what is the return policy of Science Fiction Novel")

    # Log the response so you can see it in pytest output
    logger.info("Generated answer: %s", response)

    # Validation: response should be a non-empty string
    assert isinstance(response, str)
    assert len(response.strip()) > 0
