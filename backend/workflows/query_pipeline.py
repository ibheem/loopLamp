import logging
from typing import Dict, List, Optional, Tuple

from backend.agents.automotive import AutomotiveAgent
from backend.agents.banking_assistant import BankingAssistantAgent
from backend.agents.ecommerce import EcommerceAgent
from backend.agents.financial_risk import FinancialRiskAgent
from backend.agents.manufacturing import ManufacturingAgent
from backend.agents.medical_qa import MedicalQAAgent
from backend.agents.openai_report_agent import OpenAIReportAgent
from backend.agents.telecom_security import TelecomSecurityAgent
from backend.agents.tool_calling_report_agent import ToolCallingReportAgent
from backend.core.models import ExecutionMetadata, QueryRequest, QueryResponse, SourceDocument
from backend.core.documents import Document
from backend.services.document_ingestion import DocumentIngestionService
from backend.services.llm_registry import LLMProviderRegistry
from backend.services.llm_provider import OpenAIResponsesReportProvider
from backend.services.report_evaluator import evaluate_report
from backend.services.retrieval import RetrievalService
from backend.services.source_registry import SourceRegistryService
from backend.services.vector_store import build_vector_db
from backend.workflows.query_graph import QueryGraphWorkflow

logger = logging.getLogger(__name__)


