# services/search/Dockerfile
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY services/search/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Add torch and FlagEmbedding
# RUN pip install torch --index-url https://download.pytorch.org/whl/cpu
# RUN pip install FlagEmbedding

COPY services /app/services
EXPOSE 8083
ENV WEAVIATE_URL=http://weaviate:8080
ENV EMBEDDING_URL=http://embedding:8082
CMD ["uvicorn", "services.search.main:app", "--host", "0.0.0.0", "--port", "8083"]