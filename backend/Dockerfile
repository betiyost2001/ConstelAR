# backend/Dockerfile
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Agregamos postgresql-client para usar pg_isready
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      curl \
      build-essential \
      python3-dev \
      libffi-dev \
      postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN python -m pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Alembic y config
COPY alembic.ini ./alembic.ini
COPY alembic ./alembic

# Código
COPY app ./app

# Usuario no-root (opcional)
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# El compose sobreescribe el command para agregar el wait + alembic
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
