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


class MedicalQAAgent(DomainAgent):
    name = "medical_qa"

    def run(self, query: str, context_documents: List[Document]) -> DomainReport:
        if not context_documents:
            return DomainReport(
                domain=self.name,
                summary=(
                    "I could not ground an answer in the retrieved context. "
                    "Please ingest an authoritative medical guideline, textbook, or pharmacology reference."
                ),
                insights=[
                    DomainInsight(
                        title="No grounded medical evidence found",
                        severity="medium",
                        detail="The retrieval step did not return trusted clinical or pharmacology context.",
                    )
                ],
                recommendations=[
                    DomainRecommendation(
                        priority=1,
                        action="Ingest an authoritative medical document before asking healthcare questions.",
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

        if "pharmacology" in combined or "drug" in combined or "medication" in combined:
            insights.append(
                DomainInsight(
                    title="Pharmacology evidence located",
                    severity="medium",
                    detail="Retrieved context contains medication or drug-mechanism information relevant to the question.",
                )
            )
        if "treatment" in combined or "clinical" in combined or "disease" in combined:
            insights.append(
                DomainInsight(
                    title="Clinical guidance context present",
                    severity="medium",
                    detail="Retrieved material includes clinical concepts or treatment-oriented evidence relevant to the query.",
                )
            )

        recommendations.append(
            DomainRecommendation(
                priority=1,
                action="Use the cited medical sources as reference material and verify final decisions through qualified clinical review.",
            )
        )
        recommendations.append(
            DomainRecommendation(
                priority=2,
                action="Cross-check the retrieved sections for disease-specific or medication-specific contraindications before applying guidance.",
            )
        )

        metrics = [
            DomainMetric(name="matched_documents", value=str(len(context_documents)), unit="documents"),
            DomainMetric(name="matched_sources", value=str(len(source_refs)), unit="sources"),
        ]

        return DomainReport(
            domain=self.name,
            summary=(
                f"Medical Q&A Agent response for query '{query}': "
                "Based on the retrieved context, the strongest matching evidence is: "
                f"{' '.join(snippets)}"
            ),
            metrics=metrics,
            insights=insights,
            recommendations=recommendations,
            source_refs=source_refs,
        )
