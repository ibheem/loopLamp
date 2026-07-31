import json
import logging
import os
from abc import ABC, abstractmethod
from typing import List, Optional

from pydantic import BaseModel, Field

from backend.core.documents import Document
from backend.core.models import DomainReport, DomainSourceRef

logger = logging.getLogger(__name__)

try:  # pragma: no cover - exercised through fake providers in tests
    from openai import OpenAI
except Exception:  # pragma: no cover - import failure handled at runtime
    OpenAI = None


class ProviderUnavailableError(RuntimeError):
    pass


class RetrievalPlan(BaseModel):
    should_retrieve: bool = False
    search_query: str = ""
    max_results: int = Field(default=0, ge=0, le=10)
    rationale: str = ""


class EvidenceReview(BaseModel):
    grounded: bool = False
    summary: str = ""


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

    def plan_retrieval(
        self,
        domain: str,
        query: str,
        context_documents: List[Document],
        source_refs: List[DomainSourceRef],
    ) -> Optional[RetrievalPlan]:
        return None

    def inspect_evidence(
        self,
        domain: str,
        query: str,
        context_documents: List[Document],
        source_refs: List[DomainSourceRef],
    ) -> Optional[EvidenceReview]:
        return None


def _domain_report_schema() -> dict:
    if hasattr(DomainReport, "model_json_schema"):
        return DomainReport.model_json_schema()
    return DomainReport.schema()


def _domain_report_from_json(payload: str) -> DomainReport:
    if hasattr(DomainReport, "model_validate_json"):
        return DomainReport.model_validate_json(payload)
    return DomainReport.parse_raw(payload)


def _retrieval_plan_schema() -> dict:
    if hasattr(RetrievalPlan, "model_json_schema"):
        return RetrievalPlan.model_json_schema()
    return RetrievalPlan.schema()


def _retrieval_plan_from_json(payload: str) -> RetrievalPlan:
    if hasattr(RetrievalPlan, "model_validate_json"):
        return RetrievalPlan.model_validate_json(payload)
    return RetrievalPlan.parse_raw(payload)


def _evidence_review_schema() -> dict:
    if hasattr(EvidenceReview, "model_json_schema"):
        return EvidenceReview.model_json_schema()
    return EvidenceReview.schema()


def _evidence_review_from_json(payload: str) -> EvidenceReview:
    if hasattr(EvidenceReview, "model_validate_json"):
        return EvidenceReview.model_validate_json(payload)
    return EvidenceReview.parse_raw(payload)


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

        prompt = self._build_report_prompt(domain=domain, query=query, context_documents=context_documents, source_refs=source_refs)

        last_error = None
        for model_name in (self.model, self.escalation_model):
            try:
                logger.info("llm_report_generation model=%s domain=%s docs=%s", model_name, domain, len(context_documents))
                payload = self._run_json_schema_prompt(
                    model_name=model_name,
                    prompt=prompt,
                    schema_name="domain_report",
                    schema=_domain_report_schema(),
                )
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

    def plan_retrieval(
        self,
        domain: str,
        query: str,
        context_documents: List[Document],
        source_refs: List[DomainSourceRef],
    ) -> Optional[RetrievalPlan]:
        if not self.is_available():
            raise ProviderUnavailableError("OpenAI provider is unavailable. Set OPENAI_API_KEY to enable it.")

        payload = self._run_json_schema_prompt(
            model_name=self.model,
            prompt=self._build_plan_prompt(
                domain=domain,
                query=query,
                context_documents=context_documents,
                source_refs=source_refs,
            ),
            schema_name="retrieval_plan",
            schema=_retrieval_plan_schema(),
        )
        return _retrieval_plan_from_json(payload)

    def inspect_evidence(
        self,
        domain: str,
        query: str,
        context_documents: List[Document],
        source_refs: List[DomainSourceRef],
    ) -> Optional[EvidenceReview]:
        if not self.is_available():
            raise ProviderUnavailableError("OpenAI provider is unavailable. Set OPENAI_API_KEY to enable it.")

        payload = self._run_json_schema_prompt(
            model_name=self.model,
            prompt=self._build_inspection_prompt(
                domain=domain,
                query=query,
                context_documents=context_documents,
                source_refs=source_refs,
            ),
            schema_name="evidence_review",
            schema=_evidence_review_schema(),
        )
        return _evidence_review_from_json(payload)

    def _run_json_schema_prompt(self, model_name: str, prompt: str, schema_name: str, schema: dict) -> str:
        response = self._client.responses.create(
            model=model_name,
            input=prompt,
            text={
                "format": {
                    "type": "json_schema",
                    "name": schema_name,
                    "schema": schema,
                }
            },
        )
        return response.output_text

    def _build_report_prompt(
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

    def _build_plan_prompt(
        self,
        domain: str,
        query: str,
        context_documents: List[Document],
        source_refs: List[DomainSourceRef],
    ) -> str:
        return (
            "You are a retrieval planning agent.\n"
            "Decide whether the current evidence is enough to answer the user query.\n"
            "If more evidence is needed, produce one improved retrieval query.\n"
            "Use should_retrieve=false when the current evidence is already sufficient.\n\n"
            + self._build_context_prompt(domain, query, context_documents, source_refs)
        )

    def _build_inspection_prompt(
        self,
        domain: str,
        query: str,
        context_documents: List[Document],
        source_refs: List[DomainSourceRef],
    ) -> str:
        return (
            "You are an evidence inspection agent.\n"
            "Review the retrieved evidence and determine whether it is grounded enough to answer the user query.\n"
            "Return a short summary of what the retrieved evidence now supports.\n\n"
            + self._build_context_prompt(domain, query, context_documents, source_refs)
        )

    def _build_context_prompt(
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
            f"Domain: {domain}\n"
            f"User query: {query}\n"
            f"Available source refs: {json.dumps(source_payload)}\n\n"
            "Context:\n"
            + "\n\n".join(context_blocks)
        )
