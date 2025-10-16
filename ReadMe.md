
# What we’ll build


## Services (each independently scalable):

Ingestion & ETL – normalize CSV, create IDs, diacritic-aware fields.
Embedding – batch GPU embedding with LaBSE; supports Pāli/English/Chinese/Russian.
Indexer – push objects to Weaviate with named vectors.
Search API (FastAPI) – Hybrid retrieval (BM25 + vectors) + reranking + RAG answering with citations.
(Optional) Background queue – Celery/Redis for throughput & resiliency.



Key choices:

Weaviate with HNSW and named vectors (pali, en, zh, ru, and a multilingual fused vector).
Hybrid search: BM25 (keyword) + vector blending (alpha control).
Reranker: Local BAAI/bge-reranker-v2-m3 (strong multilingual cross-encoder).
RAG: Pluggable LLM (local or Azure/OpenAI), answer in user query language, with citations.



Data schema (current → future):

CSV: book_id, para_id, pali_paragraph, english_paragraph
Extend: chinese_paragraph, russian_paragraph (optional, may be empty initially)



How to run (dev)

Put CSV at ./data/<pali_english>.csv with columns:
book_id, para_id, pali_paragraph, english_paragraph
(Optional now: chinese_paragraph, russian_paragraph)
docker compose up -d --build
Call Ingestion to produce parquet.
Embedding worker watches for parquet path (via env/HTTP), computes vectors, upserts to Weaviate.
Query Search API:

POST http://localhost:8082/search with {"query":"anicca", "top_k":10}
POST http://localhost:8082/answer for RAG answer.