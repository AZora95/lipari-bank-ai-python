# Giorno 10: l'immagine dell'API. uv serve a costruirla, non a farla girare
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS build
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=0
WORKDIR /app
# prima solo le dipendenze: finché il lock non cambia, questo strato resta in cache
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

FROM python:3.12-slim-bookworm
RUN useradd --create-home --uid 1000 app
WORKDIR /app
COPY --from=build /app/.venv /app/.venv
COPY alembic.ini ./
COPY alembic ./alembic
COPY src ./src
COPY scripts ./scripts
# il seed_all indicizza il corpus con la funzione degli eval: il modulo e i documenti
COPY evals/ingest_fixtures.py ./evals/
COPY data/docs ./data/docs
# l'agente avvia il server MCP come processo figlio: python -m liparibank_mcp.server
COPY liparibank_mcp ./liparibank_mcp
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
USER app
EXPOSE 8000
# graceful-timeout sotto lo stop_grace_period del compose: le richieste in corso finiscono
CMD ["gunicorn", "src.main:app", "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "2", "--bind", "0.0.0.0:8000", "--graceful-timeout", "30", "--timeout", "120"]
