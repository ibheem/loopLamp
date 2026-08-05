import json
import logging
from typing import Callable, List, Optional

from backend.agents.langchain_domain_config import prompt_guidance_for_domain
from backend.agents.tool_calling_report_agent import ToolCallingReportAgent
from backend.core.documents import Document
from backend.core.models import DomainReport
from backend.services.llm_provider import EvidenceSummary, SourceComparison

logger = logging.getLogger(__name__)

try:  # pragma: no cover - import availability is environment-dependent
    from langchain.agents import create_agent
except Exception:  # pragma: no cover - handled at runtime
    create_agent = None


class LangChainCreateAgentReportAgent(ToolCallingReportAgent):
    def __init__(
        self,
        provider,
        fallback_agent=None,
        domain_name: str = "telecom_security",
        agent_factory: Optional[Callable[..., object]] = None,
    ):
        super().__init__(provider=provider, fallback_agent=fallback_agent, domain_name=domain_name)
        self._agent_factory = agent_factory or create_agent

    def generate_report_from_state(
        self,
        query: str,
        context_documents: List[Document],
        comparison: Optional[SourceComparison] = None,
        evidence_summary: Optional[EvidenceSummary] = None,
    ):
        chat_model = self.provider.build_chat_model() if hasattr(self.provider, "build_chat_model") else None
        if (
            not context_documents
            or not self.provider.is_available()
            or self._agent_factory is None
            or chat_model is None
        ):
            return super().generate_report_from_state(
                query,
                context_documents,
                comparison=comparison,
                evidence_summary=evidence_summary,
            )

        try:
            agent = self._agent_factory(
                model=chat_model,
                tools=self._build_agent_tools(context_documents, comparison, evidence_summary),
                system_prompt=self._build_system_prompt(),
                response_format=DomainReport,
                name=f"{self.name}_structured_agent",
            )
            result = agent.invoke(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": self._build_user_prompt(
                                query=query,
                                context_documents=context_documents,
                                comparison=comparison,
                                evidence_summary=evidence_summary,
                            ),
                        }
                    ]
                }
            )
            report = self._extract_report(result)
            self._capture_agent_result(result, comparison=comparison, evidence_summary=evidence_summary)
            self._last_provider_mode = f"{getattr(self.provider, 'provider_id', 'langchain')}_agent"
            self._last_provider_model = getattr(self.provider, "model", "")
            self._last_used_fallback = False
            return self._normalize_report(
                report,
                len(context_documents),
                self._build_source_refs(context_documents),
            )
        except Exception as exc:
            logger.warning(
                "langchain_create_agent_fallback domain=%s error=%s",
                self.name,
                exc.__class__.__name__,
            )
            self._last_agent_trace["steps"].append(
                {
                    "label": "LangChain Agent",
                    "detail": "LangChain create_agent generation failed, so the provider fallback path was used.",
                    "status": "warning",
                }
            )
            return super().generate_report_from_state(
                query,
                context_documents,
                comparison=comparison,
                evidence_summary=evidence_summary,
            )

    def _build_agent_tools(
        self,
        context_documents: List[Document],
        comparison: Optional[SourceComparison],
        evidence_summary: Optional[EvidenceSummary],
    ) -> List[Callable[..., str]]:
        source_payload = [
            {
                "source": str((document.metadata or {}).get("source", "unknown")),
                "chunk_index": (document.metadata or {}).get("chunk_index"),
                "file_type": (document.metadata or {}).get("file_type"),
                "content": document.page_content,
            }
            for document in context_documents
        ]
        comparison_payload = (
            comparison.model_dump() if comparison is not None and hasattr(comparison, "model_dump") else comparison
        )
        evidence_payload = (
            evidence_summary.model_dump()
            if evidence_summary is not None and hasattr(evidence_summary, "model_dump")
            else evidence_summary
        )

        def review_retrieved_sources() -> str:
            """Review the currently retrieved grounded source chunks before finalizing the report."""

            return json.dumps(source_payload, ensure_ascii=False)

        def review_source_comparison() -> str:
            """Review the cross-source comparison summary if one is available."""

            return json.dumps(comparison_payload, ensure_ascii=False) if comparison_payload is not None else "null"

        def review_evidence_summary() -> str:
            """Review the synthesized evidence summary if one is available."""

            return json.dumps(evidence_payload, ensure_ascii=False) if evidence_payload is not None else "null"

        return [review_retrieved_sources, review_source_comparison, review_evidence_summary]

    def _build_system_prompt(self) -> str:
        domain_name = self.name.replace("_", " ")
        return (
            f"You are a {domain_name} reporting agent.\n"
            "Use the available tools when they help you inspect grounded evidence before finalizing the answer.\n"
            "Return only information grounded in the retrieved evidence.\n"
            "The final response must satisfy the DomainReport schema.\n"
            "The summary must begin with the exact phrase 'Based on the retrieved context,'.\n"
            "Include at least 2 concise grounded insights and at least 2 grounded recommendations.\n"
            + self._domain_prompt_guidance()
            + "Do not invent source references or unsupported remediation steps."
        )

    def _build_user_prompt(
        self,
        query: str,
        context_documents: List[Document],
        comparison: Optional[SourceComparison],
        evidence_summary: Optional[EvidenceSummary],
    ) -> str:
        comparison_note = (
            comparison.summary
            if comparison is not None and getattr(comparison, "summary", "")
            else "No source comparison summary is available yet."
        )
        evidence_note = (
            evidence_summary.summary
            if evidence_summary is not None and getattr(evidence_summary, "summary", "")
            else "No evidence synthesis summary is available yet."
        )
        return (
            f"User query: {query}\n"
            f"Retrieved chunk count: {len(context_documents)}\n"
            f"Source comparison note: {comparison_note}\n"
            f"Evidence synthesis note: {evidence_note}\n"
            f"Inspect the available tools as needed, then produce the final {self.name.replace('_', ' ')} DomainReport."
        )

    def _extract_report(self, result) -> DomainReport:
        payload = result.get("structured_response") if isinstance(result, dict) else None
        if payload is None:
            raise RuntimeError("LangChain agent did not return a structured_response payload.")
        if isinstance(payload, DomainReport):
            return payload
        if isinstance(payload, dict):
            if hasattr(DomainReport, "model_validate"):
                return DomainReport.model_validate(payload)
            return DomainReport.parse_obj(payload)
        raise RuntimeError("LangChain agent returned an unsupported structured_response payload.")

    def _capture_agent_result(
        self,
        result,
        comparison: Optional[SourceComparison],
        evidence_summary: Optional[EvidenceSummary],
    ) -> None:
        messages = result.get("messages", []) if isinstance(result, dict) else []
        tool_call_count = 0
        for message in messages:
            tool_call_count += len(getattr(message, "tool_calls", []) or [])

        self._last_tool_calls = max(self._last_tool_calls, tool_call_count)
        self._last_agent_loop = "langchain_create_agent"
        detail = "LangChain create_agent generated the final structured report."
        if tool_call_count:
            detail = f"LangChain create_agent generated the final structured report after {tool_call_count} tool call(s)."
        self._last_agent_trace["steps"].append(
            {
                "label": "LangChain Agent",
                "detail": detail,
                "status": "success",
            }
        )
        if comparison is not None and not self._last_agent_trace.get("comparison_summary"):
            self._last_agent_trace["comparison_summary"] = comparison.summary
        if evidence_summary is not None and not self._last_agent_trace.get("summary_digest"):
            self._last_agent_trace["summary_digest"] = evidence_summary.summary

    def _domain_prompt_guidance(self) -> str:
        return prompt_guidance_for_domain(self.name)
