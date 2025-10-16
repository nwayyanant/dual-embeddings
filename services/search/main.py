# services/search/main.py
import os
import weaviate
import httpx
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from .language import detect_lang, strip_diacritics
from .rag import LLMProvider, build_prompt, make_bilingual_answer

WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
EMBEDDING_URL = os.getenv("EMBEDDING_URL", "http://embedding:8082")
CLASS = "Paragraph"

app = FastAPI(title="Semantic Search + RAG Service")

origins = os.getenv("CORS_ORIGINS", "http://localhost:8084,http://127.0.0.1:8084").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = weaviate.Client(WEAVIATE_URL)
llm = LLMProvider()

class SearchBody(BaseModel):
    query: str
    top_k: int = 10
    alpha: float = 0.5  # 0->BM25 only; 1->vector only

def build_snippet(o: dict) -> str:
    parts = [o.get("pali_paragraph"), o.get("translation_paragraph")]
    return " \n ".join([p for p in parts if p])

async def get_query_vector(q: str) -> list[float] | None:
    try:
        async with httpx.AsyncClient(timeout=30) as s:
            r = await s.post(f"{EMBEDDING_URL}/embed", json={"texts": [q], "normalize": True})
            r.raise_for_status()
            data = r.json()
            vectors = data.get("vectors") or []
            return vectors[0] if vectors else None
    except Exception:
        return None  # graceful degrade to BM25-only

@app.get("/")
def root():
    return {"service": "search", "status": "ok", "embedding_url": EMBEDDING_URL}

@app.post("/search")
async def search(body: SearchBody):
    try:
        lang = detect_lang(body.query)
        keyword_query = strip_diacritics(body.query) if lang == "pali" else body.query

        q_vec = await get_query_vector(body.query)

        q = client.query.get(
            CLASS, ["doc_id","book_id","para_id","pali_paragraph","translation_paragraph"]
        )
        if q_vec is not None:
            q = q.with_hybrid(query=keyword_query, alpha=body.alpha, vector=q_vec)
        else:
            q = q.with_hybrid(query=keyword_query, alpha=0.0)  # BM25-only fallback

        res = q.with_limit(max(100, body.top_k)).do()
        hits = [{"snippet": build_snippet(o), **o} for o in res["data"]["Get"][CLASS]]

        # Fallbacks if empty
        if not hits and q_vec is not None:
            vec_only = client.query.get(CLASS, ["doc_id","book_id","para_id","pali_paragraph","translation_paragraph"]) \
                        .with_hybrid(query="", alpha=1.0, vector=q_vec) \
                        .with_limit(max(100, body.top_k)).do()
            hits = [{"snippet": build_snippet(o), **o} for o in vec_only["data"]["Get"][CLASS]]

        return {"query_lang": lang, "alpha": body.alpha, "results": hits[:body.top_k]}
    
    except Exception as e:
            import traceback
            traceback.print_exc()
            return {"error": str(e)}
 
@app.post("/answer")
async def answer(body: SearchBody):
    search_res = await search(body)
    contexts = search_res["results"]
    target_lang = search_res["query_lang"]

    if llm.name != "none":
        prompt = build_prompt(body.query, contexts, target_lang)
        out = llm.generate(prompt)
    else:
        out = make_bilingual_answer(body.query, contexts, target_lang)

    return {"lang": target_lang, "answer": out, "citations": contexts[:min(10, len(contexts))]}