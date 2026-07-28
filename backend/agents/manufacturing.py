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


class ManufacturingAgent(DomainAgent):
    name = "manufacturing"

    def run(self, query: str, context_documents: List[Document]) -> DomainReport:
        if not context_documents:
            return DomainReport(
                domain=self.name,
                summary=(
                    "I could not ground an answer in the retrieved context. "
                    "Please ingest a production log, SOP, or quality incident document."
                ),
                insights=[
                    DomainInsight(
                        title="No grounded manufacturing evidence found",
                        severity="medium",
                        detail="The retrieval step did not return production, SOP, or quality-control context.",
                    )
                ],
                recommendations=[
                    DomainRecommendation(
                        priority=1,
                        action="Ingest a manufacturing operations or quality document before querying this domain.",
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

        if "quality" in combined or "defect" in combined or "non-conformance" in combined:
            insights.append(
                DomainInsight(
                    title="Quality incident context detected",
                    severity="high",
                    detail="Retrieved context includes defect or non-conformance evidence relevant to corrective action.",
                )
            )
            recommendations.append(
                DomainRecommendation(
                    priority=1,
                    action="Open or update the corrective-action workflow and confirm root-cause ownership for the quality issue.",
                )
            )
        if "sop" in combined or "procedure" in combined or "work instruction" in combined:
            insights.append(
                DomainInsight(
                    title="Process guidance present",
                    severity="medium",
                    detail="The retrieved material includes operating procedure context relevant to production execution.",
                )
            )
            recommendations.append(
                DomainRecommendation(
                    priority=2,
                    action="Validate the current production step against the cited SOP or work instruction before restart.",
                )
            )
        if "downtime" in combined or "line" in combined or "throughput" in combined:
            insights.append(
                DomainInsight(
                    title="Production performance evidence found",
                    severity="medium",
                    detail="Retrieved context references line performance, downtime, or throughput signals relevant to operations review.",
                )
            )

        if not recommendations:
            recommendations.append(
                DomainRecommendation(
                    priority=1,
                    action="Review the cited manufacturing evidence and convert it into a production, quality, or process-control action.",
                )
            )

        metrics = [
            DomainMetric(name="matched_documents", value=str(len(context_documents)), unit="documents"),
            DomainMetric(name="matched_sources", value=str(len(source_refs)), unit="sources"),
        ]

        return DomainReport(
            domain=self.name,
            summary=(
                f"Manufacturing Agent response for query '{query}': "
                "Based on the retrieved context, the strongest matching evidence is: "
                f"{' '.join(snippets)}"
            ),
            metrics=metrics,
            insights=insights,
            recommendations=recommendations,
            source_refs=source_refs,
        )
