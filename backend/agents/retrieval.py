def retrieve_context(db, query: str, k: int = 5):
    """
    Fetch top-k chunks from the vector DB based on similarity search.
    """
    return db.similarity_search(query, k=k)
