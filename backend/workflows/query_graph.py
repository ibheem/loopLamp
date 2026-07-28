import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from backend.core.documents import Document
from backend.core.models import DomainReport, QueryRequest
from backend.guards.execution import GuardedExecutionResult

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
            state = self._generate_node(state)
            next_step = self._next_step(state)
            if next_step == "finish":
                return state
            state.used_reflection = True
            state.current_k += 1

    def _build_graph(self):
        graph = StateGraph(dict)
        graph.add_node("retrieve", self._retrieve_payload_node)
        graph.add_node("generate", self._generate_payload_node)
        graph.set_entry_point("retrieve")
        graph.add_edge("retrieve", "generate")
        graph.add_conditional_edges(
            "generate",
            self._next_payload_step,
            {"retry": "retrieve", "finish": END},
        )
        return graph.compile()

    def _retrieve_node(self, state: QueryWorkflowState) -> QueryWorkflowState:
        state.attempts += 1
        state.sources = self.retrieval_service.retrieve(
            state.vector_db,
            state.request.query,
            k=state.current_k,
        )
        return state

    def _generate_node(self, state: QueryWorkflowState) -> QueryWorkflowState:
        state.report = state.agent.run(state.request.query, state.sources or [])
        return state

    def _next_step(self, state: QueryWorkflowState) -> str:
        if _report_is_grounded(state.report, state.sources):
            return "finish"
        if state.attempts >= state.max_attempts:
            return "finish"
        return "retry"

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
            "report": state.report,
        }

    def _from_payload(self, payload: Dict[str, Any]) -> QueryWorkflowState:
        return QueryWorkflowState(
            request=payload["request"],
            agent=payload["agent"],
            vector_db=payload["vector_db"],
            current_k=payload["current_k"],
            max_attempts=payload["max_attempts"],
            attempts=payload.get("attempts", 0),
            used_reflection=payload.get("used_reflection", False),
            sources=payload.get("sources"),
            report=payload.get("report"),
        )

    def _retrieve_payload_node(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        state = self._from_payload(payload)
        state = self._retrieve_node(state)
        return self._to_payload(state)

    def _generate_payload_node(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        state = self._from_payload(payload)
        state = self._generate_node(state)
        next_step = self._next_step(state)
        if next_step == "retry":
            state.used_reflection = True
            state.current_k += 1
        return self._to_payload(state)

    def _next_payload_step(self, payload: Dict[str, Any]) -> str:
        state = self._from_payload(payload)
        return self._next_step(state)
