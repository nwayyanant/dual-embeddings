# services/ingestion/Dockerfile
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY services/ingestion/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services /app/services
COPY data /app/data
EXPOSE 8081
CMD ["uvicorn", "services.ingestion.main:app", "--host", "0.0.0.0", "--port", "8081"]