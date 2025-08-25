import os
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

def _persist_dir() -> str:
    return os.getenv("PERSIST_DIR", os.path.join(os.path.dirname(__file__), "chroma_db"))

def _collection() -> str:
    return (os.getenv("COLLECTION_NAME", "infinitepay") or "infinitepay").strip()

def _embedding():
    model = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    return HuggingFaceEmbeddings(model_name=model)

def get_store() -> Chroma:
    persist_dir = _persist_dir()
    collection = _collection()
    emb = _embedding()
    return Chroma(
        embedding_function=emb,
        collection_name=collection,
        persist_directory=persist_dir,
    )

def retriever(k: int = 4):
    return get_store().as_retriever(search_kwargs={"k": k})

def similarity_search(query: str, k: int = 4):
    return get_store().similarity_search(query, k=k)
