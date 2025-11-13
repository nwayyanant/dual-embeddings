
# Pali–English Semantic Search: Runbook (Steps 1–9)

> This runbook explains how to **run and test** your local stack: Weaviate + Ingestion + Embedding + Search/RAG + Frontend UI.
> It assumes the repository layout already matches the files you have.

---

## 1) Prerequisites (local machine)

- **Docker** (Engine + Compose v2)
- **Bash** shell (for `bootstrap.sh`)
  - macOS/Linux: already present
  - Windows: use **Git Bash** or **WSL** (or follow *Manual run* in Step 6)
- **jq** (optional, used by `bootstrap.sh` to pretty‑print JSON)
  - macOS: `brew install jq`
  - Ubuntu: `sudo apt-get install -y jq`
  - Windows (Chocolatey): `choco install jq`

> If you don’t have `jq`, the bootstrap will error at pretty‑print lines (because `set -e` is on). Either install `jq` or run the manual commands in **Step 6**.

---

## 2) Project layout check

Ensure your working folder looks like this (key parts only):

```
pali-search/
  bootstrap.sh
  docker-compose.yml
  .env.sample
  services/
    ingestion/   # FastAPI for ETL
    embedding/   # FastAPI + LaBSE for indexing
    search/      # FastAPI + CORS + RAG fallback
    frontend/    # FastAPI UI
  data/
    251005Tipitaka500lines.csv
    MN5chunk.csv
```

> Your CSV must be at `data/251005Tipitaka500lines.csv`.

---

## 3) One‑click start (recommended)

1. **Optional**: copy env defaults

```bash
cp .env.sample .env
# .env defaults:
# CSV_PATH=data/251005Tipitaka500lines.csv
# OUT_PARQUET=data/out/normalized.parquet
# INCLUDE_LANGS='["multilingual"]'
# ALPHA=0.5
```

2. **Run the bootstrap**

```bash
bash bootstrap.sh
```

**What happens:**
- Builds & starts **Weaviate**, **ingestion**, **embedding**, **search**, **frontend**
- Waits for Weaviate health
- Runs **ETL** → `data/out/normalized.parquet`
- Runs **Indexing** (LaBSE → single `multilingual` vector per paragraph)
- Runs **smoke tests** (search + answer)
- Prints links:
  - Ingestion API docs: `http://localhost:8081/docs`
  - Embedding API docs: `http://localhost:8082/docs`
  - Search/RAG API docs: `http://localhost:8083/docs`
  - **Frontend UI**: `http://localhost:8084`

---

## 4) Use the Frontend UI

Open **`http://localhost:8084`** and try:

- Query examples:
  - **Pāli**: `anicca`
  - **English**: `What is Abhidhamma?`
- Adjust:
  - **Top‑K**: number of results
  - **α** (alpha): blend between BM25 (0) and vector (1); `0.5` is a good hybrid
- Click **Search**: ranked items show **Pāli + English** snippets.
- Click **Ask (RAG)**: Answer panel shows a **bilingual summary** + **citations** `[book_id:para_id]`.

---

## 5) Test via API (curl / Swagger)

### A) Swagger UIs
- Search/RAG: `http://localhost:8083/docs`
  - **POST /search**
    ```json
    {
      "query": "anicca",
      "top_k": 8,
      "alpha": 0.5
    }
    ```
    Check fields: `pali_paragraph`, `translation_paragraph`, `snippet`.
  - **POST /answer**
    ```json
    {
      "query": "What is Abhidhamma?",
      "top_k": 10,
      "alpha": 0.5
    }
    ```
    Check: `answer` (bilingual summary) and `citations` with `[book_id:para_id]`.

### B) curl examples

```bash
# SEARCH (English)
curl -s http://localhost:8083/search -H 'content-type: application/json' \
  -d '{"query":"What is Abhidhamma?","top_k":5,"alpha":0.5}' | jq .

# SEARCH (Pāli)
curl -s http://localhost:8083/search -H 'content-type: application/json' \
  -d '{"query":"anicca","top_k":5,"alpha":0.5}' | jq .

# ANSWER (RAG)
curl -s http://localhost:8083/answer -H 'content-type: application/json' \
  -d '{"query":"Explain the Abhidhamma in brief","top_k":8,"alpha":0.5}' | jq .

# Eample queries

# Search #1
curl -s http://localhost:8083/answer -H 'content-type: application/json' \
  -d '{"query":"Which 2 things suddenly happened to plants as a sign that the Buddha-to-be will soon become a Buddha?","top_k":8,"alpha":0.5}' | jq .

# Search #2
curl -s http://localhost:8083/answer -H 'content-type: application/json' \
  -d '{"query":"What was the kind of nutriment that an ascetic decided to eat, which helped him to then achieve psychic powers?","top_k":8,"alpha":0.5}' | jq .

curl -s http://localhost:8083/answer -H 'content-type: application/json' \
  -d '{"query":"In which ancient city was available abundance of precious stones?","top_k":8,"alpha":0.5}' | jq .

curl -s http://localhost:8083/answer -H 'content-type: application/json' \
  -d '{"query":"What is the meaning of Dhamma in the context of understanding reality as it is?","top_k":8,"alpha":0.5}' | jq .

curl -s http://localhost:8083/answer -H 'content-type: application/json' \
  -d '{"query":"What did the Buddha do, when he found out that deities still have a doubt about him?","top_k":8,"alpha":0.5}' | jq .


# Another Way of search 
curl -fsS -X POST http://localhost:8083/search \
  -H "Content-Type: application/json" \
  -d '{"query":"What is Abhidhamma?","top_k":5,"alpha":0.5}' | jq '.results[0:3][] | {doc_id, book_id, para_id}'

curl -fsS -X POST http://localhost:8083/answer \
  -H "Content-Type: application/json" \
  -d '{"query":"What is Abhidhamma?","top_k":10,"alpha":0.5}' | jq '.answer'

curl -fsS -X POST http://localhost:8083/answer \
  -H "Content-Type: application/json" \
  -d '{"query":"Which 2 things suddenly happened to plants as a sign that the Buddha-to-be will soon become a Buddha?","top_k":10,"alpha":0.5}' | jq '.answer'

  curl -fsS -X POST http://localhost:8083/answer \
  -H "Content-Type: application/json" \
  -d '{"query":"What was the kind of nutriment that an ascetic decided to eat, which helped him to then achieve psychic powers?","top_k":10,"alpha":0.5}' | jq '.answer'

  curl -fsS -X POST http://localhost:8083/answer \
  -H "Content-Type: application/json" \
  -d '{"query":"In which ancient city was available abundance of precious stones?","top_k":10,"alpha":0.5}' | jq '.answer'  

  curl -fsS -X POST http://localhost:8083/answer \
  -H "Content-Type: application/json" \
  -d '{"query":"What is the meaning of Dhamma in the context of understanding reality as it is?","top_k":10,"alpha":0.5}' | jq '.answer'  

  curl -fsS -X POST http://localhost:8083/answer \
  -H "Content-Type: application/json" \
  -d '{"query":"What did the Buddha do, when he found out that deities still have a doubt about him?","top_k":10,"alpha":0.5}' | jq '.answer'

```


