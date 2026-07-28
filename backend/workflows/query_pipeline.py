import logging

from backend.agents.telecom_security import TelecomSecurityAgent
from backend.core.models import QueryRequest, QueryResponse, SourceDocument
from backend.services.document_ingestion import DocumentIngestionService
from backend.services.retrieval import RetrievalService
from backend.services.vector_store import build_vector_db
from backend.workflows.query_graph import QueryGraphWorkflow

logger = logging.getLogger(__name__)


class QueryPipeline:
    def __init__(self):
        self.ingestion_service = DocumentIngestionService()
        self.retrieval_service = RetrievalService()
        self.workflow = QueryGraphWorkflow(self.retrieval_service)
        self.agents = {
            "telecom_security": TelecomSecurityAgent(),
            "general": TelecomSecurityAgent(),
        }

    def run(self, request: QueryRequest) -> QueryResponse:
        agent = self.agents.get(request.domain)
        if agent is None:
            supported = ", ".join(sorted(self.agents))
            raise ValueError(f"Unsupported domain '{request.domain}'. Supported domains: {supported}")

        documents = self.ingestion_service.ingest(request.document_path)
        vector_db = build_vector_db(documents)

        execution = self.workflow.run(agent, vector_db, request)
        logger.info(
            "query_pipeline_complete domain=%s backend=%s attempts=%s sources=%s reflected=%s",
            agent.name,
            self.workflow.backend_name,
            execution.attempts,
            len(execution.sources),
            execution.used_reflection,
        )

        return QueryResponse(
            answer=execution.answer.summary,
            domain=agent.name,
            attempts=execution.attempts,
            used_reflection=execution.used_reflection,
            report=execution.answer,
            sources=[
                SourceDocument(content=document.page_content, metadata=document.metadata)
                for document in execution.sources
            ],
        )
