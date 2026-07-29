from abc import ABC, abstractmethod
from typing import Dict, List

from backend.core.documents import Document
from backend.core.models import DomainReport


class DomainAgent(ABC):
    name: str

    @abstractmethod
    def run(self, query: str, context_documents: List[Document]) -> DomainReport:
        raise NotImplementedError

    def runtime_metadata(self) -> Dict[str, str]:
        return {
            "agent_type": self.__class__.__name__,
            "provider_mode": "deterministic",
            "provider_model": "",
            "used_fallback": "false",
        }
