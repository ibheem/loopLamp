import logging

from backend.agents.financial_risk import FinancialRiskAgent
from backend.agents.openai_report_agent import OpenAIReportAgent
from backend.agents.telecom_security import TelecomSecurityAgent
from backend.core.models import ExecutionMetadata, QueryRequest, QueryResponse, SourceDocument
from backend.services.document_ingestion import DocumentIngestionService
from backend.services.llm_provider import OpenAIResponsesReportProvider
from backend.services.report_evaluator import evaluate_report
from backend.services.retrieval import RetrievalService
from backend.services.vector_store import build_vector_db
from backend.workflows.query_graph import QueryGraphWorkflow

logger = logging.getLogger(__name__)


class QueryPipeline:
    def __init__(self):
        self.ingestion_service = DocumentIngestionService()
        self.retrieval_service = RetrievalService()
        self.workflow = QueryGraphWorkflow(self.retrieval_service)
        telecom_fallback = TelecomSecurityAgent()
        finance_fallback = FinancialRiskAgent()
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
        self.agents = {
            "telecom_security": telecom_agent,
            "financial_risk": finance_agent,
            "general": telecom_agent,
        }

    def run(self, request: QueryRequest) -> QueryResponse:
        agent = self.agents.get(request.domain)
        if agent is None:
            supported = ", ".join(sorted(self.agents))
            raise ValueError(f"Unsupported domain '{request.domain}'. Supported domains: {supported}")

        documents = self.ingestion_service.ingest(request.document_path)
        vector_db = build_vector_db(documents)

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
