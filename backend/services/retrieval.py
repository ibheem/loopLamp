from typing import List

from backend.core.documents import Document


def retrieve_context(db, query: str, k: int = 5) -> List[Document]:
    return db.similarity_search(query, k=k)


class RetrievalService:
    def retrieve(self, db, query: str, k: int = 5) -> List[Document]:
        return retrieve_context(db, query, k=k)
