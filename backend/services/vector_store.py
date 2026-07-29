import logging
import math
import re
from collections import Counter
from typing import List, Sequence

from backend.core.documents import Document

logger = logging.getLogger(__name__)

try:
    from langchain_core.embeddings import Embeddings as LangChainEmbeddings
except Exception:  # pragma: no cover - exercised through fallback tests
    LangChainEmbeddings = object


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


def _cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    numerator = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)


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


class SentenceTransformerEmbeddingsAdapter(LangChainEmbeddings):
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        self._model = SentenceTransformer(model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        vectors = self._model.encode(texts)
        return [vector.tolist() for vector in vectors]

    def embed_query(self, text: str) -> List[float]:
        vector = self._model.encode(text)
        return vector.tolist()


class LangChainEmbeddingVectorStore:
    def __init__(self, documents: Sequence[Document], embeddings: SentenceTransformerEmbeddingsAdapter):
        self._documents = list(documents)
        self._embeddings = embeddings
        self._vectors = embeddings.embed_documents([document.page_content for document in self._documents])

    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        query_vector = self._embeddings.embed_query(query)
        ranked = sorted(
            zip(self._documents, self._vectors),
            key=lambda item: _cosine_similarity(query_vector, item[1]),
            reverse=True,
        )
        return [document for document, _ in ranked[:k]]


def _build_langchain_vector_store(chunks: Sequence[Document]):
    try:
        embeddings = SentenceTransformerEmbeddingsAdapter()
    except Exception as exc:
        logger.info(
            "vector_store_strategy strategy=fallback reason=%s",
            exc.__class__.__name__,
        )
        return None

    logger.info(
        "vector_store_strategy strategy=langchain_embedding model=%s documents=%s",
        embeddings.model_name,
        len(chunks),
    )
    return LangChainEmbeddingVectorStore(chunks, embeddings)


def build_vector_db(chunks: Sequence[Document]):
    langchain_store = _build_langchain_vector_store(chunks)
    if langchain_store is not None:
        return langchain_store

    logger.info("vector_store_strategy strategy=lexical_fallback documents=%s", len(chunks))
    return InMemoryVectorStore(chunks)
