import json
import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from backend.core.documents import Document
from backend.core.models import DomainReport, DomainSourceRef

logger = logging.getLogger(__name__)

try:  # pragma: no cover - exercised through provider availability checks
    from langchain_ollama import ChatOllama
except Exception:  # pragma: no cover - import failure handled at runtime
    ChatOllama = None

try:  # pragma: no cover - exercised through provider availability checks
    from langchain_openai import ChatOpenAI
except Exception:  # pragma: no cover - import failure handled at runtime
    ChatOpenAI = None


class ProviderUnavailableError(RuntimeError):
    pass


def _model_to_dict(model: BaseModel) -> dict:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


class RetrievalPlan(BaseModel):
    should_retrieve: bool = False
    search_query: str = ""
    max_results: int = Field(default=0, ge=0, le=10)
    rationale: str = ""
    compare_sources: bool = False
    summarize_evidence: bool = False


class EvidenceReview(BaseModel):
    grounded: bool = False
    summary: str = ""


class SourceComparison(BaseModel):
    summary: str = ""
    compared_sources: List[str] = Field(default_factory=list)
    consensus_points: List[str] = Field(default_factory=list)
    conflicts: List[str] = Field(default_factory=list)
    control_themes: List[str] = Field(default_factory=list)
    obligations: List[str] = Field(default_factory=list)
    symptoms: List[str] = Field(default_factory=list)
    red_flags: List[str] = Field(default_factory=list)
    escalation_criteria: List[str] = Field(default_factory=list)
    care_constraints: List[str] = Field(default_factory=list)
    transaction_signals: List[str] = Field(default_factory=list)
    customer_impact_checks: List[str] = Field(default_factory=list)
    fraud_indicators: List[str] = Field(default_factory=list)
    next_actions: List[str] = Field(default_factory=list)
    order_signals: List[str] = Field(default_factory=list)
    policy_constraints: List[str] = Field(default_factory=list)
    fulfillment_risks: List[str] = Field(default_factory=list)
    customer_resolution_actions: List[str] = Field(default_factory=list)
    fault_signals: List[str] = Field(default_factory=list)
    subsystem_risks: List[str] = Field(default_factory=list)
    repair_prerequisites: List[str] = Field(default_factory=list)
    safety_checks: List[str] = Field(default_factory=list)
    defect_signals: List[str] = Field(default_factory=list)
    line_impact: List[str] = Field(default_factory=list)
    containment_actions: List[str] = Field(default_factory=list)
    restart_gates: List[str] = Field(default_factory=list)


class EvidenceSummary(BaseModel):
    summary: str = ""
    key_points: List[str] = Field(default_factory=list)
    cited_sources: List[str] = Field(default_factory=list)
    decision_basis: List[str] = Field(default_factory=list)
    recommended_controls: List[str] = Field(default_factory=list)
    follow_up_checks: List[str] = Field(default_factory=list)
    symptom_summary: List[str] = Field(default_factory=list)
    escalation_path: List[str] = Field(default_factory=list)
    patient_safety_notes: List[str] = Field(default_factory=list)
    service_actions: List[str] = Field(default_factory=list)
    customer_message_points: List[str] = Field(default_factory=list)
    fraud_follow_ups: List[str] = Field(default_factory=list)
    refund_basis: List[str] = Field(default_factory=list)
    resolution_plan: List[str] = Field(default_factory=list)
    inventory_notes: List[str] = Field(default_factory=list)
    diagnosis_summary: List[str] = Field(default_factory=list)
    repair_plan: List[str] = Field(default_factory=list)
    vehicle_safety_notes: List[str] = Field(default_factory=list)
    containment_summary: List[str] = Field(default_factory=list)
    production_actions: List[str] = Field(default_factory=list)
    quality_follow_ups: List[str] = Field(default_factory=list)


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
        comparison: Optional[SourceComparison] = None,
        evidence_summary: Optional[EvidenceSummary] = None,
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

    def compare_sources(
        self,
        domain: str,
        query: str,
        context_documents: List[Document],
        source_refs: List[DomainSourceRef],
    ) -> Optional[SourceComparison]:
        return None

    def summarize_evidence(
        self,
        domain: str,
        query: str,
        context_documents: List[Document],
        source_refs: List[DomainSourceRef],
    ) -> Optional[EvidenceSummary]:
        return None

    def build_chat_model(self, model_override: Optional[str] = None):
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


