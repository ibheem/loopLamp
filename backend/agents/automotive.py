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


class AutomotiveAgent(DomainAgent):
    name = "automotive"

    def run(self, query: str, context_documents: List[Document]) -> DomainReport:
        if not context_documents:
            return DomainReport(
                domain=self.name,
                summary=(
                    "I could not ground an answer in the retrieved context. "
                    "Please ingest a service manual, maintenance bulletin, or fault-code reference."
                ),
                insights=[
                    DomainInsight(
                        title="No grounded automotive evidence found",
                        severity="medium",
                        detail="The retrieval step did not return service, maintenance, or diagnostic context.",
                    )
                ],
                recommendations=[
                    DomainRecommendation(
                        priority=1,
                        action="Ingest an automotive service or diagnostic source before querying this domain.",
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

        if "dtc" in combined or "fault code" in combined or "p0" in combined:
            insights.append(
                DomainInsight(
                    title="Diagnostic fault context detected",
                    severity="high",
                    detail="Retrieved context includes trouble-code or diagnostic evidence relevant to root-cause analysis.",
                )
            )
            recommendations.append(
                DomainRecommendation(
                    priority=1,
                    action="Validate the fault code against the diagnostic steps before replacing parts or clearing the code.",
                )
            )
        if "maintenance" in combined or "inspection" in combined or "service interval" in combined:
            insights.append(
                DomainInsight(
                    title="Maintenance guidance present",
                    severity="medium",
                    detail="The retrieved material includes inspection or service-interval instructions relevant to the request.",
                )
            )
            recommendations.append(
                DomainRecommendation(
                    priority=2,
                    action="Map the cited maintenance actions to the current service schedule and inspection checklist.",
                )
            )
        if "brake" in combined or "engine" in combined or "coolant" in combined:
            insights.append(
                DomainInsight(
                    title="Vehicle subsystem evidence found",
                    severity="medium",
                    detail="Retrieved context references a specific subsystem that may guide repair or inspection decisions.",
                )
            )

        if not recommendations:
            recommendations.append(
                DomainRecommendation(
                    priority=1,
                    action="Review the cited automotive evidence and convert it into a step-by-step diagnostic or maintenance action.",
                )
            )

        metrics = [
            DomainMetric(name="matched_documents", value=str(len(context_documents)), unit="documents"),
            DomainMetric(name="matched_sources", value=str(len(source_refs)), unit="sources"),
        ]

        return DomainReport(
            domain=self.name,
            summary=(
                f"Automotive Agent response for query '{query}': "
                "Based on the retrieved context, the strongest matching evidence is: "
                f"{' '.join(snippets)}"
            ),
            metrics=metrics,
            insights=insights,
            recommendations=recommendations,
            source_refs=source_refs,
        )
