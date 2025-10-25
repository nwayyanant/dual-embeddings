#!/usr/bin/env bash
set -euo pipefail

# Load .env if present
if [ -f ".env" ]; then
  set -a; source .env; set +a
else
  CSV_PATH=${CSV_PATH:-data/251005Tipitaka500lines.csv}
  OUT_PARQUET=${OUT_PARQUET:-data/out/normalized.parquet}
  INCLUDE_LANGS=${INCLUDE_LANGS:-'["multilingual"]'}
  ALPHA=${ALPHA:-0.5}
fi



pip install -r requirements.txt

echo ">>> Building and starting the stack..."
docker compose up -d --build

echo ">>> Waiting for Weaviate to be ready..."
for i in $(seq 1 60); do
  if curl -fsS http://localhost:8080/v1/.well-known/ready >/dev/null; then
    echo "Weaviate is ready."
    break
  fi
  sleep 2
done

sleep 5  
#echo "Initializing Weaviate schema..."
#python3 services/embedding/weaviate_schema.py


echo ">>> Running ETL on ${CSV_PATH} -> ${OUT_PARQUET}"
curl -fsS -X POST http://localhost:8081/ingest \
  -H "Content-Type: application/json" \
  -d "{\"csv_path\":\"${CSV_PATH}\",\"out_parquet\":\"${OUT_PARQUET}\"}"

echo ">>> Indexing embeddings with LaBSE (include_langs=${INCLUDE_LANGS})"
curl -fsS -X POST http://localhost:8082/index \
  -H "Content-Type: application/json" \
  -d "{\"parquet_path\":\"${OUT_PARQUET}\",\"include_langs\":${INCLUDE_LANGS}}"

echo ">>> Smoke tests: semantic search and RAG answer"
echo "Search: 'anicca'"
curl -fsS -X POST http://localhost:8083/search \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"anicca\",\"top_k\":5,\"alpha\":${ALPHA}}" | jq '.results[0:3][] | {doc_id,book_id,para_id}'

echo
echo "Answer: 'What is Abhidhamma?'"
curl -fsS -X POST http://localhost:8083/answer \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"What is Abhidhamma?\",\"top_k\":10,\"alpha\":${ALPHA}}" | jq '.answer[0:400]'

echo
echo ">>> Done. Try interactive docs:"
echo "  - Ingestion: http://localhost:8081/docs"
echo "  - Embedding: http://localhost:8082/docs"
echo "  - Search/RAG: http://localhost:8083/docs"
echo "  - Frontend UI: http://localhost:8084"
echo "      Type queries (e.g., 'anicca' or 'What is Abhidhamma?')"
echo "      Adjust Top-K and α, click Search and Ask (RAG).
