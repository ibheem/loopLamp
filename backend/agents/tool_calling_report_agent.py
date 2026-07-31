import logging
from typing import List, Optional

from backend.agents.base import RetrieveTool
from backend.agents.openai_report_agent import OpenAIReportAgent
from backend.core.documents import Document
from backend.services.llm_provider import EvidenceReview, RetrievalPlan

logger = logging.getLogger(__name__)


class ToolCallingReportAgent(OpenAIReportAgent):
    def __init__(self, provider, fallback_agent=None, domain_name: str = "telecom_security"):
        super().__init__(provider=provider, fallback_agent=fallback_agent, domain_name=domain_name)
        self._last_tool_calls = 0
        self._last_agent_loop = "retrieve_generate"
        self._last_agent_trace = {
            "planned_query": "",
            "plan_rationale": "",
            "evidence_summary": "",
            "grounded": False,
            "added_sources": [],
            "steps": [],
        }

    def begin_workflow(self, query: str, context_documents: List[Document]) -> None:
        self._last_tool_calls = 0
        self._last_agent_loop = "retrieve_generate"
        self._last_agent_trace = {
            "planned_query": "",
            "plan_rationale": "",
            "evidence_summary": "",
            "grounded": False,
            "added_sources": [],
            "steps": [
                {
                    "label": "Initial Retrieval",
                    "detail": f"Started with {len(context_documents)} retrieved evidence chunk(s).",
                    "status": "info",
                }
            ],
        }

    def plan_retrieval(self, query: str, context_documents: List[Document]) -> Optional[RetrievalPlan]:
        if not context_documents or not self.provider.is_available():
            return None

        source_refs = self._build_source_refs(context_documents)
        try:
            plan = self.provider.plan_retrieval(
                domain=self.name,
                query=query,
                context_documents=context_documents,
                source_refs=source_refs,
            )
        except Exception as exc:
            logger.warning(
                "agent_plan_failed domain=%s error=%s",
                self.name,
                exc.__class__.__name__,
            )
            return None

        if plan is None or not plan.should_retrieve or not plan.search_query.strip():
            logger.info("agent_tool_plan_skipped domain=%s", self.name)
            return None

        self._last_agent_trace["planned_query"] = plan.search_query
        self._last_agent_trace["plan_rationale"] = plan.rationale
        self._last_agent_trace["steps"].append(
            {
                "label": "Plan",
                "detail": plan.rationale or "The agent decided to refine retrieval with a more targeted query.",
                "status": "info",
            }
        )
        return plan

    def record_tool_result(
        self,
        query: str,
        prior_documents: List[Document],
        retrieved_documents: List[Document],
        merged_documents: List[Document],
    ) -> None:
        self._last_tool_calls = 1
        self._last_agent_loop = "plan_retrieve_inspect_generate"
        added_sources = self._added_source_names(prior_documents, retrieved_documents)
        self._last_agent_trace["added_sources"] = added_sources
        self._last_agent_trace["steps"].append(
            {
                "label": "Tool Call",
                "detail": (
                    f"Retrieve tool added {len(added_sources)} source(s): {', '.join(added_sources)}."
                    if added_sources
                    else "Retrieve tool ran but did not add any new sources."
                ),
                "status": "success" if added_sources else "warning",
            }
        )

    def inspect_evidence(self, query: str, context_documents: List[Document]) -> Optional[EvidenceReview]:
        if not context_documents or not self.provider.is_available():
            return None

        try:
            inspection = self.provider.inspect_evidence(
                domain=self.name,
                query=query,
                context_documents=context_documents,
                source_refs=self._build_source_refs(context_documents),
            )
        except Exception as exc:
            logger.warning(
                "agent_evidence_review_failed domain=%s error=%s",
                self.name,
                exc.__class__.__name__,
            )
            self._last_agent_trace["steps"].append(
                {
                    "label": "Evidence Review",
                    "detail": "Evidence review failed, so the agent continued with the available retrieved context.",
                    "status": "warning",
                }
            )
            return None

        if inspection is not None:
            self._last_agent_trace["evidence_summary"] = inspection.summary
            self._last_agent_trace["grounded"] = inspection.grounded
            self._last_agent_trace["steps"].append(
                {
                    "label": "Evidence Review",
                    "detail": inspection.summary or "Evidence review completed.",
                    "status": "success" if inspection.grounded else "warning",
                }
            )
            logger.info(
                "agent_evidence_review domain=%s grounded=%s summary=%s",
                self.name,
                inspection.grounded,
                inspection.summary,
            )
        return inspection

    def generate_report(self, query: str, context_documents: List[Document]):
        report = self.run(query, context_documents)
        self._last_agent_trace["steps"].append(
            {
                "label": "Generate",
                "detail": f"Generated the final {self.name.replace('_', ' ')} report from {len(context_documents)} chunk(s).",
                "status": "success",
            }
        )
        return report

    def run_with_tools(
        self,
        query: str,
        context_documents: List[Document],
        retrieve_tool: RetrieveTool = None,
    ):
        working_documents = list(context_documents)
        self.begin_workflow(query, working_documents)

        if not working_documents or retrieve_tool is None or not self.provider.is_available():
            return self.generate_report(query, working_documents), working_documents

        plan = self.plan_retrieval(query, working_documents)
        if plan is None:
            return self.generate_report(query, working_documents), working_documents

        max_results = plan.max_results or max(len(working_documents) + 1, 2)
        logger.info(
            "agent_tool_call domain=%s tool=retrieve search_query=%s max_results=%s",
            self.name,
            plan.search_query,
            max_results,
        )
        retrieved_documents = retrieve_tool(plan.search_query, max_results)
        merged_documents = self._merge_documents(working_documents, retrieved_documents)
        self.record_tool_result(query, working_documents, retrieved_documents, merged_documents)
        self.inspect_evidence(query, merged_documents)
        return self.generate_report(query, merged_documents), merged_documents

    def runtime_metadata(self):
        metadata = super().runtime_metadata()
        metadata["tool_calls"] = self._last_tool_calls
        metadata["agent_loop"] = self._last_agent_loop
        metadata["agent_trace"] = dict(self._last_agent_trace)
        return metadata

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

    def _added_source_names(self, left: List[Document], right: List[Document]) -> List[str]:
        existing_keys = {
            (
                str((document.metadata or {}).get("source", "")),
                (document.metadata or {}).get("chunk_index"),
                document.page_content,
            )
            for document in left
        }
        added_sources: List[str] = []
        seen_sources = set()
        for document in right:
            metadata = document.metadata or {}
            key = (
                str(metadata.get("source", "")),
                metadata.get("chunk_index"),
                document.page_content,
            )
            if key in existing_keys:
                continue
            source_name = str(metadata.get("source", "unknown")).split("/")[-1]
            if source_name in seen_sources:
                continue
            seen_sources.add(source_name)
            added_sources.append(source_name)
        return added_sources
