from backend.core.documents import Document
from backend.services import document_ingestion, vector_store


def test_build_vector_db_uses_fallback_store_when_langchain_backend_unavailable(monkeypatch):
    documents = [Document(page_content="refund policy applies to returns")]

    monkeypatch.setattr(vector_store, "_build_qdrant_vector_store", lambda chunks, collection_key="", storage_dir=None: None)
    monkeypatch.setattr(vector_store, "_build_qdrant_reindex_store", lambda chunks, collection_key="", storage_dir=None: None)
    monkeypatch.setattr(vector_store, "_build_langchain_vector_store", lambda chunks: None)

    store = vector_store.build_vector_db(documents)

    assert isinstance(store, vector_store.InMemoryVectorStore)


def test_build_vector_db_uses_langchain_store_when_available(monkeypatch):
    documents = [Document(page_content="ss7 anomaly detected")]

    class FakeStore:
        def similarity_search(self, query: str, k: int = 5):
            return documents[:k]

    fake_store = FakeStore()
    monkeypatch.setattr(vector_store, "_build_qdrant_vector_store", lambda chunks, collection_key="", storage_dir=None: None)
    monkeypatch.setattr(vector_store, "_build_qdrant_reindex_store", lambda chunks, collection_key="", storage_dir=None: None)
    monkeypatch.setattr(vector_store, "_build_langchain_vector_store", lambda chunks: fake_store)

    store = vector_store.build_vector_db(documents)

    assert store is fake_store


def test_build_vector_db_prefers_qdrant_store_when_available(monkeypatch):
    documents = [Document(page_content="refund policy applies to returns")]

    class FakeStore:
        def similarity_search(self, query: str, k: int = 5):
            return documents[:k]

    fake_store = FakeStore()
    monkeypatch.setattr(vector_store, "_build_qdrant_vector_store", lambda chunks, collection_key="", storage_dir=None: fake_store)

    store = vector_store.build_vector_db(documents, collection_key="sample:ecommerce:return_policy.md")

    assert store is fake_store


def test_build_vector_db_uses_qdrant_reindex_store_when_forced(monkeypatch):
    documents = [Document(page_content="refund policy applies to returns")]

    class FakeStore:
        backend_name = "qdrant_persistent"

        def similarity_search(self, query: str, k: int = 5):
            return documents[:k]

    fake_store = FakeStore()
    monkeypatch.setattr(vector_store, "_build_qdrant_reindex_store", lambda chunks, collection_key="", storage_dir=None: fake_store)

    store = vector_store.build_vector_db(documents, collection_key="sample:ecommerce:return_policy.md", force_reindex=True)

    assert store is fake_store


def test_resolve_qdrant_runtime_prefers_server_mode_when_url_present(monkeypatch, tmp_path):
    monkeypatch.setenv("QDRANT_URL", "http://qdrant:6333")
    monkeypatch.setattr(vector_store, "_build_qdrant_client", lambda storage_dir: object())

    client, backend_name = vector_store._resolve_qdrant_runtime(tmp_path / "qdrant_storage")

    assert client is not None
    assert backend_name == "qdrant_server"


def test_build_qdrant_client_uses_server_url(monkeypatch, tmp_path):
    calls = {}

    class FakeQdrantClient:
        def __init__(self, **kwargs):
            calls.update(kwargs)

    monkeypatch.setenv("QDRANT_URL", "http://qdrant:6333")
    monkeypatch.setenv("QDRANT_API_KEY", "secret")
    monkeypatch.setattr(vector_store, "QdrantClient", FakeQdrantClient)

    vector_store._build_qdrant_client(tmp_path / "qdrant_storage")

    assert calls["url"] == "http://qdrant:6333"
    assert calls["api_key"] == "secret"


def test_chunk_text_falls_back_when_langchain_splitter_missing(monkeypatch):
    monkeypatch.setattr(document_ingestion, "RecursiveCharacterTextSplitter", None)

    chunks = document_ingestion._chunk_text("alpha beta gamma delta epsilon", chunk_size=10, chunk_overlap=2)

    assert chunks
    assert all(hasattr(chunk, "page_content") for chunk in chunks)
