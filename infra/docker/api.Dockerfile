# Backend image: API, worker and Discord bot share this image.
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps kept minimal; asyncpg ships wheels.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Install the backend package first for better layer caching.
COPY packages/adf/pyproject.toml packages/adf/pyproject.toml
COPY packages/adf/adf packages/adf/adf
RUN pip install -e ./packages/adf

# Migrations + alembic config.
COPY alembic.ini alembic.ini
COPY packages/adf/migrations packages/adf/migrations

# Non-root user.
RUN useradd --create-home --uid 10001 appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=5 \
    CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["uvicorn", "adf.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
