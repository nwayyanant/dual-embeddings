try:
    from FlagEmbedding import FlagReranker
    import torch
    USE_RERANKER = True
except Exception:
    FlagReranker = None
    USE_RERANKER = False

class Reranker:
    def __init__(self, model_name="BAAI/bge-reranker-v2-m3"):
        print(f"🔍 USE_RERANKER is set to: {USE_RERANKER}")
        if USE_RERANKER:
            self.model = FlagReranker(model_name, use_fp16=True)
        else:
            self.model = None

    def rerank(self, query: str, candidates: list[dict], text_key="snippet", top_k=10) -> list[dict]:
        if not USE_RERANKER or not candidates:  # fallback: naive score
            return candidates[:top_k]
        pairs = [(query, c.get(text_key,"")) for c in candidates]
        scores = self.model.compute_score(pairs, normalize=True)
        for c, s in zip(candidates, scores):
            c["_rerank_score"] = float(s)
        return sorted(candidates, key=lambda x: x.get("_rerank_score", 0.0), reverse=True)[:top_k]