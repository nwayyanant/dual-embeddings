FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY services/frontend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services /app/services
EXPOSE 8084
# API_BASE will be injected by docker-compose (points to http://localhost:8083)
ENV API_BASE=http://localhost:8083
CMD ["uvicorn", "services.frontend.main:app", "--host", "0.0.0.0", "--port", "8084"]