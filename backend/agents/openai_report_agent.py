import logging
from typing import List

from backend.agents.base import DomainAgent
from backend.agents.telecom_security import TelecomSecurityAgent
from backend.core.documents import Document
from backend.core.models import DomainMetric, DomainReport, DomainSourceRef
from backend.services.llm_provider import ProviderUnavailableError, ReportLLMProvider

logger = logging.getLogger(__name__)


class OpenAIReportAgent(DomainAgent):
    name = "telecom_security"

    def __init__(self, provider: ReportLLMProvider, fallback_agent: DomainAgent = None):
        self.provider = provider
        self.fallback_agent = fallback_agent or TelecomSecurityAgent()

    def run(self, query: str, context_documents: List[Document]) -> DomainReport:
        if not context_documents:
            return self.fallback_agent.run(query, context_documents)

        source_refs = self._build_source_refs(context_documents)

        try:
            report = self.provider.generate_report(
                domain=self.name,
                query=query,
                context_documents=context_documents,
                source_refs=source_refs,
            )
            return self._normalize_report(report, len(context_documents), source_refs)
        except ProviderUnavailableError:
            logger.info("llm_agent_fallback reason=provider_unavailable domain=%s", self.name)
            return self.fallback_agent.run(query, context_documents)
        except Exception as exc:
            logger.warning(
                "llm_agent_fallback reason=generation_failure domain=%s error=%s",
                self.name,
                exc.__class__.__name__,
            )
            return self.fallback_agent.run(query, context_documents)

    def _build_source_refs(self, context_documents: List[Document]) -> List[DomainSourceRef]:
        return [
            DomainSourceRef(
                source=str(document.metadata.get("source", "unknown")),
                chunk_index=document.metadata.get("chunk_index"),
                file_type=document.metadata.get("file_type"),
            )
            for document in context_documents[:3]
        ]

    def _normalize_report(
        self,
        report: DomainReport,
        document_count: int,
        source_refs: List[DomainSourceRef],
    ) -> DomainReport:
        if hasattr(report, "model_copy"):
            normalized = report.model_copy(deep=True)
        else:
            normalized = report.copy(deep=True)
        normalized.domain = self.name
        if not normalized.metrics:
            normalized.metrics = [DomainMetric(name="matched_documents", value=str(document_count), unit="documents")]
        if not normalized.source_refs:
            normalized.source_refs = source_refs
        return normalized
