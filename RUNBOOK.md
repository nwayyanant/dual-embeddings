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
  -d '{"csv_path":"data/251005Tipitaka500lines.csv","out_parquet":"data/out/normalized.parquet"}'
```

4. **Index embeddings**
```bash
curl -s -X POST http://localhost:8082/index \
  -H "Content-Type: application/json" \
  -d '{"parquet_path":"data/out/normalized.parquet","include_langs":["multilingual"]}'
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

