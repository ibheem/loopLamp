from typing import List

from backend.agents.base import DomainAgent
from backend.core.documents import Document
from backend.core.models import (
    DomainInsight,
    DomainMetric,
    DomainRecommendation,
    DomainReport,
    DomainSourceRef,
)


class BankingAssistantAgent(DomainAgent):
    name = "banking_assistant"

    def run(self, query: str, context_documents: List[Document]) -> DomainReport:
        if not context_documents:
            return DomainReport(
                domain=self.name,
                summary=(
                    "I could not ground an answer in the retrieved context. "
                    "Please ingest a banking notice, transaction file, or service policy document."
                ),
                insights=[
                    DomainInsight(
                        title="No grounded banking evidence found",
                        severity="medium",
                        detail="The retrieval step did not return banking policy, transaction, or service-charge context.",
                    )
                ],
                recommendations=[
                    DomainRecommendation(
                        priority=1,
                        action="Ingest a banking operations, charges, or transaction-support document before querying.",
                    )
                ],
            )

        snippets = []
        insights = []
        recommendations = []
        source_refs = []
        combined = " ".join(document.page_content.lower() for document in context_documents)

        for document in context_documents[:3]:
            snippet = document.page_content.strip().replace("\n", " ")
            if len(snippet) > 220:
                snippet = f"{snippet[:217]}..."
            snippets.append(snippet)
            source_refs.append(
                DomainSourceRef(
                    source=str(document.metadata.get("source", "unknown")),
                    chunk_index=document.metadata.get("chunk_index"),
                    file_type=document.metadata.get("file_type"),
                )
            )

        if "atm" in combined or "cash withdrawal" in combined:
            insights.append(
                DomainInsight(
                    title="ATM operations context detected",
                    severity="medium",
                    detail="Retrieved context includes ATM access, withdrawal, or card-usage instructions relevant to the query.",
                )
            )
            recommendations.append(
                DomainRecommendation(
                    priority=1,
                    action="Validate ATM handling instructions and communicate any service limits or downtime clearly to customers.",
                )
            )
        if "charge" in combined or "fee" in combined or "penalty" in combined:
            insights.append(
                DomainInsight(
                    title="Service charge policy identified",
                    severity="high",
                    detail="Retrieved material includes fee, penalty, or service-charge rules that affect customer guidance.",
                )
            )
            recommendations.append(
                DomainRecommendation(
                    priority=2,
                    action="Map the cited fee or penalty clauses into a customer-facing explanation before finalizing the response.",
                )
            )
        if "transaction" in combined or "debit" in combined or "credit" in combined:
            insights.append(
                DomainInsight(
                    title="Transaction support context present",
                    severity="medium",
                    detail="Retrieved context contains transaction-level evidence relevant for account activity or support analysis.",
                )
            )
        if "kyc" in combined or "verification" in combined or "identity" in combined:
            insights.append(
                DomainInsight(
                    title="Customer verification requirement found",
                    severity="medium",
                    detail="The banking context references identity or KYC checks that may gate service actions.",
                )
            )

        if not recommendations:
            recommendations.append(
                DomainRecommendation(
                    priority=1,
                    action="Review the cited banking evidence and convert it into a clear customer-support action or policy explanation.",
                )
            )

        metrics = [
            DomainMetric(name="matched_documents", value=str(len(context_documents)), unit="documents"),
            DomainMetric(name="matched_sources", value=str(len(source_refs)), unit="sources"),
        ]

        return DomainReport(
            domain=self.name,
            summary=(
                f"Banking Assistant response for query '{query}': "
                "Based on the retrieved context, the strongest matching evidence is: "
                f"{' '.join(snippets)}"
            ),
            metrics=metrics,
            insights=insights,
            recommendations=recommendations,
            source_refs=source_refs,
        )
