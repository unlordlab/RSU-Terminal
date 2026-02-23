FROM python:3.11-slim

WORKDIR /app

# Copiar requirements primero (optimización)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código del backend
COPY main.py .

# Puerto que usará Railway
EXPOSE 8000

# Comando para iniciar
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
