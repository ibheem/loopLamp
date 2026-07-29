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


class FinancialRiskAgent(DomainAgent):
    name = "financial_risk"

    def run(self, query: str, context_documents: List[Document]) -> DomainReport:
        if not context_documents:
            return DomainReport(
                domain=self.name,
                summary=(
                    "I could not ground an answer in the retrieved context. "
                    "Please ingest a financial policy, compliance, or regulatory document."
                ),
                insights=[
                    DomainInsight(
                        title="No grounded financial evidence found",
                        severity="medium",
                        detail="The retrieval step did not return policy or compliance context.",
                    )
                ],
                recommendations=[
                    DomainRecommendation(
                        priority=1,
                        action="Ingest a finance regulation, risk policy, or compliance document before querying.",
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

        if "procurement" in combined:
            insights.append(
                DomainInsight(
                    title="Procurement risk guidance identified",
                    severity="high",
                    detail="Retrieved context includes procurement-related controls or guidelines relevant to financial governance.",
                )
            )
            recommendations.append(
                DomainRecommendation(
                    priority=1,
                    action="Review procurement control clauses and map them to current approval and audit workflows.",
                )
            )
        if "accountability" in combined or "audit" in combined:
            insights.append(
                DomainInsight(
                    title="Financial accountability requirements present",
                    severity="high",
                    detail="Context references accountability, audit, or reporting obligations that affect compliance posture.",
                )
            )
            recommendations.append(
                DomainRecommendation(
                    priority=2,
                    action="Document accountability owners and ensure audit-ready reporting controls are in place.",
                )
            )
        if "kyc" in combined or "investor" in combined or "sebi" in combined:
            insights.append(
                DomainInsight(
                    title="Regulatory compliance context detected",
                    severity="medium",
                    detail="Retrieved material references investor protection, KYC, or SEBI-related compliance expectations.",
                )
            )

        if not recommendations:
            recommendations.append(
                DomainRecommendation(
                    priority=1,
                    action="Review the cited clauses and convert them into explicit financial control or compliance actions.",
                )
            )

        metrics = [
            DomainMetric(name="matched_documents", value=str(len(context_documents)), unit="documents"),
            DomainMetric(name="matched_sources", value=str(len(source_refs)), unit="sources"),
        ]

        return DomainReport(
            domain=self.name,
            summary=(
                f"Financial Risk Agent response for query '{query}': "
                "Based on the retrieved context, the strongest matching evidence is: "
                f"{' '.join(snippets)}"
            ),
            metrics=metrics,
            insights=insights,
            recommendations=recommendations,
            source_refs=source_refs,
        )
