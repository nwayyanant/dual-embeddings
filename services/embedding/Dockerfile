# services/embedding/Dockerfile
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
# Hugging Face cache routed to a mounted volume to avoid container bloat
ENV HF_HOME=/hf-cache \
    TRANSFORMERS_CACHE=/hf-cache \
    SENTENCE_TRANSFORMERS_HOME=/hf-cache
# System deps (optional but helps torch wheels)
RUN apt-get update && apt-get install -y build-essential git && rm -rf /var/lib/apt/lists/*
COPY services/embedding/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install pyarrow
COPY services /app/services
COPY data /app/data
EXPOSE 8082
ENV WEAVIATE_URL=http://weaviate:8080
CMD ["uvicorn", "services.embedding.main:app", "--host", "0.0.0.0", "--port", "8082"]