import logging
import math
import re
import hashlib
import json
import os
from collections import Counter
from pathlib import Path
from typing import List, Sequence

from backend.core.documents import Document

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
QDRANT_STORAGE_DIR = Path(os.getenv("QDRANT_STORAGE_PATH", str(PROJECT_ROOT / "qdrant_storage")))

try:
    from langchain_core.embeddings import Embeddings as LangChainEmbeddings
except Exception:  # pragma: no cover - exercised through fallback tests
    LangChainEmbeddings = object

try:  # pragma: no cover - optional dependency for persistence path
    from qdrant_client import QdrantClient
    from qdrant_client.http.models import Distance, PointStruct, VectorParams
except Exception:  # pragma: no cover - handled through fallback tests
    QdrantClient = None
    Distance = None
    PointStruct = None
    VectorParams = None


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
    backend_name = "memory"

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
    backend_name = "langchain_embedding"

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


class QdrantPersistentVectorStore:
    backend_name = "qdrant_persistent"

    def __init__(
        self,
        documents: Sequence[Document],
        embeddings: SentenceTransformerEmbeddingsAdapter,
        collection_key: str,
        storage_dir: Path,
        force_reindex: bool = False,
        client=None,
        backend_name: str = "qdrant_persistent",
    ):
        if QdrantClient is None and client is None:
            raise RuntimeError("qdrant-client is not installed")

        self._documents = list(documents)
        self._embeddings = embeddings
        self._storage_dir = storage_dir
        self.backend_name = backend_name
        if client is None:
            self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._client = client or _build_qdrant_client(self._storage_dir)
        self._collection_name = _make_collection_name(collection_key, self._documents)
        self._content_hash = _documents_hash(self._documents)
        self._ensure_collection(force_reindex=force_reindex)

    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        query_vector = self._embeddings.embed_query(query)
        results = self._client.search(
            collection_name=self._collection_name,
            query_vector=query_vector,
            limit=k,
            with_payload=True,
        )
        documents: List[Document] = []
        for item in results:
            payload = item.payload or {}
            documents.append(
                Document(
                    page_content=str(payload.get("page_content", "")),
                    metadata=payload.get("metadata") or {},
                )
            )
        return documents

    def _ensure_collection(self, force_reindex: bool = False):
        if not force_reindex and _collection_matches(self._client, self._collection_name, self._content_hash, len(self._documents)):
            logger.info(
                "vector_store_strategy strategy=qdrant_persistent_reuse collection=%s documents=%s",
                self._collection_name,
                len(self._documents),
            )
            return

        vectors = self._embeddings.embed_documents([document.page_content for document in self._documents])
        _recreate_collection(self._client, self._collection_name, vector_size=len(vectors[0]) if vectors else 384)
        self._client.upsert(
            collection_name=self._collection_name,
            points=[
                PointStruct(
                    id=index,
                    vector=vector,
                    payload={
                        "page_content": document.page_content,
                        "metadata": document.metadata,
                        "content_hash": self._content_hash,
                    },
                )
                for index, (document, vector) in enumerate(zip(self._documents, vectors))
            ],
        )
        logger.info(
            "vector_store_strategy strategy=qdrant_persistent_indexed collection=%s documents=%s",
            self._collection_name,
            len(self._documents),
        )


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


def _documents_hash(chunks: Sequence[Document]) -> str:
    digest = hashlib.sha256()
    for document in chunks:
        digest.update(document.page_content.encode("utf-8"))
        digest.update(json.dumps(document.metadata, sort_keys=True, default=str).encode("utf-8"))
    return digest.hexdigest()


def _make_collection_name(collection_key: str, chunks: Sequence[Document]) -> str:
    stable_key = collection_key or _documents_hash(chunks)
    digest = hashlib.sha1(stable_key.encode("utf-8")).hexdigest()[:16]
    return f"looplamp_{digest}"


def _recreate_collection(client, collection_name: str, vector_size: int):
    try:
        client.delete_collection(collection_name=collection_name)
    except Exception:
        pass
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )


