FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primeiro (cache de layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo o código
COPY . .

# Comando de start
CMD ["python", "-m", "apps.worker.worker"]
