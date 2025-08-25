import os, re, time, json
from typing import List, Dict
from urllib.parse import urlparse, urlunparse
import bleach

from app.rag.store import retriever as get_retriever

SUSPICIOUS = (
    "ignore previous", "system prompt", "jailbreak", "do anything",
    "por favor ignore", "resete as regras",
)

STOPWORDS_PT = {
    "a","o","os","as","um","uma","de","da","do","das","dos","em","no","na","nos","nas",
    "para","por","com","e","ou","se","que","qual","quais","como","quando","onde","porque",
    "porquê","sobre","ao","à","às","aos","minha","meu","meus","minhas","sua","seu","seus",
    "suas","esse","essa","isso","este","esta","isto","aquele","aquela","aquilo","já","não",
    "sim","também","mais","menos","até","sem","muito","pouco"
}
STOPWORDS_EN = {
    "the","a","an","and","or","to","for","of","in","on","at","by","with","from","as","is",
    "are","be","been","this","that","these","those","it","its","your","you","we","our"
}
STOPWORDS = STOPWORDS_PT | STOPWORDS_EN

def _normalize_url(u: str) -> str:
    if not u:
        return ""
    p = urlparse(u)
    p = p._replace(query="", fragment="")
    norm = urlunparse(p)
    if norm.endswith("/"):
        norm = norm[:-1]
    return norm

def _load_pages() -> List[str]:
    jf = os.getenv("PAGES_FILE", "").strip()
    if jf:
        try:
            with open(jf, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list) and data:
                return [str(u).strip() for u in data if str(u).strip()]
        except Exception:
            pass
    pages = []
    try:
        from app.rag.pages_auto import PAGES as PAGES_AUTO
        if isinstance(PAGES_AUTO, (list, tuple)):
            pages.extend([str(u).strip() for u in PAGES_AUTO])
    except Exception:
        pass
    if not pages:
        try:
            from app.rag.pages_manual import PAGES as PAGES_MAN
            if isinstance(PAGES_MAN, (list, tuple)):
                pages.extend([str(u).strip() for u in PAGES_MAN])
        except Exception:
            pass
    seen = set(); out = []
    for u in pages:
        u = (u or "").strip()
        if not u or u in seen:
            continue
        if urlparse(u).scheme in ("http","https"):
            seen.add(u); out.append(u)
    return out

def _tokenize(text: str) -> List[str]:
    text = text.lower()
    text = re.sub(r"[^0-9a-zá-úà-ùâ-ûã-õç]+", " ", text, flags=re.IGNORECASE)
    return [t for t in text.split() if t and t not in STOPWORDS and len(t) > 1]

def _extractive_answer(docs, max_chars: int = 900) -> str:
    parts = []
    for d in docs[:2]:
        txt = (d.page_content or "").replace("\n", " ").strip()
        if not txt:
            continue
        if len(txt) > 600:
            txt = txt[:600] + "..."
        parts.append(txt)
    if not parts:
        return "Não encontrei informações suficientes na Central de Ajuda."
    body = " ".join(parts).strip()
    if len(body) > max_chars:
        body = body[:max_chars] + "..."
    return body

def _dedupe_keep_order(items: List[str]) -> List[str]:
    seen = set(); out = []
    for x in items:
        if x and x not in seen:
            seen.add(x); out.append(x)
    return out

def knowledge_answer(message: str, user_id: str, conversation_id: str, log):
    \"\"\"Retorna (response_text, source_agent_response_text).\"\"\"
    t0 = time.perf_counter()

    msg = bleach.clean(message or "", tags=[], attributes={}, strip=True).strip()
    if any(tok in msg.lower() for tok in SUSPICIOUS):
        ms = int((time.perf_counter()-t0)*1000)
        log.warn({
            "agent":"KnowledgeAgent","conversation_id":conversation_id,
            "user_id":user_id,"execution_time":ms,"decision":"blocked"
        })
        return ("Não posso seguir instruções potencialmente maliciosas. Tente reformular.",
                f"Blocked suspicious message | time={ms}ms")

    pages = _load_pages()
    norm_pages = {_normalize_url(u): u for u in pages}
    if not pages:
        ms = int((time.perf_counter()-t0)*1000)
        log.error({"agent":"KnowledgeAgent","conversation_id":conversation_id,"user_id":user_id,
                   "execution_time":ms,"decision":"no_pages"})
        return ("Base de conhecimento não configurada (sem PAGES).",
                f"Sources: [] | time={ms}ms")

    k = int(os.getenv("RAG_K", "4") or "4")
    retr = get_retriever(k=k)
    try:
        docs = retr.invoke(msg)  # LC >= 0.2
    except Exception:
        docs = retr.get_relevant_documents(msg)  # fallback
    print(f\"[KnowledgeAgent] msg='{msg}' k={k} retrieved={len(docs)}\", flush=True)

    valid_docs = []
    valid_sources = []
    for d in docs:
        url = (d.metadata or {}).get("url") or (d.metadata or {}).get("source")
        nu = _normalize_url(url or "")
        if nu and nu in norm_pages:
            valid_docs.append(d)
            valid_sources.append(norm_pages[nu])

    valid_sources = _dedupe_keep_order(valid_sources)[:5]

    if not valid_docs:
        ms = int((time.perf_counter()-t0)*1000)
        print(f\"[KnowledgeAgent] no_valid_hits time={ms}ms\", flush=True)
        log.info({
            "agent":"KnowledgeAgent",
            "conversation_id":conversation_id,
            "user_id":user_id,
            "execution_time":ms,
            "sources":[],
            "decision":"no_valid_hits"
        })
        msg_out = ("Não encontrei informações suficientes na Central de Ajuda para essa pergunta. "
                   "Tente ser mais específico (ex.: 'taxas do link de pagamento').")
        return (msg_out, f"Sources: [] | time={ms}ms")

    ans = _extractive_answer(valid_docs, max_chars=int(os.getenv("MAX_SNIPPET_CHARS","900") or "900"))
    ms = int((time.perf_counter()-t0)*1000)
    print(f\"[KnowledgeAgent] ok sources={valid_sources} time={ms}ms\", flush=True)

    log.info({
        "agent":"KnowledgeAgent",
        "conversation_id":conversation_id,
        "user_id":user_id,
        "execution_time":ms,
        "sources":valid_sources,
        "decision":"vector_rag_validated"
    })

    fontes = "\\n".join(f"- {u}" for u in valid_sources) if valid_sources else "- (sem fonte detectada)"
    response = f\"{ans}\\n\\nFontes:\\n{fontes}\"
    details = f\"Docs={len(valid_docs)} | Sources: {valid_sources} | time={ms}ms\"
    return response, details
