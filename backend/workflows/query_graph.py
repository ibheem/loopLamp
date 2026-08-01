import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from backend.core.documents import Document
from backend.core.models import DomainReport, QueryRequest
from backend.guards.execution import GuardedExecutionResult
from backend.services.llm_provider import EvidenceReview, EvidenceSummary, RetrievalPlan, SourceComparison

logger = logging.getLogger(__name__)

try:  # pragma: no cover - covered through fallback in current environment
    from langgraph.graph import END, StateGraph
except Exception:  # pragma: no cover - covered through fallback tests
    END = None
    StateGraph = None


@dataclass
class QueryWorkflowState:
    request: QueryRequest
    agent: Any
    vector_db: Any
    current_k: int
    max_attempts: int
    attempts: int = 0
    used_reflection: bool = False
    sources: Optional[List[Document]] = None
    report: Optional[DomainReport] = None
    plan: Optional[RetrievalPlan] = None
    comparison: Optional[SourceComparison] = None
    evidence_summary: Optional[EvidenceSummary] = None
    evidence_review: Optional[EvidenceReview] = None
    runtime_metadata: Dict[str, Any] = field(default_factory=dict)


def _report_is_grounded(report: Optional[DomainReport], sources: Optional[List[Document]]) -> bool:
    if report is None or not sources:
        return False
    lowered = report.summary.lower()
    return "retrieved context" in lowered


