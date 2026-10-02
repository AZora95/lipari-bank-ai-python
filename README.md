# LipariBank AI Assistant

Bootcamp Python AI Powered v1 — Lipari Consulting.

## Cosa fa

Un backend FastAPI per gli operatori di LipariBank:

1. **Advice:** risponde alle domande sulle policy della banca citando i documenti interni (RAG su pgvector). Prima di cercare riscrive la domanda.
2. **Permessi:** ogni ruolo vede solo i documenti del suo livello. Un operatore non cita mai i documenti riservati alla compliance.
3. **Agente:** consulta clienti, conti e movimenti con dei tool. Sopra 5.000 € un'azione si ferma e aspetta l'approvazione di un responsabile.
4. **Costi:** ogni chiamata al modello finisce in un registro, e solo il ruolo `risk_lead` ne vede il rapporto.
5. **Modelli e cache:** risposte e riscritture le genera Big Pickle via opencode (gratuito). Agente ed embedding girano in locale su Ollama. Redis evita di ricalcolare quello che si è già calcolato.

## Come si avvia

**Prerequisiti:**
- Docker con Compose v2 (Docker Desktop su Windows e macOS). Docker deve avere almeno **8 GB di RAM**, perché `qwen2.5:7b` da solo ne usa 5–6, e circa **12 GB di disco**.
- Le porte **8000** e **5432** libere. Se sul PC gira già un Postgres sulla 5432, va fermato.
- Per lo smoke test: `bash`, `curl` e `python` (qualunque Python 3). Su Windows vanno bene quelli di Git for Windows.

**1. Il file `.env`:**

```bash
cp .env.example .env          # PowerShell: Copy-Item .env.example .env
```

Le righe che contano sono tre:

| Riga | Cosa metterci |
|---|---|
| `JWT_SECRET` | **Obbligatoria da cambiare**: firma i token di login. Generala con `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `DEFAULT_MODEL` | Lascia `opencode-big-pickle`, che è gratuito e non vuole chiavi. In alternativa `gpt-4o-mini` oppure `claude-haiku-4-5-20251001` |
| `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` | Solo se in `DEFAULT_MODEL` hai messo un modello di quel fornitore. Con Big Pickle lasciale come sono |

Il resto del `.env` serve a chi sviluppa senza Docker (vedi sotto): il compose si imposta da solo indirizzi del database, di Redis, di Ollama e di opencode.

**2. L'avvio:**

```bash
docker compose up --build -d
docker compose ps             # pronto quando api è "healthy"
```

**La prima volta ci vogliono 15–30 minuti**, a seconda della rete. Si scaricano l'immagine di Ollama e i due modelli, `qwen2.5:7b` (4,7 GB) e `nomic-embed-text` (274 MB). Lo scaricamento si segue con `docker compose logs -f ollama-pull`. Dalla seconda volta l'avvio richiede pochi secondi.

All'avvio il compose, da solo:
- applica le migrazioni (`migrate`);
- crea i tre utenti e i conti di prova (`seed`);
- indicizza i documenti di `data/docs/` se l'indice è vuoto. Quelli in `data/docs/compliance_only/` sono riservati.

| Servizio | A cosa serve |
|---|---|
| `postgres` | Il database, con pgvector. È anche quello di `uv run`, sulla 5432 |
| `cache` | Redis: riscritture ed embedding già calcolati. Senza persistenza: un riavvio la svuota |
| `ollama` + `ollama-pull` | I modelli locali. `ollama-pull` scarica solo quelli che mancano |
| `opencode` | `opencode serve`, il server che porta a Big Pickle. Non è esposto fuori dal compose |
| `migrate`, `seed` | Partono, fanno il loro lavoro e si chiudono |
| `api` | L'applicazione, su <http://localhost:8000> (documentazione su <http://localhost:8000/docs>) |

**Utenti di prova** (password `bootcamp` per tutti):

| Utente | Ruolo |
|---|---|
| `mbianchi` | `operator` |
| `grossi` | `compliance_lead` |
| `lverdi` | `risk_lead` |

**Per spegnere:**
- `docker compose down`: i dati restano.
- `docker compose down -v`: cancella anche il database **e i modelli**, che al prossimo avvio si riscaricano.

## Come si verifica che funzioni

```bash
bash scripts/smoke.sh
```

**Su Windows** lancia il comando da un terminale **Git Bash**. In PowerShell `bash` è il lanciatore di WSL, non Git Bash: usa invece

```powershell
& "C:\Program Files\Git\bin\bash.exe" scripts/smoke.sh
```

Lo script attraversa il sistema intero:
- le due sonde;
- il login dei tre ruoli;
- un advice con citazione e riscrittura;
- i permessi sul documento riservato;
- l'agente;
- la cache;
- il registro dei costi.

Se tutto va bene finisce così:

```
  ok  vivo
  ok  pronto
  ...
  ok  Lucia vede il registro
