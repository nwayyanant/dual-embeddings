#!/usr/bin/env bash
set -euo pipefail

# Load .env if present
if [ -f ".env" ]; then
  set -a; source .env; set +a
else
  CSV_PATH=${CSV_PATH:-data/MN5chunk.csv}
  OUT_PARQUET=${OUT_PARQUET:-data/out/normalized.parquet}
  INCLUDE_LANGS=${INCLUDE_LANGS:-'["multilingual"]'}
  ALPHA=${ALPHA:-0.5}
  # Default ports
  WEAVIATE_HOST_PORT="${WEAVIATE_HOST_PORT:-8090}"
  WEAVIATE_GRPC_HOST_PORT="${WEAVIATE_GRPC_HOST_PORT:-50051}"
  INGESTION_HOST_PORT="${INGESTION_HOST_PORT:-8081}"
  EMBEDDING_HOST_PORT="${EMBEDDING_HOST_PORT:-8082}"
  SEARCH_HOST_PORT="${SEARCH_HOST_PORT:-8083}"
  FRONTEND_HOST_PORT=${FRONTEND_HOST_PORT:-8084}
fi    



wait_for_service() {
  local name="$1"
  local url="$2"
  local max_wait="${3:-120}"
  local waited=0
  local delay=2

  echo "⏳ Waiting for $name ($url)..."

  until curl -fsSL "$url" >/dev/null 2>&1; do
    sleep "$delay"
    waited=$((waited+delay))
    if [ "$waited" -ge "$max_wait" ]; then
      echo "❌ Timeout: $name not ready after ${max_wait}s" >&2
      exit 1
    fi
    if [ "$delay" -lt 10 ]; then
      delay=$((delay*2))
    fi
  done
  echo "✅ $name ready after ${waited}s."
}

pip install -r requirements.txt

echo ">>> Building and starting the stack..."
docker compose up -d --build


echo ">>> Waiting for services to be ready..."
wait_for_service "weaviate" "http://localhost:${WEAVIATE_HOST_PORT}/v1/.well-known/ready" 300
wait_for_service "ingestion" "http://localhost:${INGESTION_HOST_PORT}/health" 200
wait_for_service "embedding" "http://localhost:${EMBEDDING_HOST_PORT}/health" 200
wait_for_service "search" "http://localhost:${SEARCH_HOST_PORT}/health" 200

# for i in $(seq 1 60); do
  # if curl -fsS http://localhost:8080/v1/.well-known/ready >/dev/null; then
    # echo "Weaviate is ready."
    # break
  # fi
  # sleep 2
# done

sleep 5  
#echo "Initializing Weaviate schema..."
#python3 services/embedding/weaviate_schema.py

# chmod +x services/embedding/weaviate_schema.py
# ./services/embedding/weaviate_schema.py


echo ">>> Running ETL on ${CSV_PATH} -> ${OUT_PARQUET}"
curl -fsS -X POST http://localhost:${INGESTION_HOST_PORT}/ingest \
  -H "Content-Type: application/json" \
  -d "{\"csv_path\":\"${CSV_PATH}\",\"out_parquet\":\"${OUT_PARQUET}\"}"

echo ">>> Indexing embeddings with LaBSE (include_langs=${INCLUDE_LANGS})"
curl -fsS -X POST http://localhost:${EMBEDDING_HOST_PORT}/index \
  -H "Content-Type: application/json" \
  -d "{\"parquet_path\":\"${OUT_PARQUET}\",\"include_langs\":${INCLUDE_LANGS}}"

echo ">>> Smoke tests: semantic search and RAG answer"
echo "Search: 'anicca'"
curl -fsS -X POST http://localhost:${SEARCH_HOST_PORT}/search \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"anicca\",\"top_k\":5,\"alpha\":${ALPHA}}" 

echo
echo "Answer: 'What is Abhidhamma?'"
curl -fsS -X POST http://localhost:${SEARCH_HOST_PORT}/answer \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"What is Abhidhamma?\",\"top_k\":10,\"alpha\":${ALPHA}}"

echo
echo ">>> Done. Try interactive docs:"
echo "  - Search/RAG: http://localhost:${SEARCH_HOST_PORT}/docs"
echo "      Type queries (e.g., 'anicca' or 'What is Abhidhamma?')"
echo "      Adjust Top-K and α, click Search and Ask (RAG)."

