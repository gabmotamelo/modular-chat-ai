import os, sys, time, json, typing as t, requests
from urllib.parse import urlparse

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

if __package__ is None:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

def _try_import_pages() -> t.List[str]:
    try:
        from .pages_auto import PAGES
        if isinstance(PAGES, (list, tuple)) and PAGES:
            print("[indexer] loaded PAGES from .pages_auto")
            return list(PAGES)
    except Exception:
        pass
    try:
        from .pages_manual import PAGES
        if isinstance(PAGES, (list, tuple)) and PAGES:
            print("[indexer] loaded PAGES from .pages_manual")
            return list(PAGES)
    except Exception:
        pass
    try: # type: ignore
        if isinstance(PAGES, (list, tuple)) and PAGES:
            print("[indexer] loaded PAGES from app.rag.pages_auto")
            return list(PAGES)
    except Exception:
        pass
    try:
        from app.rag.pages_manual import PAGES
        if isinstance(PAGES, (list, tuple)) and PAGES:
            print("[indexer] loaded PAGES from app.rag.pages_manual")
            return list(PAGES)
    except Exception:
        pass
    return []

def load_pages() -> t.List[str]:
    jf = os.getenv("PAGES_FILE", "").strip()
    if jf:
        try:
            with open(jf, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                print(f"[indexer] loaded {len(data)} URLs from JSON:", jf)
                return [str(u).strip() for u in data if str(u).strip()]
        except Exception as e:
            print(f"[indexer] WARN: failed to read PAGES_FILE={jf}: {e}")
    pages = _try_import_pages()
    if pages:
        return pages
    print("[indexer] WARN: using fallback seed URLs")
    return [
        "https://ajuda.infinitepay.io/pt-BR/articles/4800276-quais-sao-as-taxas-do-link-de-pagamento",
        "https://ajuda.infinitepay.io/pt-BR/articles/4712034-como-funciona-a-calculadora-de-taxas-e-parcelas",
    ]

def html_to_text(html: str) -> str:
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        for tag in soup(["script","style","noscript"]):
            tag.decompose()
        main = soup.find("article") or soup.find("main") or soup
        txt = main.get_text(separator="\n", strip=True)
        lines = [ln.strip() for ln in txt.splitlines()]
        return "\n".join([ln for ln in lines if ln])
    except Exception:
        import re
        txt = re.sub(r"(?is)<(script|style|noscript).*?>.*?(</\1>)", " ", html)
        txt = re.sub(r"(?s)<[^>]+>", " ", txt)
        txt = re.sub(r"\s+", " ", txt).strip()
        return txt

def fetch(url: str, timeout: int) -> tuple[str, str]:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; RAG-Indexer/1.0)",
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
    }
    r = requests.get(url, headers=headers, timeout=timeout)
    r.raise_for_status()
    html = r.text
    title = ""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
    except Exception:
        pass
    return title, html_to_text(html)

def main():
    pages = load_pages()
    max_pages = int(os.getenv("MAX_PAGES","0") or "0")
    if max_pages > 0:
        pages = pages[:max_pages]
        print(f"[indexer] limiting to MAX_PAGES={max_pages} -> {len(pages)} URLs")

    seen, filtered = set(), []
    for u in pages:
        if not isinstance(u, str): 
            continue
        u = u.strip()
        if not u or u in seen: 
            continue
        pr = urlparse(u)
        if pr.scheme not in ("http","https"):
            continue
        filtered.append(u); seen.add(u)

    if not filtered:
        print("[indexer] ERROR: no URLs to index."); sys.exit(1)

    collection = (os.getenv("COLLECTION_NAME") or "infinitepay").strip()
    persist_dir = os.getenv("PERSIST_DIR") or os.path.join(os.path.dirname(__file__), "chroma_db")
    timeout = int(os.getenv("TIMEOUT","25") or "25")
    emb_model = os.getenv("EMBEDDING_MODEL") or "all-MiniLM-L6-v2"

    print(f"[indexer] URLs={len(filtered)} | collection={collection} | persist={persist_dir}")
    print(f"[indexer] EMBEDDING_MODEL={emb_model}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=200,
        separators=["\n\n","\n",". "," ",""]
    )
    docs: t.List[Document] = []
    ok=err=0

    for i, url in enumerate(filtered, 1):
        try:
            title, text = fetch(url, timeout)
            if not text or len(text) < 80:
                print(f"[indexer] WARN: short content → {url}")
                continue
            chunks = splitter.split_text(text)
            for ch in chunks:
                docs.append(Document(page_content=ch, metadata={"url": url, "title": title}))
            ok += 1
            print(f"[indexer] [{i}/{len(filtered)}] OK {url} → {len(chunks)} chunks")
        except Exception as e:
            err += 1
            print(f"[indexer] [{i}/{len(filtered)}] ERROR {url} → {e}")

    if not docs:
        print("[indexer] ERROR: 0 chunks produced."); sys.exit(2)

    print(f"[indexer] building embeddings for {len(docs)} chunks ...")
    t0 = time.time()
    emb = HuggingFaceEmbeddings(model_name=emb_model)
    vs = Chroma.from_documents(
        documents=docs,
        embedding=emb,
        collection_name=collection,
        persist_directory=persist_dir,
    )
    try:
        vs.persist()
    except Exception:
        pass
    dt = int((time.time()-t0)*1000)
    print(f"[indexer] DONE: {len(docs)} chunks from {ok} pages (errors={err}) in {dt} ms.")
    print(f"[indexer] store at: {persist_dir}")

if __name__ == "__main__":
    main()
