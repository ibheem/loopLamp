from backend.core.documents import Document
from backend.core.models import DomainReport, QueryRequest
from backend.services.llm_provider import EvidenceReview, EvidenceSummary, RetrievalPlan, SourceComparison
from backend.services.retrieval import RetrievalService
from backend.services.vector_store import InMemoryVectorStore
from backend.workflows.query_graph import QueryGraphWorkflow, QueryWorkflowState


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


class ToolAwareAgent:
    name = "telecom_security"

    def __init__(self):
        self.events = []
        self.last_comparison = None
        self.last_evidence_summary = None

    def begin_workflow(self, query, context_documents):
        self.events.append(("begin", len(context_documents)))

    def plan_retrieval(self, query, context_documents):
        self.events.append(("plan", len(context_documents)))

        class Plan:
            should_retrieve = True
            search_query = "recommended action isolate route"
            max_results = 2
            compare_sources = True
            summarize_evidence = True

        return Plan()

    def record_tool_result(self, query, prior_documents, retrieved_documents, merged_documents):
        self.events.append(("retrieve_sources", len(prior_documents), len(retrieved_documents), len(merged_documents)))

    def compare_sources(self, query, context_documents):
        self.events.append(("compare_sources", len(context_documents)))
        return SourceComparison(
            summary="Compared the issue signal with the recommended action chunk.",
            compared_sources=["a.txt"],
            consensus_points=["The evidence agrees the route should be isolated."],
        )

    def summarize_evidence(self, query, context_documents):
        self.events.append(("summarize_evidence", len(context_documents)))
        return EvidenceSummary(
            summary="Synthesized the action-oriented evidence across the retrieved chunks.",
            key_points=["Isolate the affected route."],
            cited_sources=["a.txt"],
        )

    def inspect_evidence(self, query, context_documents):
        self.events.append(("inspect", len(context_documents)))
        return None

    def generate_report_from_state(self, query, context_documents, comparison=None, evidence_summary=None):
        self.events.append(("generate", len(context_documents)))
        self.last_comparison = comparison
        self.last_evidence_summary = evidence_summary
        return DomainReport(
            domain=self.name,
            summary="Based on the retrieved context, the SS7 route should be isolated.",
        )

    def runtime_metadata(self):
        return {"agent_type": "ToolAwareAgent"}


def test_query_graph_supports_agent_level_retrieval_tool_loop():
    workflow = QueryGraphWorkflow(RetrievalService())
    agent = ToolAwareAgent()
    documents = [
        Document(page_content="ss7 anomaly", metadata={"source": "a.txt", "chunk_index": 0, "file_type": "text"}),
        Document(
            page_content="recommended action isolate route",
            metadata={"source": "a.txt", "chunk_index": 1, "file_type": "text"},
        ),
    ]
    db = InMemoryVectorStore(documents)
    request = QueryRequest(
        query="What should be done for the SS7 route issue?",
        document_path="test_data/telecom_incident.txt",
        domain="telecom_security",
        max_results=1,
    )

    result = workflow.run(agent, db, request)

    assert result.attempts == 1
    assert result.used_reflection is False
    assert "retrieved context" in result.answer.summary.lower()
    assert len(result.sources) == 2
    assert [event[0] for event in agent.events] == [
        "begin",
        "plan",
        "retrieve_sources",
        "compare_sources",
        "summarize_evidence",
        "inspect",
        "generate",
    ]
    assert agent.last_comparison is not None
    assert agent.last_comparison.summary == "Compared the issue signal with the recommended action chunk."
    assert agent.last_evidence_summary is not None
    assert agent.last_evidence_summary.cited_sources == ["a.txt"]


def test_query_graph_runtime_metadata_flows_from_graph_execution():
    workflow = QueryGraphWorkflow(RetrievalService())
    agent = ToolAwareAgent()
    documents = [
        Document(page_content="ss7 anomaly", metadata={"source": "a.txt", "chunk_index": 0, "file_type": "text"}),
        Document(
            page_content="recommended action isolate route",
            metadata={"source": "a.txt", "chunk_index": 1, "file_type": "text"},
        ),
    ]
    db = InMemoryVectorStore(documents)
    request = QueryRequest(
        query="What should be done for the SS7 route issue?",
        document_path="test_data/telecom_incident.txt",
        domain="telecom_security",
        max_results=1,
    )

    result = workflow.run(agent, db, request)

    assert result.runtime_metadata["agent_type"] == "ToolAwareAgent"


def test_query_graph_payload_roundtrip_preserves_typed_plan_and_inspection():
    workflow = QueryGraphWorkflow(RetrievalService())
    state = QueryWorkflowState(
        request=QueryRequest(
            query="What should be done for the SS7 route issue?",
            document_path="test_data/telecom_incident.txt",
            domain="telecom_security",
            max_results=1,
        ),
        agent=ToolAwareAgent(),
        vector_db=InMemoryVectorStore([]),
        current_k=1,
        max_attempts=2,
        plan=RetrievalPlan(
            should_retrieve=True,
            search_query="recommended action isolate route",
            max_results=2,
            rationale="Need a more action-oriented chunk.",
            compare_sources=True,
            summarize_evidence=True,
        ),
        comparison=SourceComparison(
            summary="Both chunks reinforce the same action recommendation.",
            compared_sources=["a.txt"],
            consensus_points=["Isolate the route."],
        ),
        evidence_summary=EvidenceSummary(
            summary="The retrieved evidence now supports the route isolation step.",
            key_points=["Route isolation is explicitly recommended."],
            cited_sources=["a.txt"],
        ),
        evidence_review=EvidenceReview(
            grounded=True,
            summary="The evidence now includes the recommended action.",
        ),
    )

    payload = workflow._to_payload(state)
    restored = workflow._from_payload(payload)

    assert isinstance(restored.plan, RetrievalPlan)
    assert restored.plan.search_query == "recommended action isolate route"
    assert restored.plan.compare_sources is True
    assert isinstance(restored.comparison, SourceComparison)
    assert restored.comparison.summary == "Both chunks reinforce the same action recommendation."
    assert isinstance(restored.evidence_summary, EvidenceSummary)
    assert restored.evidence_summary.cited_sources == ["a.txt"]
    assert isinstance(restored.evidence_review, EvidenceReview)
    assert restored.evidence_review.grounded is True


def test_query_graph_finish_node_captures_runtime_metadata():
    workflow = QueryGraphWorkflow(RetrievalService())
    state = QueryWorkflowState(
        request=QueryRequest(
            query="What should be done for the SS7 route issue?",
            document_path="test_data/telecom_incident.txt",
            domain="telecom_security",
            max_results=1,
        ),
        agent=ToolAwareAgent(),
        vector_db=InMemoryVectorStore([]),
        current_k=1,
        max_attempts=2,
        report=DomainReport(domain="telecom_security", summary="Based on the retrieved context, isolate route."),
        sources=[Document(page_content="route", metadata={"source": "a.txt"})],
    )

    finished = workflow._finish_node(state)

    assert finished.runtime_metadata["agent_type"] == "ToolAwareAgent"
    assert finished.runtime_metadata["comparison"] is None
    assert finished.runtime_metadata["evidence_summary"] is None
