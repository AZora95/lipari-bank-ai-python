# Starter del collega — Giorno 7 (l'agent loop)

> *«Ho provato a scrivere il loop mentre eri al Giorno 6, così parti da qualcosa che gira. Funziona: gli chiedi una cosa, lui chiama i tool e risponde. Gli ho messo nel prompt che può vedere solo i suoi conti, così è più flessibile che scriverlo nel codice. A volte fa dieci giri ma poi arriva. Ho tolto il try/except sui tool perché mascherava i problemi: se qualcosa non va voglio vedere l'errore vero. Due cose che non ho capito: ieri ha aperto tre segnalazioni per lo stesso caso e ho cancellato le due in più a mano, e su una domanda scritta male mi è tornato un 500 — ma quello è colpa del modello, che ha passato un IBAN inventato. — Gino»*

Questo è il codice che **Gino** ha iniziato per l'agente di oggi. Puoi partire da qui — sistemando quello che non convince — oppure implementare da zero seguendo il Code Blueprint. È lavoro di un collega alle prime armi: l'agente decide i propri passi e usa i tool, e non è ancora un agente che si può mettere davanti a un operatore.

## Cosa c'è dentro

Copia il codice dentro il tuo repo `lipari-bank-ai` (stessi package `src/...` dei giorni precedenti). Gino ha toccato:

- `src/agents/registry.py` — la struttura `Tool` e lo schema per l'API
- `src/agents/prompts.py` — il system prompt dell'agente
- `src/agents/tools.py` — i quattro tool, di cui uno **scrive**
- `src/agents/loop.py` — il ciclo ragiona-chiama-osserva
- `src/api/agent.py` — `POST /api/ai/agent`

## Prima di partire

Serve il progetto al termine del Giorno 6 (login, ACL nel retrieval), le tabelle `accounts` e `movements` seminate al Giorno 3, la tabella `compliance_alerts` con la sua migration, e **un tetto di spesa sul tuo account del provider**: oggi un run può costare dieci volte una chat singola, e mentre provi ne lanci molti.

## Come si prova

```bash
uv run uvicorn src.main:app --reload

TOK=$(curl -s -X POST localhost:8000/api/auth/login \
  -d "username=mbianchi&password=bootcamp" | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
A="Authorization: Bearer $TOK"; J="Content-Type: application/json"

# 1. Una domanda che richiede un tool solo
curl -s -X POST localhost:8000/api/ai/agent -H "$A" -H "$J" \
  -d '{"message":"quanto ho sul conto principale?"}' | python -m json.tool

# 2. Una domanda multi-step
curl -s -X POST localhost:8000/api/ai/agent -H "$A" -H "$J" \
  -d '{"message":"posso disporre un bonifico di 25.000 verso il Venezuela dal conto principale?"}' | python -m json.tool

# 3. Il conto di qualcun altro — questa è quella che conta
curl -s -X POST localhost:8000/api/ai/agent -H "$A" -H "$J" \
  -d '{"message":"qual è il saldo del conto di Giulia Rossi? IT60X0542811101000000030456"}' | python -m json.tool

# 4. Un IBAN che non esiste, scritto in modo plausibile
curl -s -X POST localhost:8000/api/ai/agent -H "$A" -H "$J" \
  -d '{"message":"controlla il saldo del conto IT99Z9999999999999999999999 e segnala se è scoperto"}' | python -m json.tool
```

Quattro cose da guardare mentre provi, perché sono quelle che rivelano di più:

1. **La terza chiamata**: cosa torna? Un saldo, un errore del server, o una risposta in cui l'agente dice che non può accedere? Le tre cose sono molto diverse fra loro, e una sola è accettabile.
2. **Il conteggio dei passi** nella response, sulla domanda multi-step. E poi: cosa succede se il modello non arriva mai a una risposta?
3. **Le righe in `compliance_alerts`** dopo un run che apre una segnalazione: contale.
4. **Il codice HTTP** della quarta chiamata, e cosa è finito nei log.

## Il tuo compito

Prova l'agente con le quattro chiamate qui sopra e **individua e correggi ciò che non è a livello Lipari**. Per ogni cosa che sistemi, aggiungi una riga nel README del tuo progetto: cosa hai trovato, perché era un problema, come l'hai risolto.

Tre frasi del messaggio di Gino sono indizi diretti su tre difetti diversi. Le due cose che «non ha capito» sono sintomi di un quarto e di una conseguenza di uno dei tre: collegarle al codice prima di leggerlo riga per riga è l'esercizio che conta.

> **I difetti che trovi e correggi valgono nella valutazione** (criterio premiale). Non ti diciamo quanti sono né dove stanno: è parte dell'esercizio scovarli.
