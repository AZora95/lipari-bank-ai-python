# Starter del collega — Giorno 2 (FastAPI + Pydantic v2 + REST)

> *"Ciao! Ho buttato giù la parte di oggi mentre ero un po' di corsa. Ci sono i primi endpoint del nostro `lipari-bank-ai`: la chat in modalità echo, la categorize dummy per keyword, i Pydantic model e la gestione errori nel `main.py`. Sul mio portatile parte e risponde, ma non ci metterei la mano sul fuoco: dagli un'occhiata prima di costruirci sopra. — Gino"*

Questo è il codice che **Gino** ha iniziato per la feature di oggi. Puoi partire da qui — trovando e sistemando quello che non convince — oppure implementare da zero seguendo il Code Blueprint della giornata. Se parti da qui, ricordati che è codice di un collega alle prime armi: funziona in apparenza, ma non è detto che sia fatto come lo faresti tu.

## Cosa c'è dentro

Il codice va copiato dentro il tuo repo `lipari-bank-ai` (usa gli stessi package `src/...` che hai già dal Giorno 1). Gino ha toccato:

- `src/types/chat.py` — i model `ChatRequest`, `ToolCallInfo`, `ChatResponse`
- `src/types/categorize.py` — i model della categorizzazione
- `src/types/error.py` — il model di errore globale
- `src/exceptions.py` — `AppException` e le sue sottoclassi
- `src/api/chat.py` — l'endpoint `/api/ai/chat` (echo)
- `src/api/categorize.py` — l'endpoint `/api/ai/categorize` (dummy)
- `src/api/users.py` — un endpoint di servizio che legge la directory utenti interna
- `src/main.py` — app, middleware, exception handler e registrazione dei router

## Come si prova

```bash
uv run uvicorn src.main:app --reload

curl -X POST localhost:8000/api/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"s-123","message":"Ciao!"}'

curl -X POST localhost:8000/api/ai/categorize \
  -H "Content-Type: application/json" \
  -d '{"description":"Bonifico Enel Energia","amount":100,"currency":"EUR"}'

# Apri anche http://localhost:8000/docs e guarda come vengono documentati gli endpoint.
```

## Il tuo compito

Fai girare il codice, mettilo alla prova (prova anche i casi limite: body non valido, errori imprevisti, cosa mostra Swagger, come si comporta sotto più richieste in parallelo) e **individua e correggi ciò che non è a livello Lipari**. Per ogni cosa che sistemi, aggiungi una riga di spiegazione nel README del tuo progetto: cosa hai trovato, perché era un problema, come l'hai risolto.

> **I difetti che trovi e correggi valgono nella valutazione** (criterio premiale). Non ti diciamo quanti sono né dove stanno: è parte dell'esercizio scovarli.
