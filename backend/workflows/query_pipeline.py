import logging
from typing import Dict, List, Tuple

from backend.agents.automotive import AutomotiveAgent
from backend.agents.banking_assistant import BankingAssistantAgent
from backend.agents.ecommerce import EcommerceAgent
from backend.agents.financial_risk import FinancialRiskAgent
from backend.agents.manufacturing import ManufacturingAgent
from backend.agents.medical_qa import MedicalQAAgent
from backend.agents.openai_report_agent import OpenAIReportAgent
from backend.agents.telecom_security import TelecomSecurityAgent
from backend.core.models import ExecutionMetadata, QueryRequest, QueryResponse, SourceDocument
from backend.core.documents import Document
from backend.services.document_ingestion import DocumentIngestionService
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
        self.workflow = QueryGraphWorkflow(self.retrieval_service)
        telecom_fallback = TelecomSecurityAgent()
        finance_fallback = FinancialRiskAgent()
        medical_fallback = MedicalQAAgent()
        banking_fallback = BankingAssistantAgent()
        automotive_fallback = AutomotiveAgent()
        manufacturing_fallback = ManufacturingAgent()
        ecommerce_fallback = EcommerceAgent()
        telecom_agent = OpenAIReportAgent(
            provider=OpenAIResponsesReportProvider(),
            fallback_agent=telecom_fallback,
            domain_name="telecom_security",
        )
        finance_agent = OpenAIReportAgent(
            provider=OpenAIResponsesReportProvider(),
            fallback_agent=finance_fallback,
            domain_name="financial_risk",
        )
        medical_agent = OpenAIReportAgent(
            provider=OpenAIResponsesReportProvider(),
            fallback_agent=medical_fallback,
            domain_name="medical_qa",
        )
        banking_agent = OpenAIReportAgent(
            provider=OpenAIResponsesReportProvider(),
            fallback_agent=banking_fallback,
            domain_name="banking_assistant",
        )
        automotive_agent = OpenAIReportAgent(
            provider=OpenAIResponsesReportProvider(),
            fallback_agent=automotive_fallback,
            domain_name="automotive",
        )
        manufacturing_agent = OpenAIReportAgent(
            provider=OpenAIResponsesReportProvider(),
            fallback_agent=manufacturing_fallback,
            domain_name="manufacturing",
        )
        ecommerce_agent = OpenAIReportAgent(
            provider=OpenAIResponsesReportProvider(),
            fallback_agent=ecommerce_fallback,
            domain_name="ecommerce",
        )
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
        agent = self.agents.get(request.domain)
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
        evaluation = evaluate_report(execution.answer)
        runtime_metadata = agent.runtime_metadata() if hasattr(agent, "runtime_metadata") else {}
        execution_metadata = ExecutionMetadata(
            workflow_backend=self.workflow.backend_name,
            agent_type=runtime_metadata.get("agent_type", agent.__class__.__name__),
            provider_mode=runtime_metadata.get("provider_mode", "deterministic"),
            provider_model=runtime_metadata.get("provider_model", ""),
            used_fallback=runtime_metadata.get("used_fallback", "false") == "true",
        )
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
