from backend.core.documents import Document
from backend.core.models import DomainReport, QueryRequest
from backend.services.retrieval import RetrievalService
from backend.services.vector_store import InMemoryVectorStore
from backend.workflows.query_graph import QueryGraphWorkflow


class GroundedOnSecondAttemptAgent:
    name = "telecom_security"

    def run(self, query, context_documents):
        if len(context_documents) < 2:
            return DomainReport(
                domain=self.name,
                summary="Need more evidence before I can answer confidently.",
            )
        return DomainReport(
            domain=self.name,
            summary="Based on the retrieved context, the SS7 route should be isolated.",
        )


def test_query_graph_fallback_retries_until_grounded():
    workflow = QueryGraphWorkflow(RetrievalService())
    documents = [
        Document(page_content="ss7 anomaly", metadata={"source": "a.txt", "chunk_index": 0, "file_type": "text"}),
        Document(page_content="recommended action isolate route", metadata={"source": "a.txt", "chunk_index": 1, "file_type": "text"}),
    ]
    db = InMemoryVectorStore(documents)
    request = QueryRequest(
        query="What should be done for the SS7 route issue?",
        document_path="test_data/telecom_incident.txt",
        domain="telecom_security",
        max_results=1,
    )

    result = workflow.run(GroundedOnSecondAttemptAgent(), db, request)

    assert workflow.backend_name in {"fallback", "langgraph"}
    assert result.attempts == 2
    assert result.used_reflection is True
    assert "retrieved context" in result.answer.summary.lower()
    assert len(result.sources) >= 2
