# services/embedding/main.py
import os
import numpy as np
import pandas as pd
import weaviate
import uuid
from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from functools import lru_cache
from services.embedding.weaviate_schema import ensure_schema

WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
CLASS = "Paragraph"

app = FastAPI(title="Embedding & Indexer Service")

# Load once; cache vectors in-memory to avoid recompute for repeated queries
labse = SentenceTransformer("sentence-transformers/LaBSE")

def _encode(text: str) -> np.ndarray:
    return labse.encode([text or ""], normalize_embeddings=True, convert_to_numpy=True).astype(np.float32)[0]

# LRU cache for single-text vectors (default maxsize=4096; override via env)
@lru_cache(maxsize=int(os.getenv("EMBED_CACHE_SIZE", "4096")))
def encode_text_cached(text: str) -> bytes:
    # store as bytes to be cacheable; caller converts back to float32
    vec = _encode(text)
    return vec.tobytes()

def encode_list(texts):
    return labse.encode(texts, normalize_embeddings=True, convert_to_numpy=True).astype(np.float32)

class IndexBody(BaseModel):
    parquet_path: str
    batch_size: int = 5000
    include_langs: list[str] = ["multilingual"]  # keep default light

class EmbedBody(BaseModel):
    texts: list[str]
    normalize: bool = True

@app.get("/")
def root():
    return {"service": "embedding", "status": "ok"}

@app.post("/embed")
def embed(body: EmbedBody):
    """
    Returns vectors for input texts; uses LRU cache for single-item calls.
    """
    if not body.texts:
        return {"vectors": []}
    if len(body.texts) == 1:
        raw = encode_text_cached(body.texts[0])
        vec = np.frombuffer(raw, dtype=np.float32).tolist()
        return {"vectors": [vec]}
    # batch path (uncached)
    vecs = encode_list(body.texts).tolist()
    return {"vectors": vecs}

@app.post("/index")
def index(body: IndexBody):
    df = pd.read_parquet(body.parquet_path)
    print("Connecting to Weaviate...")
    client = weaviate.Client(WEAVIATE_URL)
    print("Connected. Ensuring schema...")
    ensure_schema(client, named_vectors=False)
    print("Schema setup complete.")

    text_for_vec = df["multilingual_concat"].fillna("").tolist()
    vecs = encode_list(text_for_vec)

    total = len(df)
    with client.batch as batch:
        batch.batch_size = 256
        for i in range(total):
            payload = {
                "doc_id": df.loc[i, "doc_id"],
                "book_id": df.loc[i, "book_id"],
                "para_id": df.loc[i, "para_id"],
                "pali_paragraph": df.loc[i, "pali_paragraph"] if "pali_paragraph" in df.columns else None,
                "pali_paragraph_ascii": df.loc[i, "pali_paragraph_ascii"] if "pali_paragraph_ascii" in df.columns else None,
                "translation_paragraph": df.loc[i, "translation_paragraph"] if "translation_paragraph" in df.columns else None,
                "translation_paragraph_ascii": df.loc[i, "translation_paragraph_ascii"] if "translation_paragraph_ascii" in df.columns else None,
                "multilingual_concat": df.loc[i, "multilingual_concat"],
            }
            stable_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, str(payload["doc_id"]))
            batch.add_data_object(
                data_object=payload,
                class_name=CLASS,
                uuid=str(stable_uuid),
                vector=vecs[i]
            )

    return {"message": "Index upsert complete", "count": total, "vector": "multilingual"}