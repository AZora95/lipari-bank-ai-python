# Starter del collega — Giorno 3 (SQLAlchemy 2.0 async + Alembic)

> *"Oggi ho attaccato la persistenza: engine async, i model `ChatSession`/`ChatMessage`, il `ChatRepository` e il `ChatService` che salva la conversazione. Sul mio locale la prima chat torna un session_id e vedo le righe nel DB. Poi però ho avuto qualche grattacapo che non ho avuto tempo di capire — provaci tu. — Gino"*

Questo è il codice che **Gino** ha iniziato per la persistenza di oggi. Puoi partire da qui — mettendo a posto quello che non gira come dovrebbe — oppure implementare da zero seguendo il Code Blueprint. È il lavoro di un collega alle prime armi: la prima chiamata sembra andare, ma appena provi a fare sul serio (secondo messaggio nella stessa sessione, rileggere lo storico, riavviare il server) qualcosa scricchiola.

## Cosa c'è dentro

Copia il codice dentro il tuo repo `lipari-bank-ai` (stessi package `src/...` dei giorni precedenti). Gino ha toccato:

- `src/db/session.py` — engine async, `AsyncSessionLocal`, dependency `get_db`
- `src/db/models.py` — i model `ChatSession` e `ChatMessage`
- `src/db/repos.py` — `ChatRepository` (create/find/add/list)
- `src/services/chat_service.py` — `ChatService`, la chat che ora persiste
- `src/api/chat.py` — endpoint `/api/ai/chat` che usa il DB + endpoint per rileggere lo storico di una sessione

I model Pydantic (`src/types/chat.py`) e le eccezioni (`src/exceptions.py`) vengono dai giorni precedenti e non sono inclusi: usali dal tuo repo.

## Prima di partire

Serve PostgreSQL+pgvector via Docker e la migration Alembic applicata (`alembic init`, poi `alembic revision --autogenerate -m "init"` e `alembic upgrade head`). Il Code Blueprint della giornata ha i comandi completi.

## Come si prova

```bash
docker compose up -d
uv run alembic upgrade head
uv run uvicorn src.main:app --reload

# 1) Prima chat: session nuova
curl -X POST localhost:8000/api/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"new","message":"Ciao!"}'

# 2) Secondo messaggio nella STESSA sessione (usa il session_id ricevuto sopra)
# 3) Rileggi lo storico:  GET /api/ai/chat/<session_id>/messages
# 4) Riavvia il server e controlla nel DB se i messaggi ci sono ancora.
```

## Il tuo compito

Esercita davvero il flusso (più messaggi nella stessa sessione, la rilettura dello storico, il riavvio del server con verifica su `psql`) e **individua e correggi ciò che non è a livello Lipari**. Per ogni cosa che sistemi, aggiungi una riga di spiegazione nel README del tuo progetto: cosa hai trovato, perché era un problema, come l'hai risolto.

> **I difetti che trovi e correggi valgono nella valutazione** (criterio premiale). Non ti diciamo quanti sono né dove stanno: è parte dell'esercizio scovarli.
