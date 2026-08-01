from backend.agents.ecommerce import EcommerceAgent
from backend.core.documents import Document


def test_ecommerce_agent_returns_dashboard_ready_report():
    agent = EcommerceAgent()
    documents = [
        Document(
            page_content=(
                "A delayed order may require shipment verification before refund approval. "
                "Opened products can be exchanged if defective under the return policy."
            ),
            metadata={"source": "test_data/ecommerce/customer_issue.txt", "chunk_index": 0, "file_type": "txt"},
        )
    ]

    report = agent.run("What should support do for a delayed order with a refund request?", documents)

    assert report.domain == "ecommerce"
    assert "retrieved context" in report.summary.lower()
    assert report.metrics
    assert report.insights
    assert report.recommendations
    assert report.source_refs[0].source.endswith("customer_issue.txt")