smoke: tutto a posto
```

Due cose da sapere:
- **La prova dell'agente dipende dal modello, e fallisce spesso.** `qwen2.5:7b` a volte cerca il saldo senza prima cercare i conti del cliente. Allora lo script si ferma con `NO  agente: {...}` e una risposta tipo «Non riesco a trovare i dettagli del conto». Il sistema funziona, ha sbagliato il modello: rilancia lo script. Nelle prove passa circa una volta su tre. Se il messaggio è diverso, o se fallisce più di cinque volte di fila, guarda `docker compose logs api`.
- **Ogni domanda impiega qualche secondo, a volte di più:** Big Pickle è un servizio remoto gratuito. Un'API su un altro indirizzo si prova con `BASE=http://host:porta bash scripts/smoke.sh`.

Le due sonde, anche a mano:
- `curl localhost:8000/health`: il processo è vivo.
- `curl localhost:8000/ready`: il processo può servire traffico. Senza database risponde 503; se manca la cache, la segnala ma non risponde 503. In PowerShell il comando è `curl.exe`.

## Sviluppare senza Docker

Servono Python 3.12, [uv](https://docs.astral.sh/uv/) e, sul PC, Ollama (con `ollama pull nomic-embed-text` e `ollama pull qwen2.5:7b`) e [opencode](https://opencode.ai) avviato con `opencode serve --port 4096`.

```bash
uv sync
docker compose up -d postgres         # solo il database (se gira l'api del compose: docker compose stop api)
uv run alembic upgrade head
uv run python -m scripts.seed_all     # utenti, conti e indice dei documenti
uv run uvicorn src.main:app --reload
```

In questo modo valgono gli indirizzi del `.env`, cioè `localhost`. `REDIS_URL` resta vuota, e le cache restano nella memoria del processo.

## Test

I test girano su un database loro, `lipari_ai_test`, perché alcuni svuotano le tabelle. La CI lo indica con `TEST_DATABASE_URL`. La prima volta, e dopo ogni migrazione nuova:

```powershell
docker compose exec postgres psql -U lipari -d lipari_ai -c "CREATE DATABASE lipari_ai_test"   # solo la prima volta
$env:DATABASE_URL = "postgresql+asyncpg://lipari:lipari@localhost:5432/lipari_ai_test"   # bash: export DATABASE_URL=...
uv run alembic upgrade head
Remove-Item Env:DATABASE_URL                                                              # bash: unset DATABASE_URL
```

Poi:

```bash
uv run pytest -q --ignore=tests/test_g9.py
```

Stato noto:
- `tests/test_g9.py` non si carica ancora, perché manca `evals.runner.Spesa` del Giorno 9.
- Due test di `tests/unit/test_g7.py` falliscono.

Altri controlli:

```bash
docker compose exec api python -m scripts.bench_cache   # la cache degli embedding: serve Redis, quindi il compose
uv run python -m scripts.misura_tetti --salva           # p95 e costo medio dell'advice: la partenza
uv run python -m scripts.misura_tetti                   # dopo una modifica: il confronto con la partenza
```

## Qualità del codice

```bash
uv run ruff check .
uv run ruff format .
uv run mypy --explicit-package-bases src tests evals scripts liparibank_mcp
```

## Endpoint

| Metodo e percorso | Chi | Cosa fa |
|---|---|---|
| `GET /health`, `GET /ready` | tutti | Liveness e readiness |
| `POST /api/auth/login` | tutti | Form `username` + `password` → `access_token` |
| `POST /api/ai/advice` | con token | Domanda → risposta con citazioni |
| `POST /api/ai/agent` | con token | L'agente con i tool. `GET /api/ai/agent/{run_id}` per lo stato |
| `POST /api/ai/agent/{run_id}/approve` · `/reject` | `compliance_lead`, `risk_lead` | Decide un'azione in attesa. Chi l'ha chiesta non può deciderla |
| `POST /api/ai/supervisor` | con token | La stessa domanda divisa fra due specialisti |
| `POST /api/ai/chat` | tutti | Chat con l'assistente |
| `POST /api/ai/categorize` | tutti | Categoria di un movimento |
| `POST /api/ai/documents/ingest` | tutti | Indicizza un documento |
| `GET /api/admin/cost-report?dal=AAAA-MM-GG` | `risk_lead`, `admin` | Il registro dei costi, per modello, utente, endpoint e run |

## Una decisione di design

Sugli endpoint uso `response_model` esplicito (oltre al return type hint) invece di fidarmi solo di quest'ultimo: il return type hint è letto solo da mypy in fase di sviluppo, mentre `response_model` viene eseguito davvero da FastAPI a runtime — valida e filtra i campi della response, ed è anche la fonte dello schema mostrato in `/docs`. Su un endpoint pubblico li voglio entrambi: uno protegge mentre scrivo il codice, l'altro protegge il contratto quando il servizio gira davvero.

## Difetti dello starter del collega (Gino) trovati e corretti

Partendo dal codice fornito in `starter-collega-giorno2/` (vedi `starter_collega_giorno_02.zip` allegato all'assignment), sono stati trovati e corretti:

- **`AppException` rinominato in `AppError`** — le eccezioni custom in Python seguono la convenzione del suffisso `Error` (`ValueError`, `KeyError`, ecc.); `AppException` è ridondante col fatto di ereditare già da `Exception` ed è segnalato dalla regola ruff `N818`.
- **`response_model=ChatResponse` mancante** nell'endpoint `/api/ai/chat` di Gino — senza, lo schema di risposta in `/docs` risulta vuoto e FastAPI non valida/filtra l'output.
- **Errore mascherato da successo**: l'exception handler generico (`@app.exception_handler(Exception)`) restituiva `JSONResponse(content={"error": str(exc)})` senza `status_code`, quindi di default **200** anche per un errore interno — la "trappola numero uno" citata nel materiale del Giorno 2. Corretto con `status_code=500` e corpo coerente con gli altri handler (`timestamp`/`status`/`error`/`message`/`path`).
- **Chiamata HTTP sincrona e bloccante dentro un `async def`**: `src/api/users.py` usava `httpx.get(...)` (sincrono) dentro una funzione `async def`, bloccando l'intero event loop — e quindi tutte le altre richieste in corso — per la durata della chiamata esterna. Corretto con `httpx.AsyncClient` + `await`.
- **Sintassi Pydantic v1 silenziosamente ignorata**: `class Config: schema_extra = {...}` in `ChatResponse` non genera errore in Pydantic v2, ma viene ignorata (l'esempio Swagger che doveva produrre non viene applicato). Va scritta come `model_config = ConfigDict(json_schema_extra={...})`.
- **Tipi generici non specificati**: diversi punti (`list[dict]`, parametri e funzioni senza annotazione) non rispettavano `mypy strict`/`ruff --strict`: risolti specificando i tipi (es. `list[dict[str, str]]`, `-> None` sui costruttori, `Callable[[Request], Awaitable[Response]]` per `call_next`).

## Variabili d'ambiente

Vedi [.env.example](.env.example) per l'elenco completo. Il file `.env` reale non va mai committato.
