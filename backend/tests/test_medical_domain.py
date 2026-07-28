import os

import pytest

from backend.app.main import dashboard_report, query_documents
from backend.core.models import QueryRequest


pytest.importorskip("pypdf")


def test_medical_query_endpoint_with_healthcare_pdf():
    response = query_documents(
        QueryRequest(
            query="Summarize the pharmacology principles relevant to medication use.",
            document_path=os.path.join("test_data", "healthcare", "GENERAL PRINCIPLES OF PHARMACOLOGY.pdf"),
            domain="medical_qa",
            max_results=2,
        )
    )

    assert response.domain == "medical_qa"
    assert response.report.domain == "medical_qa"
    assert response.report.metrics
    assert response.sources


def test_medical_dashboard_endpoint_with_healthcare_pdf():
    response = dashboard_report(
        QueryRequest(
            query="What clinical guidance is present in the medical source?",
            document_path=os.path.join("test_data", "healthcare", "Harrison_s Principles of Internal Medicine.pdf"),
            domain="medical_qa",
            max_results=2,
        )
    )

    assert response.domain == "medical_qa"
    assert response.title == "Medical Qa Dashboard Report"
    assert response.source_count > 0