# Using Swagger UI 

 go to: http://localhost:8083/search/docs 

 execute : 
 ```bash
 {
  "query": "Which 2 things suddenly happened to plants as a sign that the Buddha-to-be will soon become a Buddha?",
  "top_k": 8,
  "alpha": 1
 }
 ```
**What to check**
- `/search` returns **both** `pali_paragraph` and `translation_paragraph`.
- `/answer` shows a **summary** + **citations** with bilingual lines under each citation.

---

## 6) Manual run (without `bootstrap.sh`)

1. **Build & start**
```bash
docker compose up -d --build
```

2. **Wait for Weaviate**
```bash
curl -fsS http://localhost:8080/v1/.well-known/ready
```

3. **Run ETL**
```bash
curl -s -X POST http://localhost:8081/ingest \
  -H "Content-Type: application/json" \
  -d '{"csv_path":"data/MN5chunk.csv","out_parquet":"data/out/normalized.parquet"}'
```

4. **Index embeddings**
```bash
curl -s -X POST http://localhost:8082/index \
  -H "Content-Type: application/json" \
  -d '{"parquet_path":"data/out/normalized.parquet","include_langs":["multilingual"]}'

# with diacritics.parquet 20251019
curl -fsS -X POST http://localhost:8082/index \
   -H "Content-Type: application/json" \
   -d '{"parquet_path": "data/out/normalized_with_diacritics.parquet", "include_langs": ["multilingual"]}'
```

5. **Search / Answer** (use commands from Step 5)

6. **Frontend**: open `http://localhost:8084`

> **Windows (PowerShell)**: use `curl.exe` and careful quoting, or rely on Swagger UIs.

---

## 7) Troubleshooting

- **Ports busy**: Change port mappings in `docker-compose.yml`.
- **Weaviate not ready**: Bootstrap waits ~2 min. If still failing:
  ```bash
  docker compose logs -f weaviate
  ```
- **Indexing slow**: LaBSE on CPU is fine for thousands of rows. For millions, consider GPU later or keep single‑vector.
- **UI shows no results**:
  - Confirm indexing finished: `docker compose logs -f embedding`
  - Check ETL parquet: `ls data/out/normalized.parquet`
  - Try BM25‑only: set **α=0.0** in UI.
- **CORS issues**: Ensure `search` env has
  ```
  CORS_ORIGINS=http://localhost:8084,http://127.0.0.1:8084
  ```
- **Reset everything**:
  ```bash
  docker compose down -v
  rm -rf data/out
  ```
  Re‑run bootstrap.

---

## 8) What’s done vs next

**Done**
- End‑to‑end: **Ingest → Embed → Index → Search → RAG → UI**
- `/search`: always returns **Pāli + English**
- `/answer`: bilingual summary + citations even with `LLM_PROVIDER=none`

**Next**
- Switch to **named vectors** (Pāli/English/Multilingual) when ready
- Plug an **LLM provider** for generative answers
- Add **filters/facets** (e.g., by `book_id`)
- Extend to **Chinese/Russian** later (ETL + re‑index)

---

## 9) Validation checklist

- [ ] `http://localhost:8084` opens and searches work
- [ ] `/search` JSON includes **Pāli + English** per item
- [ ] `/answer` shows **Extractive bilingual answer** + **[book_id:para_id]** citations
- [ ] Changing **α** changes result mix (BM25 ↔ semantic)



# Summary of What we build


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
docker compose up -d --build or run bootstrap.sh in one go.
Call Ingestion to produce parquet.
Embedding worker watches for parquet path (via env/HTTP), computes vectors, upserts to Weaviate.

# Query Search API:

POST http://localhost:8082/search with {"query":"anicca", "top_k":10}
POST http://localhost:8082/answer for RAG answer.

# Using Swagger UI 

 go to: http://localhost:8083/docs 

 execte : 
 ```bash 
 {
  "query": "Which 2 things suddenly happened to plants as a sign that the Buddha-to-be will soon become a Buddha?",
  "top_k": 8,
  "alpha": 0.5 
}