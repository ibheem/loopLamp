from backend.agents.telecom_security import TelecomSecurityAgent
from backend.core.documents import Document


def test_telecom_agent_returns_dashboard_ready_report():
    agent = TelecomSecurityAgent()
    documents = [
        Document(
            page_content=(
                "SS7 routing anomaly caused delayed OTP delivery. "
                "Recommended action: isolate the affected partner route. "
                "Policy note: incidents require audit logging and approval before export."
            ),
            metadata={"source": "test_data/telecom_incident.txt", "chunk_index": 0, "file_type": "text"},
        )
    ]

    report = agent.run("What should be done for the SS7 issue?", documents)

    assert report.domain == "telecom_security"
    assert "retrieved context" in report.summary.lower()
    assert any(metric.name == "matched_documents" for metric in report.metrics)
    assert any(insight.severity == "high" for insight in report.insights)
    assert report.recommendations[0].priority >= 1
    assert report.source_refs[0].source.endswith("telecom_incident.txt")
