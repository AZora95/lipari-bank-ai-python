# LipariBank AI Assistant

Bootcamp Python AI Powered v1 — Lipari Consulting.

Backend FastAPI + Pydantic v2, gestito con `uv`. Il progetto cresce di giorno in giorno durante il bootcamp: ogni sessione aggiunge una feature a questo stesso repo.

## Requisiti

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) installato

## Setup

```bash
# clona il repo
git clone https://github.com/AZora95/lipari-bank-ai-python.git
cd lipari-bank-ai-python

# installa le dipendenze (crea automaticamente il virtualenv)
uv sync

# crea il file .env a partire dal template e valorizza le variabili
cp .env.example .env
```

## Avvio in sviluppo (hot reload)

```bash
uv run uvicorn src.main:app --reload
```

L'app parte su `http://127.0.0.1:8000`.

## Test rapido

```bash
curl http://127.0.0.1:8000/health
```

Risposta attesa:

```json
{
  "status": "UP",
  "timestamp": "2026-09-03T12:00:00+00:00",
  "app_name": "LipariBank AI",
  "version": "1.0.0"
}
```

## Qualità del codice

```bash
uv run ruff check .
uv run ruff format .
uv run mypy .
```

## Variabili d'ambiente

Vedi [.env.example](.env.example) per l'elenco completo (DB, OpenAI, Anthropic, JWT). Il file `.env` reale non va mai committato.
