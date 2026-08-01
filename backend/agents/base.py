from abc import ABC, abstractmethod
from typing import Callable, Dict, List, Optional, Tuple

from backend.core.documents import Document
from backend.core.models import DomainReport
from backend.services.llm_provider import EvidenceReview, EvidenceSummary, RetrievalPlan, SourceComparison


RetrieveTool = Callable[[str, int], List[Document]]


class DomainAgent(ABC):
    name: str

    @abstractmethod
    def run(self, query: str, context_documents: List[Document]) -> DomainReport:
        raise NotImplementedError

    def run_with_tools(
        self,
        query: str,
        context_documents: List[Document],
        retrieve_tool: Optional[RetrieveTool] = None,
    ) -> Tuple[DomainReport, List[Document]]:
        return self.run(query, context_documents), list(context_documents)

    def begin_workflow(self, query: str, context_documents: List[Document]) -> None:
        return None

    def plan_retrieval(self, query: str, context_documents: List[Document]) -> Optional[RetrievalPlan]:
        return None

    def record_tool_result(
        self,
        query: str,
        prior_documents: List[Document],
        retrieved_documents: List[Document],
        merged_documents: List[Document],
    ) -> None:
        return None

    def inspect_evidence(self, query: str, context_documents: List[Document]) -> Optional[EvidenceReview]:
        return None

    def compare_sources(self, query: str, context_documents: List[Document]) -> Optional[SourceComparison]:
        return None

    def summarize_evidence(self, query: str, context_documents: List[Document]) -> Optional[EvidenceSummary]:
        return None

    def generate_report(self, query: str, context_documents: List[Document]) -> DomainReport:
        return self.run(query, context_documents)

    def generate_report_from_state(
        self,
        query: str,
        context_documents: List[Document],
        comparison: Optional[SourceComparison] = None,
        evidence_summary: Optional[EvidenceSummary] = None,
    ) -> DomainReport:
        return self.generate_report(query, context_documents)

    def runtime_metadata(self) -> Dict[str, object]:
        return {
            "agent_type": self.__class__.__name__,
            "provider_mode": "deterministic",
            "provider_model": "",
            "used_fallback": "false",
            "tool_calls": 0,
            "agent_loop": "retrieve_generate",
            "agent_trace": {
                "planned_query": "",
                "plan_rationale": "",
                "comparison_summary": "",
                "evidence_summary": "",
                "summary_digest": "",
                "grounded": False,
                "added_sources": [],
                "steps": [],
            },
        }