def _collection_matches(client, collection_name: str, content_hash: str, expected_count: int) -> bool:
    try:
        client.get_collection(collection_name=collection_name)
    except Exception:
        return False

    try:
        count_response = client.count(collection_name=collection_name, exact=True)
    except TypeError:
        count_response = client.count(collection_name=collection_name)
    if getattr(count_response, "count", 0) != expected_count:
        return False

    records, _ = client.scroll(
        collection_name=collection_name,
        limit=1,
        with_payload=True,
        with_vectors=False,
    )
    if not records:
        return False
    payload = records[0].payload or {}
    return payload.get("content_hash") == content_hash


def _build_qdrant_vector_store(chunks: Sequence[Document], collection_key: str = "", storage_dir: Path = QDRANT_STORAGE_DIR):
    if not chunks or QdrantClient is None or PointStruct is None or VectorParams is None or Distance is None:
        return None

    try:
        embeddings = SentenceTransformerEmbeddingsAdapter()
        client, backend_name = _resolve_qdrant_runtime(storage_dir)
        return QdrantPersistentVectorStore(
            documents=chunks,
            embeddings=embeddings,
            collection_key=collection_key,
            storage_dir=storage_dir,
            client=client,
            backend_name=backend_name,
        )
    except Exception as exc:
        logger.info(
            "vector_store_strategy strategy=fallback_from_qdrant reason=%s",
            exc.__class__.__name__,
        )
        return None


def build_vector_db(chunks: Sequence[Document], collection_key: str = "", force_reindex: bool = False):
    qdrant_store = _build_qdrant_vector_store(chunks, collection_key=collection_key, storage_dir=QDRANT_STORAGE_DIR) if not force_reindex else _build_qdrant_reindex_store(chunks, collection_key=collection_key)
    if qdrant_store is not None:
        return qdrant_store

    langchain_store = _build_langchain_vector_store(chunks)
    if langchain_store is not None:
        return langchain_store

    logger.info("vector_store_strategy strategy=lexical_fallback documents=%s", len(chunks))
    return InMemoryVectorStore(chunks)


def _build_qdrant_reindex_store(chunks: Sequence[Document], collection_key: str = "", storage_dir: Path = QDRANT_STORAGE_DIR):
    if not chunks or QdrantClient is None or PointStruct is None or VectorParams is None or Distance is None:
        return None

    try:
        embeddings = SentenceTransformerEmbeddingsAdapter()
        client, backend_name = _resolve_qdrant_runtime(storage_dir)
        return QdrantPersistentVectorStore(
            documents=chunks,
            embeddings=embeddings,
            collection_key=collection_key,
            storage_dir=storage_dir,
            force_reindex=True,
            client=client,
            backend_name=backend_name,
        )
    except Exception as exc:
        logger.info(
            "vector_store_strategy strategy=fallback_from_qdrant_reindex reason=%s",
            exc.__class__.__name__,
        )
        return None


def _resolve_qdrant_runtime(storage_dir: Path):
    qdrant_url = os.getenv("QDRANT_URL", "").strip()
    if qdrant_url:
        logger.info("vector_store_qdrant_runtime mode=server url=%s", qdrant_url)
        return _build_qdrant_client(storage_dir), "qdrant_server"
    logger.info("vector_store_qdrant_runtime mode=local path=%s", storage_dir)
    return _build_qdrant_client(storage_dir), "qdrant_persistent"


def _build_qdrant_client(storage_dir: Path):
    qdrant_url = os.getenv("QDRANT_URL", "").strip()
    qdrant_api_key = os.getenv("QDRANT_API_KEY", "").strip()
    if qdrant_url:
        kwargs = {"url": qdrant_url}
        if qdrant_api_key:
            kwargs["api_key"] = qdrant_api_key
        return QdrantClient(**kwargs)
    storage_dir.mkdir(parents=True, exist_ok=True)
    return QdrantClient(path=str(storage_dir))
