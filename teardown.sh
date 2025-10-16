#!/usr/bin/env bash
set -euo pipefail

echo "WARNING: This will stop and remove all Docker containers, networks, and volumes for this project."
echo "It will also delete generated data in data/out/ and the persisted Weaviate volume."
read -p "Are you sure you want to proceed? (Y/N): " confirm

if [[ "$confirm" != "Y" && "$confirm" != "y" ]]; then
  echo "Teardown aborted."
  exit 0
fi

echo ">>> Stopping and removing containers, networks, and volumes..."
docker compose down -v

# Remove generated data directory
OUT_DIR="data/out"
if [[ -d "$OUT_DIR" ]]; then
  echo ">>> Removing generated data directory: $OUT_DIR"
  rm -rf "$OUT_DIR"
else
  echo ">>> No generated data directory found at $OUT_DIR"
fi

# Confirm removal of named volume (already removed by -v)
echo ">>> Checking for leftover Docker volumes..."
if docker volume ls --format '{{.Name}}' | grep -q '^weaviate_data$'; then
  echo ">>> Removing leftover volume: weaviate_data"
  docker volume rm weaviate_data || true
else
  echo ">>> No leftover weaviate_data volume found."
fi

echo "Teardown completed successfully."
