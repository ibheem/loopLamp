from backend.agents.medical_qa import MedicalQAAgent
from backend.core.documents import Document


def test_medical_qa_agent_returns_dashboard_ready_report():
    agent = MedicalQAAgent()
    documents = [
        Document(
            page_content=(
                "Clinical pharmacology discusses drug action, treatment principles, and disease-focused care. "
                "Medication decisions should be validated through clinical review."
            ),
            metadata={"source": "test_data/healthcare/GENERAL PRINCIPLES OF PHARMACOLOGY.pdf", "chunk_index": 0, "file_type": "pdf"},
        )
    ]

    report = agent.run("Explain the pharmacology context for a treatment question.", documents)

    assert report.domain == "medical_qa"
    assert "retrieved context" in report.summary.lower()
    assert report.metrics
    assert report.insights
    assert report.recommendations
    assert report.source_refs[0].source.endswith("GENERAL PRINCIPLES OF PHARMACOLOGY.pdf")
