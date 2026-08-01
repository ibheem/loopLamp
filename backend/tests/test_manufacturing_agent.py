from backend.agents.manufacturing import ManufacturingAgent
from backend.core.documents import Document


def test_manufacturing_agent_returns_dashboard_ready_report():
    agent = ManufacturingAgent()
    documents = [
        Document(
            page_content=(
                "A quality defect requires corrective action ownership before line restart. "
                "Operators should validate the SOP and log deviations in the production record."
            ),
            metadata={"source": "test_data/manufacturing/quality_incident.txt", "chunk_index": 0, "file_type": "txt"},
        )
    ]

    report = agent.run("What should happen after a quality defect is reported?", documents)

    assert report.domain == "manufacturing"
    assert "retrieved context" in report.summary.lower()
    assert report.metrics
    assert report.insights
    assert report.recommendations
    assert report.source_refs[0].source.endswith("quality_incident.txt")
