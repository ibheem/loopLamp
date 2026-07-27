import math
import re
from collections import Counter
from typing import Iterable, List, Sequence

from backend.core.documents import Document


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _score(query: str, content: str) -> float:
    query_tokens = _tokenize(query)
    content_tokens = _tokenize(content)
    if not query_tokens or not content_tokens:
        return 0.0

    query_counts = Counter(query_tokens)
    content_counts = Counter(content_tokens)
    overlap = sum(min(query_counts[token], content_counts[token]) for token in query_counts)
    density = overlap / math.sqrt(len(query_tokens) * len(content_tokens))
    phrase_bonus = 0.35 if query.lower() in content.lower() else 0.0
    return density + phrase_bonus


class InMemoryVectorStore:
    def __init__(self, documents: Sequence[Document]):
        self._documents = list(documents)

    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        ranked = sorted(
            self._documents,
            key=lambda document: _score(query, document.page_content),
            reverse=True,
        )
        return [document for document in ranked[:k] if _score(query, document.page_content) > 0]


def build_vector_db(chunks: Sequence[Document]) -> InMemoryVectorStore:
    return InMemoryVectorStore(chunks)
