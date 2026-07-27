from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

def build_vector_db(chunks):
    # Use a free HuggingFace embedding model
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    db = Chroma.from_documents(chunks, embeddings)
    return db
