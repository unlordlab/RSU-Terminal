FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/main.py .

# NO exponer puerto fijo, Railway lo asigna
# EXPOSE 8000

# Usar $PORT que Railway asigna automáticamente
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
