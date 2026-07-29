from backend.agents.financial_risk import FinancialRiskAgent
from backend.core.documents import Document


def test_financial_risk_agent_returns_dashboard_ready_report():
    agent = FinancialRiskAgent()
    documents = [
        Document(
            page_content=(
                "Procurement guidelines require documented approvals and audit controls. "
                "Financial accountability and record-keeping rules must be followed."
            ),
            metadata={"source": "test_data/finance/FInal_GFR_upto_31_07_2024.pdf", "chunk_index": 0, "file_type": "pdf"},
        )
    ]

    report = agent.run("Summarize procurement risk guidelines.", documents)

    assert report.domain == "financial_risk"
    assert "retrieved context" in report.summary.lower()
    assert report.metrics
    assert report.insights
    assert report.recommendations
    assert report.source_refs[0].source.endswith("FInal_GFR_upto_31_07_2024.pdf")
