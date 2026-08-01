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


class TelecomSecurityAgent(DomainAgent):
    name = "telecom_security"

    def run(self, query: str, context_documents: List[Document]) -> DomainReport:
        if not context_documents:
            return DomainReport(
                domain=self.name,
                summary=(
                    "I could not ground an answer in the retrieved context. "
                    "Please ingest a document with telecom, security, or policy details."
                ),
                insights=[
                    DomainInsight(
                        title="No grounded evidence found",
                        severity="medium",
                        detail="The retrieval step did not return supporting telecom or policy context.",
                    )
                ],
                recommendations=[
                    DomainRecommendation(
                        priority=1,
                        action="Ingest a telecom incident, signaling, or policy document before querying.",
                    )
                ],
            )

        snippets = []
        recommendations = []
        insights = []
        metrics = [
            DomainMetric(name="matched_documents", value=str(len(context_documents)), unit="documents"),
        ]
        source_refs = []

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

        combined = " ".join(document.page_content.lower() for document in context_documents)
        if "ss7" in combined:
            insights.append(
                DomainInsight(
                    title="SS7 signaling anomaly detected",
                    severity="high",
                    detail="Retrieved context links the issue to SS7 routing instability and customer-impacting auth failures.",
                )
            )
        if "otp" in combined or "authentication" in combined:
            insights.append(
                DomainInsight(
                    title="Customer authentication impact",
                    severity="high",
                    detail="Context indicates delayed OTP or authentication disruption affecting end users.",
                )
            )
        if "isolate" in combined:
            recommendations.append(
                DomainRecommendation(
                    priority=1,
                    action="Isolate the affected partner route and review signaling firewall controls.",
                )
            )
        if "audit logging" in combined or "approval" in combined:
            recommendations.append(
                DomainRecommendation(
                    priority=2,
                    action="Apply audit logging and approval checks before exporting customer-related metadata.",
                )
            )

        joined_snippets = " ".join(snippets)
        return DomainReport(
            domain=self.name,
            summary=(
                f"Telecom Security Agent response for query '{query}': "
                "Based on the retrieved context, the strongest matching evidence is: "
                f"{joined_snippets}"
            ),
            metrics=metrics,
            insights=insights,
            recommendations=recommendations,
            source_refs=source_refs,
        )
