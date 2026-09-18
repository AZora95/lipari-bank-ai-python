# AI Code Review L2 — RAGService

**Data**: ...
**File**: src/services/rag_service.py (95 LOC)
**Reviewer**: Claude 4

## Issue

| # | Severity | Tipo | Linea | Issue | Fix | Decisione |
|---|----------|------|-------|-------|-----|-----------|
| 1 | CRITICAL | prompt-injection | 32 | User question concatenato in prompt senza sanitize | Sanitize special tokens, separate via markdown | ✅ Fix |
| 2 | MAJOR | bug | 45 | top_k hardcoded 5, no config | Param da settings | ✅ Fix |
| 3 | MAJOR | grounding | 28 | System prompt non vincola hard a context | Strengthen "ESCLUSIVAMENTE da contesto" | ✅ Fix |
| 4 | MINOR | perf | - | Embedding non cached per same query | Hash query → cache 1h | ⏸ G7 |
| 5 | INFO | eval | - | Manca eval suite | Aggiunto in `eval/datasets/rag_golden.jsonl` | ✅ Done |

## What's done well

1. RAG pipeline pulita: retrieve → context build → generate.
2. Citation strutturata in response.
3. Empty result handling esplicito.
4. Cost tracking propagato.

Tempo speso: 55 min.