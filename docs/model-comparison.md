# Model comparison — categorize

Confronto tra `gpt-4o-mini`, `gpt-4o` e `claude-haiku-4-5-20251001` sul golden
dataset `src/eval/datasets/categorize_golden.jsonl`, tramite [scripts/compare_models.py](../scripts/compare_models.py):

```bash
uv run python scripts/compare_models.py
```

## ⚠️ Nessun numero reale in questo file

Questa tabella non è stata eseguita: `OPENAI_API_KEY` e `ANTHROPIC_API_KEY` in
`.env` sono ancora i placeholder (`sk-not-set-yet`), quindi non ci sono
credenziali per chiamare davvero le API. Non riporto numeri "plausibili" al
posto di una misura reale — l'intero punto dell'eval framework è avere un
numero che sai difendere, non uno inventato.

Per compilare la tabella:
1. Metti chiavi reali in `.env` (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`).
2. Assicurati che Postgres (pgvector) e Ollama (`nomic-embed-text`) siano attivi.
3. Esegui `uv run python scripts/compare_models.py` e incolla l'output qui sotto.

## Tabella (da compilare)

| Modello | Accuracy | Costo totale (€) | Latenza media (s) |
|---|---|---|---|
| gpt-4o-mini | | | |
| gpt-4o | | | |
| claude-haiku-4-5-20251001 | | | |

## Raccomandazione (da compilare dopo la run)

<!-- 2-3 righe: sweet spot costo/accuracy/latenza per un assistente bancario
che categorizza transazioni in produzione. -->
