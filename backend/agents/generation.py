from langchain.chains import RetrievalQA
from langchain_huggingface import HuggingFacePipeline

def generate_answer(db, query: str):
    """
    Take context from the vector DB + query, and generate a natural language answer.
    """
    llm = HuggingFacePipeline.from_model_id(
        model_id="gpt2",
        task="text-generation",
        pipeline_kwargs={"max_new_tokens": 64},
    )
    qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=db.as_retriever())
    result = qa_chain.invoke(query)
    if isinstance(result, dict):
        return result.get("result") or result.get("output_text") or str(result)
    return result
