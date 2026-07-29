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


class EcommerceAgent(DomainAgent):
    name = "ecommerce"

    def run(self, query: str, context_documents: List[Document]) -> DomainReport:
        if not context_documents:
            return DomainReport(
                domain=self.name,
                summary=(
                    "I could not ground an answer in the retrieved context. "
                    "Please ingest an order log, return policy, or customer-support catalog source."
                ),
                insights=[
                    DomainInsight(
                        title="No grounded ecommerce evidence found",
                        severity="medium",
                        detail="The retrieval step did not return order, return, pricing, or support-policy context.",
                    )
                ],
                recommendations=[
                    DomainRecommendation(
                        priority=1,
                        action="Ingest an ecommerce operations or customer-support document before querying this domain.",
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

        if "return" in combined or "refund" in combined or "exchange" in combined:
            insights.append(
                DomainInsight(
                    title="Returns policy context detected",
                    severity="high",
                    detail="Retrieved context includes refund, exchange, or return-handling guidance relevant to customer support.",
                )
            )
            recommendations.append(
                DomainRecommendation(
                    priority=1,
                    action="Apply the cited return or refund policy before approving customer compensation or exchange handling.",
                )
            )
        if "order" in combined or "shipment" in combined or "delivery" in combined:
            insights.append(
                DomainInsight(
                    title="Order operations evidence found",
                    severity="medium",
                    detail="The retrieved material includes order, shipping, or delivery context relevant to fulfillment support.",
                )
            )
            recommendations.append(
                DomainRecommendation(
                    priority=2,
                    action="Validate the order and shipment status against the retrieved evidence before responding to the customer.",
                )
            )
        if "inventory" in combined or "stock" in combined or "sku" in combined:
            insights.append(
                DomainInsight(
                    title="Inventory context present",
                    severity="medium",
                    detail="Retrieved context references stock availability or SKU-level information relevant to product handling.",
                )
            )

        if not recommendations:
            recommendations.append(
                DomainRecommendation(
                    priority=1,
                    action="Review the cited ecommerce evidence and convert it into a customer-support or order-operations action.",
                )
            )

        metrics = [
            DomainMetric(name="matched_documents", value=str(len(context_documents)), unit="documents"),
            DomainMetric(name="matched_sources", value=str(len(source_refs)), unit="sources"),
        ]

        return DomainReport(
            domain=self.name,
            summary=(
                f"Ecommerce Agent response for query '{query}': "
                "Based on the retrieved context, the strongest matching evidence is: "
                f"{' '.join(snippets)}"
            ),
            metrics=metrics,
            insights=insights,
            recommendations=recommendations,
            source_refs=source_refs,
        )
