from typing import List

from backend.agents.base import DomainAgent
from backend.core.documents import Document


class TelecomSecurityAgent(DomainAgent):
    name = "telecom_security"

    def run(self, query: str, context_documents: List[Document]) -> str:
        if not context_documents:
            return (
                "I could not ground an answer in the retrieved context. "
                "Please ingest a document with telecom, security, or policy details."
            )

        snippets = []
        for document in context_documents[:3]:
            snippet = document.page_content.strip().replace("\n", " ")
            if len(snippet) > 220:
                snippet = f"{snippet[:217]}..."
            snippets.append(snippet)

        joined_snippets = " ".join(snippets)
        return (
            f"Telecom Security Agent response for query '{query}': "
            "Based on the retrieved context, the strongest matching evidence is: "
            f"{joined_snippets}"
        )