class QueryPipeline:
    def __init__(self):
        self.ingestion_service = DocumentIngestionService()
        self.retrieval_service = RetrievalService()
        self.source_registry = SourceRegistryService()
        self.provider_registry = LLMProviderRegistry()
        self.workflow = QueryGraphWorkflow(self.retrieval_service)
        self.fallback_agents = {
            "telecom_security": TelecomSecurityAgent(),
            "financial_risk": FinancialRiskAgent(),
            "medical_qa": MedicalQAAgent(),
            "banking_assistant": BankingAssistantAgent(),
            "automotive": AutomotiveAgent(),
            "manufacturing": ManufacturingAgent(),
            "ecommerce": EcommerceAgent(),
            "general": TelecomSecurityAgent(),
        }
        telecom_agent = self._build_tool_calling_agent("telecom_security")
        finance_agent = self._build_tool_calling_agent("financial_risk")
        medical_agent = self._build_tool_calling_agent("medical_qa")
        banking_agent = self._build_tool_calling_agent("banking_assistant")
        automotive_agent = self._build_tool_calling_agent("automotive")
        manufacturing_agent = self._build_tool_calling_agent("manufacturing")
        ecommerce_agent = self._build_tool_calling_agent("ecommerce")
        self.agents = {
            "telecom_security": telecom_agent,
            "financial_risk": finance_agent,
            "medical_qa": medical_agent,
            "banking_assistant": banking_agent,
            "automotive": automotive_agent,
            "manufacturing": manufacturing_agent,
            "ecommerce": ecommerce_agent,
            "general": telecom_agent,
        }

    def run(self, request: QueryRequest) -> QueryResponse:
        agent = self._resolve_agent(request)
        if agent is None:
            supported = ", ".join(sorted(self.agents))
            raise ValueError(f"Unsupported domain '{request.domain}'. Supported domains: {supported}")

        documents, collection_key, domain_source_counts = self._resolve_request_documents(request)
        vector_db = build_vector_db(documents, collection_key=collection_key)
        if request.retrieval_mode == "source" and request.source_id:
            self.source_registry.set_source_index_state(
                source_id=request.source_id,
                index_status="indexed",
                vector_backend=getattr(vector_db, "backend_name", vector_db.__class__.__name__),
                indexed_document_count=len(documents),
            )
        if request.retrieval_mode == "domain":
            for source_id, document_count in domain_source_counts.items():
                self.source_registry.set_source_index_state(
                    source_id=source_id,
                    index_status="indexed",
                    vector_backend=getattr(vector_db, "backend_name", vector_db.__class__.__name__),
                    indexed_document_count=document_count,
                )

        execution = self.workflow.run(agent, vector_db, request)
        runtime_metadata = getattr(execution, "runtime_metadata", None) or (
            agent.runtime_metadata() if hasattr(agent, "runtime_metadata") else {}
        )
        execution_metadata = ExecutionMetadata(
            workflow_backend=self.workflow.backend_name,
            agent_type=runtime_metadata.get("agent_type", agent.__class__.__name__),
            requested_provider=(request.llm_provider or "auto").strip(),
            requested_model=(request.llm_model or "").strip(),
            provider_mode=runtime_metadata.get("provider_mode", "deterministic"),
            provider_model=runtime_metadata.get("provider_model", ""),
            llm_generated=runtime_metadata.get("used_fallback", "false") != "true"
            and runtime_metadata.get("provider_mode", "deterministic") not in {"fallback", "deterministic"},
            used_fallback=runtime_metadata.get("used_fallback", "false") == "true",
            tool_calls=int(runtime_metadata.get("tool_calls", 0) or 0),
            agent_loop=str(runtime_metadata.get("agent_loop", "retrieve_generate")),
            plan=runtime_metadata.get("plan"),
            comparison=runtime_metadata.get("comparison"),
            evidence_summary=runtime_metadata.get("evidence_summary"),
            inspection=runtime_metadata.get("inspection"),
            agent_trace=runtime_metadata.get("agent_trace") or {},
        )
        evaluation = evaluate_report(execution.answer, execution=execution_metadata)
        logger.info(
            "query_pipeline_complete domain=%s backend=%s provider_mode=%s model=%s attempts=%s sources=%s reflected=%s issues=%s",
            agent.name,
            self.workflow.backend_name,
            execution_metadata.provider_mode,
            execution_metadata.provider_model or "n/a",
            execution.attempts,
            len(execution.sources),
            execution.used_reflection,
            ",".join(evaluation.issues) or "none",
        )

        return QueryResponse(
            answer=execution.answer.summary,
            domain=agent.name,
            attempts=execution.attempts,
            used_reflection=execution.used_reflection,
            report=execution.answer,
            evaluation=evaluation,
            execution=execution_metadata,
            sources=[
                SourceDocument(content=document.page_content, metadata=document.metadata)
                for document in execution.sources
            ],
        )

    def _build_tool_calling_agent(
        self,
        domain: str,
        provider_id: str = "auto",
        model_override: Optional[str] = None,
    ) -> ToolCallingReportAgent:
        provider = (
            OpenAIResponsesReportProvider()
            if provider_id == "openai" and not model_override
            else self.provider_registry.create_provider(provider_id=provider_id, model_override=model_override)
        )
        return ToolCallingReportAgent(
            provider=provider,
            fallback_agent=self.fallback_agents[domain],
            domain_name=domain,
        )

    def _resolve_agent(self, request: QueryRequest):
        base_agent = self.agents.get(request.domain)
        if base_agent is None:
            return None

        selected_provider = (request.llm_provider or "auto").strip()
        selected_model = (request.llm_model or "").strip()
        if selected_provider == "auto" and not selected_model:
            return base_agent

        return self._build_tool_calling_agent(
            domain=request.domain,
            provider_id=selected_provider,
            model_override=selected_model or None,
        )

    def _resolve_request_documents(self, request: QueryRequest) -> Tuple[List[Document], str, Dict[str, int]]:
        if request.retrieval_mode == "domain":
            documents, source_counts = self._load_domain_documents(request.domain)
            return documents, f"domain:{request.domain}:all_sources", source_counts

        source_path = request.document_path
        if request.source_id:
            source_path = str(self.source_registry.resolve_source_path(request.source_id))
        documents = self.ingestion_service.ingest(source_path)
        return documents, request.source_id or source_path or request.domain, {}

    def _load_domain_documents(self, domain: str) -> Tuple[List[Document], Dict[str, int]]:
        sources = self.source_registry.list_sources_for_domain(domain)
        if not sources:
            raise ValueError(f"No saved sources are available for domain '{domain}'.")

        combined_documents: List[Document] = []
        source_counts: Dict[str, int] = {}
        indexed_source_count = 0
        for source in sources:
            try:
                documents = self.ingestion_service.ingest(source.path)
                for document in documents:
                    document.metadata.update(
                        {
                            "source_id": source.source_id,
                            "source_domain": source.domain,
                            "source_origin": source.origin,
                        }
                    )
                combined_documents.extend(documents)
                source_counts[source.source_id] = len(documents)
                indexed_source_count += 1
            except Exception as exc:
                self.source_registry.set_source_index_state(
                    source_id=source.source_id,
                    index_status="failed",
                )
                logger.warning(
                    "domain_source_ingest_failed domain=%s source_id=%s path=%s error=%s",
                    domain,
                    source.source_id,
                    source.path,
                    exc,
                )

        if not combined_documents:
            raise ValueError(f"No readable sources were found for domain '{domain}'.")

        logger.info(
            "domain_corpus_built domain=%s sources=%s documents=%s",
            domain,
            indexed_source_count,
            len(combined_documents),
        )
        return combined_documents, source_counts

    def reindex_source(self, source_id: str) -> dict:
        source_path = str(self.source_registry.resolve_source_path(source_id))
        documents = self.ingestion_service.ingest(source_path)
        vector_db = build_vector_db(documents, collection_key=source_id, force_reindex=True)
        self.source_registry.set_source_index_state(
            source_id=source_id,
            index_status="indexed",
            vector_backend=getattr(vector_db, "backend_name", vector_db.__class__.__name__),
            indexed_document_count=len(documents),
        )
        return {
            "source_id": source_id,
            "indexed": True,
            "document_count": len(documents),
            "vector_backend": getattr(vector_db, "backend_name", vector_db.__class__.__name__),
        }

    def sync_saved_sources(self) -> Dict[str, int]:
        indexed_count = 0
        failed_count = 0

        for source in self.source_registry.list_indexable_sources():
            try:
                documents = self.ingestion_service.ingest(source.path)
                vector_db = build_vector_db(documents, collection_key=source.source_id)
                self.source_registry.set_source_index_state(
                    source_id=source.source_id,
                    index_status="indexed",
                    vector_backend=getattr(vector_db, "backend_name", vector_db.__class__.__name__),
                    indexed_document_count=len(documents),
                )
                indexed_count += 1
            except Exception as exc:
                self.source_registry.set_source_index_state(
                    source_id=source.source_id,
                    index_status="failed",
                )
                failed_count += 1
                logger.warning(
                    "startup_source_sync_failed source_id=%s path=%s error=%s",
                    source.source_id,
                    source.path,
                    exc,
                )

        logger.info(
            "startup_source_sync_complete indexed=%s failed=%s",
            indexed_count,
            failed_count,
        )
        return {
            "indexed_count": indexed_count,
            "failed_count": failed_count,
        }
