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

## Endpoint disponibili (Giorno 2)

### `POST /api/ai/chat` — echo (dummy)

```bash
curl -X POST localhost:8000/api/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"s-123","message":"Ciao!"}'
```

Risposta attesa:

```json
{
  "session_id": "s-123",
  "reply": "Echo: Ciao!",
  "tool_calls": [],
  "tokens_used": 10,
  "cost_eur": 0.0001,
  "model_used": "dummy",
  "created_at": "2026-01-01T10:00:00Z"
}
```

Un `message` vuoto o mancante restituisce `422` con il dettaglio del campo non valido.

### `POST /api/ai/categorize` — categorizzazione dummy per keyword

```bash
curl -X POST localhost:8000/api/ai/categorize \
  -H "Content-Type: application/json" \
  -d '{"description":"Bonifico Enel Energia","amount":100,"currency":"EUR"}'
```

Risposta attesa:

```json
{
  "category": "UTILITIES",
  "subcategory": "ENERGY",
  "confidence": 0.92,
  "reasoning": "Description contains utility keywords"
}
```

### Swagger UI

`http://127.0.0.1:8000/docs` — documentazione interattiva generata da FastAPI, con esempi di response cliccabili su `/api/ai/chat` (200/422/429).

## Una decisione di design

Sugli endpoint di oggi uso `response_model` esplicito (oltre al return type hint) invece di fidarmi solo di quest'ultimo: il return type hint è letto solo da mypy in fase di sviluppo, mentre `response_model` viene eseguito davvero da FastAPI a runtime — valida e filtra i campi della response, ed è anche la fonte dello schema mostrato in `/docs`. Su un endpoint pubblico li voglio entrambi: uno protegge mentre scrivo il codice, l'altro protegge il contratto quando il servizio gira davvero.

## Difetti dello starter del collega (Gino) trovati e corretti

Partendo dal codice fornito in `starter-collega-giorno2/` (vedi `starter_collega_giorno_02.zip` allegato all'assignment), sono stati trovati e corretti:

- **`AppException` rinominato in `AppError`** — le eccezioni custom in Python seguono la convenzione del suffisso `Error` (`ValueError`, `KeyError`, ecc.); `AppException` è ridondante col fatto di ereditare già da `Exception` ed è segnalato dalla regola ruff `N818`.
- **`response_model=ChatResponse` mancante** nell'endpoint `/api/ai/chat` di Gino — senza, lo schema di risposta in `/docs` risulta vuoto e FastAPI non valida/filtra l'output.
- **Errore mascherato da successo**: l'exception handler generico (`@app.exception_handler(Exception)`) restituiva `JSONResponse(content={"error": str(exc)})` senza `status_code`, quindi di default **200** anche per un errore interno — la "trappola numero uno" citata nel materiale del Giorno 2. Corretto con `status_code=500` e corpo coerente con gli altri handler (`timestamp`/`status`/`error`/`message`/`path`).
- **Chiamata HTTP sincrona e bloccante dentro un `async def`**: `src/api/users.py` usava `httpx.get(...)` (sincrono) dentro una funzione `async def`, bloccando l'intero event loop — e quindi tutte le altre richieste in corso — per la durata della chiamata esterna. Corretto con `httpx.AsyncClient` + `await`.
- **Sintassi Pydantic v1 silenziosamente ignorata**: `class Config: schema_extra = {...}` in `ChatResponse` non genera errore in Pydantic v2, ma viene ignorata (l'esempio Swagger che doveva produrre non viene applicato). Va scritta come `model_config = ConfigDict(json_schema_extra={...})`.
- **Tipi generici non specificati**: diversi punti (`list[dict]`, parametri e funzioni senza annotazione) non rispettavano `mypy strict`/`ruff --strict`: risolti specificando i tipi (es. `list[dict[str, str]]`, `-> None` sui costruttori, `Callable[[Request], Awaitable[Response]]` per `call_next`).

## Qualità del codice

```bash
uv run ruff check .
uv run ruff format .
uv run mypy .
```

## Variabili d'ambiente

Vedi [.env.example](.env.example) per l'elenco completo (DB, OpenAI, Anthropic, JWT). Il file `.env` reale non va mai committato.
