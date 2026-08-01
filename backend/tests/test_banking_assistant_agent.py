from backend.agents.banking_assistant import BankingAssistantAgent
from backend.core.documents import Document


def test_banking_assistant_agent_returns_dashboard_ready_report():
    agent = BankingAssistantAgent()
    documents = [
        Document(
            page_content=(
                "ATM withdrawal limits apply to debit cards. Failed ATM debit complaints require "
                "transaction reference logging. Duplicate statements may attract a service charge."
            ),
            metadata={"source": "test_data/banking_assistant/atm_notice.txt", "chunk_index": 0, "file_type": "txt"},
        )
    ]

    report = agent.run("Explain the ATM complaint and charges guidance.", documents)

    assert report.domain == "banking_assistant"
    assert "retrieved context" in report.summary.lower()
    assert report.metrics
    assert report.insights
    assert report.recommendations
    assert report.source_refs[0].source.endswith("atm_notice.txt")
