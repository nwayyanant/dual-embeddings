#!/usr/bin/env bash
set -euo pipefail

# Clone if not already present
if [ ! -d "dual-embeddings" ]; then
  echo "📥 Cloning repo..."
  git clone https://github.com/nwayyanant/dual-embeddings.git
  cd dual-embeddings
else
  cd dual-embeddings
  echo "🔄 Updating repo..."
  ./get_latest.sh
fi


# Reset docker (wipe old containers/volumes)
echo "♻️ Resetting Docker..."
./docker_reset.sh || true

# Bootstrap everything
echo "🚀 Bootstrapping services..."
./bootstrap.sh

echo "✅ All services are up! Try interactive docs:"
echo "   - Search/RAG: http://localhost:8083/docs"
echo "      Type queries (e.g., 'anicca' or 'Explain the Abhidhamma in brief')"
echo "      Adjust Top-K and α, click Search and Ask (RAG)."