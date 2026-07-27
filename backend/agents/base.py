from abc import ABC, abstractmethod
from typing import List

from backend.core.documents import Document


class DomainAgent(ABC):
    name: str

    @abstractmethod
    def run(self, query: str, context_documents: List[Document]) -> str:
        raise NotImplementedError