class QueryGraphWorkflow:
    def __init__(self, retrieval_service):
        self.retrieval_service = retrieval_service
        self.backend_name = "langgraph" if StateGraph is not None else "fallback"
        self._compiled_graph = self._build_graph() if StateGraph is not None else None

    def run(self, agent, vector_db, request: QueryRequest, max_attempts: int = 2) -> GuardedExecutionResult:
        state = QueryWorkflowState(
            request=request,
            agent=agent,
            vector_db=vector_db,
            current_k=request.max_results,
            max_attempts=max_attempts,
        )
        final_state = self._invoke(state)
        if final_state.report is None:
            final_state.report = DomainReport(domain=agent.name, summary="No answer generated")
        return GuardedExecutionResult(
            answer=final_state.report,
            attempts=final_state.attempts,
            used_reflection=final_state.used_reflection,
            sources=final_state.sources or [],
            runtime_metadata=final_state.runtime_metadata,
        )

    def _invoke(self, state: QueryWorkflowState) -> QueryWorkflowState:
        if self._compiled_graph is None:
            logger.info("workflow_graph_backend backend=fallback")
            return self._fallback_invoke(state)

        logger.info("workflow_graph_backend backend=langgraph")
        payload = self._compiled_graph.invoke(self._to_payload(state))
        return self._from_payload(payload)

    def _fallback_invoke(self, state: QueryWorkflowState) -> QueryWorkflowState:
        while True:
            state = self._retrieve_node(state)
            state = self._plan_node(state)
            if self._plan_next_step(state) == "retrieve_sources":
                state = self._retrieve_sources_node(state)
            state = self._compare_sources_node(state)
            state = self._summarize_evidence_node(state)
            state = self._inspect_node(state)
            state = self._generate_node(state)
            next_step = self._next_step(state)
            if next_step == "finish":
                return self._finish_node(state)
            state = self._reflect_node(state)

    def _build_graph(self):
        graph = StateGraph(dict)
        graph.add_node("retrieve", self._retrieve_payload_node)
        graph.add_node("plan", self._plan_payload_node)
        graph.add_node("retrieve_sources", self._retrieve_sources_payload_node)
        graph.add_node("compare_sources", self._compare_sources_payload_node)
        graph.add_node("summarize_evidence", self._summarize_evidence_payload_node)
        graph.add_node("inspect", self._inspect_payload_node)
        graph.add_node("generate", self._generate_payload_node)
        graph.add_node("reflect", self._reflect_payload_node)
        graph.add_node("finish", self._finish_payload_node)
        graph.set_entry_point("retrieve")
        graph.add_edge("retrieve", "plan")
        graph.add_conditional_edges(
            "plan",
            self._plan_payload_step,
            {"retrieve_sources": "retrieve_sources", "compare_sources": "compare_sources"},
        )
        graph.add_edge("retrieve_sources", "compare_sources")
        graph.add_edge("compare_sources", "summarize_evidence")
        graph.add_edge("summarize_evidence", "inspect")
        graph.add_edge("inspect", "generate")
        graph.add_conditional_edges(
            "generate",
            self._next_payload_step,
            {"retry": "reflect", "finish": "finish"},
        )
        graph.add_edge("reflect", "retrieve")
        graph.add_edge("finish", END)
        return graph.compile()

    def _retrieve_node(self, state: QueryWorkflowState) -> QueryWorkflowState:
        state.attempts += 1
        state.sources = self.retrieval_service.retrieve(
            state.vector_db,
            state.request.query,
            k=state.current_k,
        )
        state.plan = None
        state.comparison = None
        state.evidence_summary = None
        state.evidence_review = None
        begin_workflow = getattr(state.agent, "begin_workflow", None)
        if callable(begin_workflow):
            begin_workflow(state.request.query, state.sources or [])
        return state

    def _plan_node(self, state: QueryWorkflowState) -> QueryWorkflowState:
        planner = getattr(state.agent, "plan_retrieval", None)
        if callable(planner):
            state.plan = planner(state.request.query, state.sources or [])
        else:
            state.plan = None
        return state

    def _retrieve_sources_node(self, state: QueryWorkflowState) -> QueryWorkflowState:
        if state.plan is None:
            return state
        plan_query = getattr(state.plan, "search_query", "")
        max_results = getattr(state.plan, "max_results", 0) or max(len(state.sources or []) + 1, 2)
        retrieved_documents = self.retrieval_service.retrieve(
            state.vector_db,
            plan_query,
            k=max_results,
        )
        prior_documents = list(state.sources or [])
        state.sources = self._merge_documents(prior_documents, retrieved_documents)
        recorder = getattr(state.agent, "record_tool_result", None)
        if callable(recorder):
            recorder(state.request.query, prior_documents, retrieved_documents, state.sources)
        return state

    def _compare_sources_node(self, state: QueryWorkflowState) -> QueryWorkflowState:
        if not self._should_compare_sources(state):
            state.comparison = None
            return state

        comparator = getattr(state.agent, "compare_sources", None)
        if callable(comparator):
            state.comparison = comparator(state.request.query, state.sources or [])
        else:
            state.comparison = None
        return state

    def _summarize_evidence_node(self, state: QueryWorkflowState) -> QueryWorkflowState:
        if not self._should_summarize_evidence(state):
            state.evidence_summary = None
            return state

        summarizer = getattr(state.agent, "summarize_evidence", None)
        if callable(summarizer):
            state.evidence_summary = summarizer(state.request.query, state.sources or [])
        else:
            state.evidence_summary = None
        return state

    def _inspect_node(self, state: QueryWorkflowState) -> QueryWorkflowState:
        inspector = getattr(state.agent, "inspect_evidence", None)
        if callable(inspector):
            state.evidence_review = inspector(state.request.query, state.sources or [])
        else:
            state.evidence_review = None
        return state

    def _generate_node(self, state: QueryWorkflowState) -> QueryWorkflowState:
        generator = getattr(state.agent, "generate_report_from_state", None)
        if callable(generator):
            state.report = generator(
                state.request.query,
                state.sources or [],
                comparison=state.comparison,
                evidence_summary=state.evidence_summary,
            )
        else:
            legacy_generator = getattr(state.agent, "generate_report", None)
            if callable(legacy_generator):
                state.report = legacy_generator(state.request.query, state.sources or [])
            else:
                state.report = state.agent.run(state.request.query, state.sources or [])
        return state

    def _reflect_node(self, state: QueryWorkflowState) -> QueryWorkflowState:
        state.used_reflection = True
        state.current_k += 1
        return state

    def _finish_node(self, state: QueryWorkflowState) -> QueryWorkflowState:
        state.runtime_metadata = state.agent.runtime_metadata() if hasattr(state.agent, "runtime_metadata") else {}
        state.runtime_metadata["plan"] = (
            state.plan.model_dump() if hasattr(state.plan, "model_dump") else state.plan
        )
        state.runtime_metadata["comparison"] = (
            state.comparison.model_dump() if hasattr(state.comparison, "model_dump") else state.comparison
        )
        state.runtime_metadata["evidence_summary"] = (
            state.evidence_summary.model_dump()
            if hasattr(state.evidence_summary, "model_dump")
            else state.evidence_summary
        )
        state.runtime_metadata["inspection"] = (
            state.evidence_review.model_dump()
            if hasattr(state.evidence_review, "model_dump")
            else state.evidence_review
        )
        return state

    def _plan_next_step(self, state: QueryWorkflowState) -> str:
        plan = state.plan
        if plan is not None and getattr(plan, "should_retrieve", False) and getattr(plan, "search_query", "").strip():
            return "retrieve_sources"
        return "compare_sources"

    def _next_step(self, state: QueryWorkflowState) -> str:
        if _report_is_grounded(state.report, state.sources):
            return "finish"
        if state.attempts >= state.max_attempts:
            return "finish"
        return "retry"

    def _merge_documents(self, left: List[Document], right: List[Document]) -> List[Document]:
        merged: List[Document] = []
        seen = set()
        for document in list(left) + list(right):
            metadata = document.metadata or {}
            key = (
                str(metadata.get("source", "")),
                metadata.get("chunk_index"),
                document.page_content,
            )
            if key in seen:
                continue
            seen.add(key)
            merged.append(document)
        return merged

    def _to_payload(self, state: QueryWorkflowState) -> Dict[str, Any]:
        return {
            "request": state.request,
            "agent": state.agent,
            "vector_db": state.vector_db,
            "current_k": state.current_k,
            "max_attempts": state.max_attempts,
            "attempts": state.attempts,
            "used_reflection": state.used_reflection,
            "sources": state.sources,
            "plan": state.plan.model_dump() if hasattr(state.plan, "model_dump") else state.plan,
            "comparison": state.comparison.model_dump() if hasattr(state.comparison, "model_dump") else state.comparison,
            "evidence_summary": (
                state.evidence_summary.model_dump()
                if hasattr(state.evidence_summary, "model_dump")
                else state.evidence_summary
            ),
            "evidence_review": (
                state.evidence_review.model_dump()
                if hasattr(state.evidence_review, "model_dump")
                else state.evidence_review
            ),
            "report": state.report,
            "runtime_metadata": state.runtime_metadata,
        }

    def _from_payload(self, payload: Dict[str, Any]) -> QueryWorkflowState:
        raw_plan = payload.get("plan")
        raw_comparison = payload.get("comparison")
        raw_evidence_summary = payload.get("evidence_summary")
        raw_evidence_review = payload.get("evidence_review")
        return QueryWorkflowState(
            request=payload["request"],
            agent=payload["agent"],
            vector_db=payload["vector_db"],
            current_k=payload["current_k"],
            max_attempts=payload["max_attempts"],
            attempts=payload.get("attempts", 0),
            used_reflection=payload.get("used_reflection", False),
            sources=payload.get("sources"),
            plan=self._coerce_plan(raw_plan),
            comparison=self._coerce_comparison(raw_comparison),
            evidence_summary=self._coerce_evidence_summary(raw_evidence_summary),
            evidence_review=self._coerce_evidence_review(raw_evidence_review),
            report=payload.get("report"),
            runtime_metadata=payload.get("runtime_metadata") or {},
        )

    def _retrieve_payload_node(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        state = self._from_payload(payload)
        state = self._retrieve_node(state)
        return self._to_payload(state)

    def _plan_payload_node(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        state = self._from_payload(payload)
        state = self._plan_node(state)
        return self._to_payload(state)

    def _retrieve_sources_payload_node(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        state = self._from_payload(payload)
        state = self._retrieve_sources_node(state)
        return self._to_payload(state)

    def _compare_sources_payload_node(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        state = self._from_payload(payload)
        state = self._compare_sources_node(state)
        return self._to_payload(state)

    def _summarize_evidence_payload_node(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        state = self._from_payload(payload)
        state = self._summarize_evidence_node(state)
        return self._to_payload(state)

    def _inspect_payload_node(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        state = self._from_payload(payload)
        state = self._inspect_node(state)
        return self._to_payload(state)

    def _generate_payload_node(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        state = self._from_payload(payload)
        state = self._generate_node(state)
        return self._to_payload(state)

    def _reflect_payload_node(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        state = self._from_payload(payload)
        state = self._reflect_node(state)
        return self._to_payload(state)

    def _finish_payload_node(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        state = self._from_payload(payload)
        state = self._finish_node(state)
        return self._to_payload(state)

    def _plan_payload_step(self, payload: Dict[str, Any]) -> str:
        state = self._from_payload(payload)
        return self._plan_next_step(state)

    def _coerce_plan(self, payload: Any) -> Optional[RetrievalPlan]:
        if payload is None or isinstance(payload, RetrievalPlan):
            return payload
        if hasattr(RetrievalPlan, "model_validate"):
            return RetrievalPlan.model_validate(payload)
        return RetrievalPlan.parse_obj(payload)

    def _coerce_evidence_review(self, payload: Any) -> Optional[EvidenceReview]:
        if payload is None or isinstance(payload, EvidenceReview):
            return payload
        if hasattr(EvidenceReview, "model_validate"):
            return EvidenceReview.model_validate(payload)
        return EvidenceReview.parse_obj(payload)

    def _coerce_comparison(self, payload: Any) -> Optional[SourceComparison]:
        if payload is None or isinstance(payload, SourceComparison):
            return payload
        if hasattr(SourceComparison, "model_validate"):
            return SourceComparison.model_validate(payload)
        return SourceComparison.parse_obj(payload)

    def _coerce_evidence_summary(self, payload: Any) -> Optional[EvidenceSummary]:
        if payload is None or isinstance(payload, EvidenceSummary):
            return payload
        if hasattr(EvidenceSummary, "model_validate"):
            return EvidenceSummary.model_validate(payload)
        return EvidenceSummary.parse_obj(payload)

    def _next_payload_step(self, payload: Dict[str, Any]) -> str:
        state = self._from_payload(payload)
        return self._next_step(state)

    def _should_compare_sources(self, state: QueryWorkflowState) -> bool:
        plan = state.plan
        if plan is not None and getattr(plan, "compare_sources", False):
            return True
        unique_sources = {
            str((document.metadata or {}).get("source", "unknown"))
            for document in (state.sources or [])
        }
        return len(state.sources or []) >= 2 or len(unique_sources) >= 2

    def _should_summarize_evidence(self, state: QueryWorkflowState) -> bool:
        plan = state.plan
        if plan is not None and getattr(plan, "summarize_evidence", False):
            return True
        return len(state.sources or []) >= 2
