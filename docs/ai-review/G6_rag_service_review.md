# AI Code Review L4 — RAGService

**Data**: 2026-09-18
**File**: src/services/rag_service.py (69 LOC)
**Reviewer**: Claude Sonnet 5

## Issue

| # | Severity | Tipo | Linea | Issue | Fix | Decisione |
|---|----------|------|-------|-------|-----|-----------|
| 1 | CRITICAL | authz | `src/api/advice.py:23` (`/documents/ingest`) | L'endpoint di ingest non ha alcun controllo di autenticazione/autorizzazione: chiunque può inserire "documenti" arbitrari nel vector store. Combinato con #2, un contenuto malevolo ingestato diventa contesto "fidato" citato come fonte ufficiale ad altri utenti. | Proteggere l'endpoint con auth (il progetto ha già `JWT_SECRET` in config ma non è usato da nessuna route) e limitarlo a ruoli admin/back-office. | ⏸ G7 |
| 2 | MAJOR | prompt-injection | `rag_service.py:38-43` | `req.question` e il contenuto dei chunk recuperati vengono interpolati in un unico blocco di testo senza delimitatori strutturali tra "contesto non fidato" e "domanda". Un chunk compromesso (vedi #1) o una domanda con istruzioni ("ignora il contesto e...") non è isolato dal resto del prompt. | Isolare context/domanda con tag espliciti (es. `<context>...</context>`, `<question>...</question>`) e rafforzare nel system prompt l'istruzione a trattare il contenuto tra i tag come dato, non come istruzioni. | ⏸ G7 |
| 3 | MAJOR | config | `rag_service.py:19`, `rag_service.py:50` | `top_k=5` e `max_tokens=800` hardcoded: non tunabili per ambiente/caso d'uso senza modificare il codice. | Spostare in `settings` (es. `rag_top_k`, `rag_max_tokens`). | ✅ Fix |
| 4 | MINOR | perf | `src/services/retrieval_service.py` (`embed_one`) | Nessuna cache sull'embedding per query identiche: ogni domanda ripetuta rifà la chiamata a Ollama. | Hash della query → cache in-memory/Redis con TTL 1h. | ⏸ G7 |
| 5 | INFO | eval | - | Mancava una eval suite per RAG/categorize/chat. | Aggiunto oggi: `src/eval/datasets/{categorize,rag,chat}_golden.jsonl` + `src/eval/runners.py` (`eval_categorize`, `eval_rag`, `eval_chat_llm_judge`) + test in `tests/evals/`. | ✅ Done |

## Correzione rispetto al template G6

Il template di riferimento assumeva un problema di *grounding* ("system prompt non vincola hard a context"). Non è confermato su questo codebase: `src/prompts/advice_system_v1.md` impone già "Risponda ESCLUSIVAMENTE sulla base dei contesti forniti", richiede la dichiarazione esplicita quando l'informazione non è presente, obbliga la citazione `[doc_id: ...]` per ogni affermazione e vieta di rivelare istruzioni interne anche se richiesto esplicitamente. Questo vincolo è più stringente di quanto previsto dal template — spostato quindi in "what's done well" invece che tra gli issue.

La query SQL in `retrieval_service.py` (ricerca pgvector) usa correttamente bind parameter (`:query_emb`) e non concatenazione di stringhe: nessun rischio di SQL injection lì, nonostante l'uso di `text()` raw.

## What's done well

1. RAG pipeline pulita: retrieve → context build → generate.
2. Citation strutturata in response, con similarity per chunk.
3. Empty result handling esplicito: evita una chiamata LLM inutile quando non ci sono chunk pertinenti.
4. Cost tracking (`cost_eur`, `tokens_used`) propagato end-to-end dalla risposta LLM alla response API.
5. System prompt (`advice_system_v1.md`) con grounding stringente, citazioni obbligatorie e no-leak delle istruzioni interne — più robusto del previsto.

Tempo speso: 40 min.
