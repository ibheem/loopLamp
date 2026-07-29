import json
import logging
import os
from abc import ABC, abstractmethod
from typing import List, Optional

from backend.core.documents import Document
from backend.core.models import DomainReport, DomainSourceRef

logger = logging.getLogger(__name__)

try:  # pragma: no cover - exercised through fake providers in tests
    from openai import OpenAI
except Exception:  # pragma: no cover - import failure handled at runtime
    OpenAI = None


class ProviderUnavailableError(RuntimeError):
    pass


class ReportLLMProvider(ABC):
    @abstractmethod
    def is_available(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def generate_report(
        self,
        domain: str,
        query: str,
        context_documents: List[Document],
        source_refs: List[DomainSourceRef],
    ) -> DomainReport:
        raise NotImplementedError


def _domain_report_schema() -> dict:
    if hasattr(DomainReport, "model_json_schema"):
        return DomainReport.model_json_schema()
    return DomainReport.schema()


def _domain_report_from_json(payload: str) -> DomainReport:
    if hasattr(DomainReport, "model_validate_json"):
        return DomainReport.model_validate_json(payload)
    return DomainReport.parse_raw(payload)


class OpenAIResponsesReportProvider(ReportLLMProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-5-mini",
        escalation_model: str = "gpt-5.1",
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.escalation_model = escalation_model
        self._client = OpenAI(api_key=self.api_key) if OpenAI is not None and self.api_key else None

    def is_available(self) -> bool:
        return self._client is not None

    def generate_report(
        self,
        domain: str,
        query: str,
        context_documents: List[Document],
        source_refs: List[DomainSourceRef],
    ) -> DomainReport:
        if not self.is_available():
            raise ProviderUnavailableError("OpenAI provider is unavailable. Set OPENAI_API_KEY to enable it.")

        prompt = self._build_prompt(domain=domain, query=query, context_documents=context_documents, source_refs=source_refs)

        last_error = None
        for model_name in (self.model, self.escalation_model):
            try:
                logger.info("llm_report_generation model=%s domain=%s docs=%s", model_name, domain, len(context_documents))
                response = self._client.responses.create(
                    model=model_name,
                    input=prompt,
                    text={
                        "format": {
                            "type": "json_schema",
                            "name": "domain_report",
                            "schema": _domain_report_schema(),
                        }
                    },
                )
                payload = response.output_text
                report = _domain_report_from_json(payload)
                return report
            except Exception as exc:  # pragma: no cover - live API not exercised in tests
                last_error = exc
                logger.warning(
                    "llm_report_generation_failed model=%s domain=%s error=%s",
                    model_name,
                    domain,
                    exc.__class__.__name__,
                )

        raise RuntimeError("OpenAI report generation failed") from last_error

    def _build_prompt(
        self,
        domain: str,
        query: str,
        context_documents: List[Document],
        source_refs: List[DomainSourceRef],
    ) -> str:
        context_blocks = []
        for index, document in enumerate(context_documents, start=1):
            context_blocks.append(
                "Source {index}\nMetadata: {metadata}\nContent: {content}".format(
                    index=index,
                    metadata=json.dumps(document.metadata, sort_keys=True),
                    content=document.page_content,
                )
            )

        source_payload = [source_ref.dict() for source_ref in source_refs]
        return (
            "You are a domain reporting agent.\n"
            "Return only data that can be grounded in the supplied context.\n"
            "Respond with a JSON object matching the provided schema.\n"
            "Keep insights concise, dashboard-ready, and non-redundant.\n\n"
            f"Domain: {domain}\n"
            f"User query: {query}\n"
            f"Available source refs: {json.dumps(source_payload)}\n\n"
            "Context:\n"
            + "\n\n".join(context_blocks)
        )
