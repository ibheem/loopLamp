from backend.agents.automotive import AutomotiveAgent
from backend.core.documents import Document


def test_automotive_agent_returns_dashboard_ready_report():
    agent = AutomotiveAgent()
    documents = [
        Document(
            page_content=(
                "DTC P0420 requires validation before parts replacement. Brake inspection should "
                "check pads and rotors. Maintenance interval work includes coolant checks."
            ),
            metadata={"source": "test_data/automotive/service_manual.txt", "chunk_index": 0, "file_type": "txt"},
        )
    ]

    report = agent.run("What should be checked for a brake-related warning?", documents)

    assert report.domain == "automotive"
    assert "retrieved context" in report.summary.lower()
    assert report.metrics
    assert report.insights
    assert report.recommendations
    assert report.source_refs[0].source.endswith("service_manual.txt")
