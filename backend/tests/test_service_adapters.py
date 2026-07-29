from backend.core.documents import Document
from backend.services import document_ingestion, vector_store


def test_build_vector_db_uses_fallback_store_when_langchain_backend_unavailable(monkeypatch):
    documents = [Document(page_content="refund policy applies to returns")]

    monkeypatch.setattr(vector_store, "_build_langchain_vector_store", lambda chunks: None)

    store = vector_store.build_vector_db(documents)

    assert isinstance(store, vector_store.InMemoryVectorStore)


def test_build_vector_db_uses_langchain_store_when_available(monkeypatch):
    documents = [Document(page_content="ss7 anomaly detected")]

    class FakeStore:
        def similarity_search(self, query: str, k: int = 5):
            return documents[:k]

    fake_store = FakeStore()
    monkeypatch.setattr(vector_store, "_build_langchain_vector_store", lambda chunks: fake_store)

    store = vector_store.build_vector_db(documents)

    assert store is fake_store


def test_chunk_text_falls_back_when_langchain_splitter_missing(monkeypatch):
    monkeypatch.setattr(document_ingestion, "RecursiveCharacterTextSplitter", None)

    chunks = document_ingestion._chunk_text("alpha beta gamma delta epsilon", chunk_size=10, chunk_overlap=2)

    assert chunks
    assert all(hasattr(chunk, "page_content") for chunk in chunks)