def _source_comparison_schema() -> dict:
    if hasattr(SourceComparison, "model_json_schema"):
        return SourceComparison.model_json_schema()
    return SourceComparison.schema()


def _source_comparison_from_json(payload: str) -> SourceComparison:
    if hasattr(SourceComparison, "model_validate_json"):
        return SourceComparison.model_validate_json(payload)
    return SourceComparison.parse_raw(payload)


def _evidence_summary_schema() -> dict:
    if hasattr(EvidenceSummary, "model_json_schema"):
        return EvidenceSummary.model_json_schema()
    return EvidenceSummary.schema()


def _evidence_summary_from_json(payload: str) -> EvidenceSummary:
    if hasattr(EvidenceSummary, "model_validate_json"):
        return EvidenceSummary.model_validate_json(payload)
    return EvidenceSummary.parse_raw(payload)


class OpenAIResponsesReportProvider(ReportLLMProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-5-mini",
        escalation_model: str = "gpt-5.1",
        provider_id: str = "openai",
        base_url: Optional[str] = None,
        requires_api_key: bool = True,
    ):
        self.api_key = api_key if api_key is not None else (os.getenv("OPENAI_API_KEY") if provider_id == "openai" else None)
        self.model = model
        self.escalation_model = escalation_model
        self.provider_id = provider_id
        self.base_url = base_url
        self.requires_api_key = requires_api_key
        self._model_cache: Dict[str, Any] = {}

    def is_available(self) -> bool:
        return self.build_chat_model() is not None

    def build_chat_model(self, model_override: Optional[str] = None):
        selected_model = (model_override or self.model or "").strip()
        if not selected_model:
            return None
        if selected_model in self._model_cache:
            return self._model_cache[selected_model]

        model = self._create_chat_model(selected_model)
        if model is not None:
            self._model_cache[selected_model] = model
        return model

    def generate_report(
        self,
        domain: str,
        query: str,
        context_documents: List[Document],
        source_refs: List[DomainSourceRef],
        comparison: Optional[SourceComparison] = None,
        evidence_summary: Optional[EvidenceSummary] = None,
    ) -> DomainReport:
        if not self.is_available():
            raise ProviderUnavailableError(
                f"{self.provider_id} provider is unavailable. Configure the related credentials to enable it."
            )

        prompt = self._build_report_prompt(
            domain=domain,
            query=query,
            context_documents=context_documents,
            source_refs=source_refs,
            comparison=comparison,
            evidence_summary=evidence_summary,
        )

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
                quality_issues = self._report_quality_issues(report)
                if quality_issues:
                    logger.info(
                        "llm_report_repair_requested model=%s domain=%s issues=%s",
                        model_name,
                        domain,
                        ",".join(quality_issues),
                    )
                    repair_payload = self._run_json_schema_prompt(
                        model_name=model_name,
                        prompt=self._build_report_repair_prompt(
                            domain=domain,
                            query=query,
                            context_documents=context_documents,
                            source_refs=source_refs,
                            draft_report=report,
                            quality_issues=quality_issues,
                            comparison=comparison,
                            evidence_summary=evidence_summary,
                        ),
                        schema_name="domain_report_repair",
                        schema=_domain_report_schema(),
                    )
                    repaired_report = _domain_report_from_json(repair_payload)
                    repaired_issues = self._report_quality_issues(repaired_report)
                    if not repaired_issues:
                        report = repaired_report
                    else:
                        logger.warning(
                            "llm_report_repair_incomplete model=%s domain=%s issues=%s",
                            model_name,
                            domain,
                            ",".join(repaired_issues),
                        )
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

    def compare_sources(
        self,
        domain: str,
        query: str,
        context_documents: List[Document],
        source_refs: List[DomainSourceRef],
    ) -> Optional[SourceComparison]:
        if not self.is_available():
            raise ProviderUnavailableError("OpenAI provider is unavailable. Set OPENAI_API_KEY to enable it.")

        payload = self._run_json_schema_prompt(
            model_name=self.model,
            prompt=self._build_comparison_prompt(
                domain=domain,
                query=query,
                context_documents=context_documents,
                source_refs=source_refs,
            ),
            schema_name="source_comparison",
            schema=_source_comparison_schema(),
        )
        return _source_comparison_from_json(payload)

    def summarize_evidence(
        self,
        domain: str,
        query: str,
        context_documents: List[Document],
        source_refs: List[DomainSourceRef],
    ) -> Optional[EvidenceSummary]:
        if not self.is_available():
            raise ProviderUnavailableError("OpenAI provider is unavailable. Set OPENAI_API_KEY to enable it.")

        payload = self._run_json_schema_prompt(
            model_name=self.model,
            prompt=self._build_evidence_summary_prompt(
                domain=domain,
                query=query,
                context_documents=context_documents,
                source_refs=source_refs,
            ),
            schema_name="evidence_summary",
            schema=_evidence_summary_schema(),
        )
        return _evidence_summary_from_json(payload)

    def _run_json_schema_prompt(self, model_name: str, prompt: str, schema_name: str, schema: dict) -> str:
        chat_model = self.build_chat_model(model_name)
        if chat_model is None:
            raise ProviderUnavailableError(
                f"{self.provider_id} provider is unavailable. Configure the related credentials to enable it."
            )
        structured = chat_model.with_structured_output(schema, method=self._structured_output_method())
        response = structured.invoke(prompt)
        if isinstance(response, BaseModel):
            if hasattr(response, "model_dump_json"):
                return response.model_dump_json()
            return json.dumps(response.dict())
        return json.dumps(response)

    def _create_chat_model(self, model_name: str):
        if self.provider_id == "ollama":
            if ChatOllama is None:
                return None
            return ChatOllama(
                model=model_name,
                base_url=self.base_url,
                temperature=0,
                validate_model_on_init=False,
            )

        if ChatOpenAI is None:
            return None

        client_api_key = self.api_key
        if self.requires_api_key and not client_api_key:
            return None

        kwargs: Dict[str, Any] = {
            "model": model_name,
            "temperature": 0,
            "max_retries": 1,
        }
        if client_api_key:
            kwargs["api_key"] = client_api_key
        if self.base_url:
            kwargs["base_url"] = self.base_url
        if self.provider_id == "openai":
            kwargs["use_responses_api"] = True
        return ChatOpenAI(**kwargs)

    def _structured_output_method(self) -> str:
        if self.provider_id in {"openrouter", "groq", "together"}:
            return "function_calling"
        return "json_schema"

    def _build_report_prompt(
        self,
        domain: str,
        query: str,
        context_documents: List[Document],
        source_refs: List[DomainSourceRef],
        comparison: Optional[SourceComparison] = None,
        evidence_summary: Optional[EvidenceSummary] = None,
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

        source_payload = [_model_to_dict(source_ref) for source_ref in source_refs]
        comparison_payload = (
            json.dumps(comparison.model_dump() if hasattr(comparison, "model_dump") else comparison)
            if comparison is not None
            else "null"
        )
        evidence_summary_payload = (
            json.dumps(evidence_summary.model_dump() if hasattr(evidence_summary, "model_dump") else evidence_summary)
            if evidence_summary is not None
            else "null"
        )
        return (
            "You are a domain reporting agent.\n"
            "Return only data that can be grounded in the supplied context.\n"
            "If a source comparison or evidence synthesis is provided, use it to sharpen the final answer, but do not invent facts beyond the retrieved evidence.\n"
            + self._domain_report_guidance(domain)
            + "Respond with a JSON object matching the provided schema.\n"
            + "The summary must begin with the exact phrase 'Based on the retrieved context,'.\n"
            + "Provide at least 2 concise, grounded insights.\n"
            + "Provide at least 2 grounded recommendations or follow-up actions.\n"
            + "Use source_refs from the provided evidence and do not leave source_refs empty.\n"
            + "Keep insights concise, dashboard-ready, and non-redundant.\n\n"
            + f"Domain: {domain}\n"
            + f"User query: {query}\n"
            + f"Available source refs: {json.dumps(source_payload)}\n\n"
            + f"Source comparison: {comparison_payload}\n"
            + f"Evidence synthesis: {evidence_summary_payload}\n\n"
            + "Context:\n"
            + "\n\n".join(context_blocks)
        )

    def _build_report_repair_prompt(
        self,
        domain: str,
        query: str,
        context_documents: List[Document],
        source_refs: List[DomainSourceRef],
        draft_report: DomainReport,
        quality_issues: List[str],
        comparison: Optional[SourceComparison] = None,
        evidence_summary: Optional[EvidenceSummary] = None,
    ) -> str:
        draft_payload = json.dumps(_model_to_dict(draft_report), ensure_ascii=False)
        return (
            "You are repairing a weak domain report.\n"
            "Rewrite the JSON so it remains strictly grounded in the supplied evidence.\n"
            "The summary must begin with the exact phrase 'Based on the retrieved context,'.\n"
            "Return at least 2 grounded insights.\n"
            "Return at least 2 grounded recommendations or validation follow-up actions.\n"
            "Ensure source_refs is populated from the provided evidence.\n"
            f"Quality issues to fix: {json.dumps(quality_issues)}\n"
            f"Draft report: {draft_payload}\n\n"
            + self._build_report_prompt(
                domain=domain,
                query=query,
                context_documents=context_documents,
                source_refs=source_refs,
                comparison=comparison,
                evidence_summary=evidence_summary,
            )
        )

    def _report_quality_issues(self, report: DomainReport) -> List[str]:
        issues: List[str] = []
        if "retrieved context" not in report.summary.lower():
            issues.append("summary_not_explicitly_grounded")
        if len(report.insights) < 2:
            issues.append("insufficient_insights")
        if len(report.recommendations) < 2:
            issues.append("insufficient_recommendations")
        if not report.source_refs:
            issues.append("missing_source_refs")
        return issues

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
            "Set compare_sources=true when the answer should compare evidence across files or chunks.\n"
            "Set summarize_evidence=true when the evidence should be condensed into a cross-source synthesis before reporting.\n"
            + self._domain_plan_guidance(domain)
            + "Use should_retrieve=false when the current evidence is already sufficient.\n\n"
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

    def _build_comparison_prompt(
        self,
        domain: str,
        query: str,
        context_documents: List[Document],
        source_refs: List[DomainSourceRef],
    ) -> str:
        return (
            "You are a source comparison agent.\n"
            "Compare the available evidence across sources or chunks.\n"
            "Identify the main agreement points and any conflicts while staying strictly grounded in the supplied evidence.\n\n"
            + self._domain_comparison_guidance(domain)
            + self._build_context_prompt(domain, query, context_documents, source_refs)
        )

    def _build_evidence_summary_prompt(
        self,
        domain: str,
        query: str,
        context_documents: List[Document],
        source_refs: List[DomainSourceRef],
    ) -> str:
        return (
            "You are an evidence summarization agent.\n"
            "Condense the evidence into a concise cross-source synthesis for downstream reporting.\n"
            "Return grounded key points only and cite the most relevant source filenames.\n\n"
            + self._domain_evidence_summary_guidance(domain)
            + self._build_context_prompt(domain, query, context_documents, source_refs)
        )

    def _domain_plan_guidance(self, domain: str) -> str:
        if domain == "financial_risk":
            return (
                "For financial risk, target approval authority, control ownership, audit traceability, segregation of duties, and release conditions.\n"
            )
        if domain == "medical_qa":
            return (
                "For medical Q&A, target symptom descriptions, red-flag findings, escalation criteria, and care constraints from authoritative clinical evidence.\n"
            )
        if domain == "banking_assistant":
            return (
                "For banking assistance, target transaction signals, customer-impact checks, fraud clues, service policy actions, and next-step guidance.\n"
            )
        if domain == "automotive":
            return (
                "For automotive, target fault signals, subsystem risk evidence, repair prerequisites, safety checks, and the specific diagnostic action path.\n"
            )
        if domain == "manufacturing":
            return (
                "For manufacturing, target defect signals, line impact, containment actions, restart conditions, and production-quality follow-up actions.\n"
            )
        if domain == "ecommerce":
            return (
                "For ecommerce, target order signals, refund or policy constraints, fulfillment risks, and clear customer-resolution actions.\n"
            )
        return ""

    def _domain_report_guidance(self, domain: str) -> str:
        if domain == "financial_risk":
            return (
                "For financial risk, prioritize approval controls, delegated authority, auditability, and decision-ready compliance actions.\n"
            )
        if domain == "medical_qa":
            return (
                "For medical Q&A, prioritize clinically grounded symptom interpretation, red-flag escalation, and careful safety-oriented recommendations.\n"
            )
        if domain == "banking_assistant":
            return (
                "For banking assistance, prioritize customer-safe operational actions, fraud awareness, service clarity, and policy-grounded next steps.\n"
            )
        if domain == "automotive":
            return (
                "For automotive, prioritize grounded diagnostics, subsystem-aware repair actions, and vehicle safety cautions before closure.\n"
            )
        if domain == "manufacturing":
            return (
                "For manufacturing, prioritize containment, restart readiness, quality ownership, and line-safe operational recovery.\n"
            )
        if domain == "ecommerce":
            return (
                "For ecommerce, prioritize policy-grounded refund logic, fulfillment clarity, inventory-aware actions, and customer-safe resolution steps.\n"
            )
        return ""

    def _domain_comparison_guidance(self, domain: str) -> str:
        if domain == "financial_risk":
            return (
                "For financial risk, populate control_themes and obligations from the evidence, and use conflicts for clause tension or approval ambiguity.\n\n"
            )
        if domain == "medical_qa":
            return (
                "For medical Q&A, populate symptoms, red_flags, escalation_criteria, and care_constraints directly from the evidence.\n\n"
            )
        if domain == "banking_assistant":
            return (
                "For banking assistance, populate transaction_signals, customer_impact_checks, fraud_indicators, and next_actions from the evidence.\n\n"
            )
        if domain == "automotive":
            return (
                "For automotive, populate fault_signals, subsystem_risks, repair_prerequisites, and safety_checks directly from the evidence.\n\n"
            )
        if domain == "manufacturing":
            return (
                "For manufacturing, populate defect_signals, line_impact, containment_actions, and restart_gates directly from the evidence.\n\n"
            )
        if domain == "ecommerce":
            return (
                "For ecommerce, populate order_signals, policy_constraints, fulfillment_risks, and customer_resolution_actions directly from the evidence.\n\n"
            )
        return ""

    def _domain_evidence_summary_guidance(self, domain: str) -> str:
        if domain == "financial_risk":
            return (
                "For financial risk, populate decision_basis, recommended_controls, and follow_up_checks so the final report can support a governance decision.\n\n"
            )
        if domain == "medical_qa":
            return (
                "For medical Q&A, populate symptom_summary, escalation_path, and patient_safety_notes so the final answer stays clinically cautious and grounded.\n\n"
            )
        if domain == "banking_assistant":
            return (
                "For banking assistance, populate service_actions, customer_message_points, and fraud_follow_ups so the final answer is actionable for support operations.\n\n"
            )
        if domain == "automotive":
            return (
                "For automotive, populate diagnosis_summary, repair_plan, and vehicle_safety_notes so the final answer becomes technician-ready and safety-conscious.\n\n"
            )
        if domain == "manufacturing":
            return (
                "For manufacturing, populate containment_summary, production_actions, and quality_follow_ups so the final answer supports safe restart and quality recovery.\n\n"
            )
        if domain == "ecommerce":
            return (
                "For ecommerce, populate refund_basis, resolution_plan, and inventory_notes so the final answer is support-ready and policy-grounded.\n\n"
            )
        return ""

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

        source_payload = [_model_to_dict(source_ref) for source_ref in source_refs]
        return (
            f"Domain: {domain}\n"
            f"User query: {query}\n"
            f"Available source refs: {json.dumps(source_payload)}\n\n"
            "Context:\n"
            + "\n\n".join(context_blocks)
        )
