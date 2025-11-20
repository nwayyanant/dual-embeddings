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


echo ">>> Waiting for services to be ready..."
wait_for_service "weaviate" "http://localhost:${WEAVIATE_HOST_PORT}/v1/.well-known/ready" 300
wait_for_service "ingestion" "http://localhost:${INGESTION_HOST_PORT}/health" 200
wait_for_service "embedding" "http://localhost:${EMBEDDING_HOST_PORT}/health" 200
wait_for_service "search" "http://localhost:${SEARCH_HOST_PORT}/health" 200

sleep 5  



echo ">>> Running ETL on ${CSV_PATH} -> ${OUT_PARQUET}"
curl -fsS -X POST http://localhost:${INGESTION_HOST_PORT}/ingest \
  -H "Content-Type: application/json" \
  -d "{\"csv_path\":\"${CSV_PATH}\",\"out_parquet\":\"${OUT_PARQUET}\"}"

echo ">>> Indexing embeddings with LaBSE (include_langs=${INCLUDE_LANGS})"
curl -fsS -X POST http://localhost:${EMBEDDING_HOST_PORT}/index \
  -H "Content-Type: application/json" \
  -d "{\"parquet_path\":\"${OUT_PARQUET}\",\"include_langs\":${INCLUDE_LANGS}}"



