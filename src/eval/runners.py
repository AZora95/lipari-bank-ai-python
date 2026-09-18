# src/eval/runners.py
import asyncio
import json
import time
from pathlib import Path
from typing import Any

from src.db.session import AsyncSessionLocal
from src.llm.client import Message
from src.llm.embedding_client import EmbeddingClient
from src.llm.factory import get_llm_provider
from src.services.categorize_service import CategorizeService
from src.services.retrieval_service import RetrievalService
from src.types.categorize import CategorizeRequest


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    raw = path.read_text(encoding="utf-8")
    return [json.loads(line) for line in raw.splitlines() if line.strip()]


async def eval_categorize(dataset_path: Path) -> dict[str, Any]:
    """Run categorize on dataset, return metrics."""
    examples = await asyncio.to_thread(_load_jsonl, dataset_path)
    service = CategorizeService()

    correct = 0
    failures = []
    total_latency = 0.0

    for ex in examples:
        req = CategorizeRequest(**ex["input"])

        start = time.time()
        result = await service.categorize(req)
        total_latency += time.time() - start

        is_correct = result.category == ex["expected"]["category"]
        if is_correct:
            correct += 1
        else:
            failures.append(
                {
                    "input": ex["input"],
                    "expected": ex["expected"],
                    "actual": result.model_dump(),
                }
            )

    n = len(examples)
    return {
        "accuracy": correct / n,
        "n_examples": n,
        "n_failures": len(failures),
        "avg_latency_s": total_latency / n,
        "failures": failures[:10],  # top 10 failures
    }


async def eval_rag(dataset_path: Path) -> dict[str, Any]:
    """Eval retrieval recall@1 and recall@5."""
    examples = await asyncio.to_thread(_load_jsonl, dataset_path)

    async with AsyncSessionLocal() as session:
        retrieval = RetrievalService(session, EmbeddingClient())

        correct_at_5 = 0
        correct_at_1 = 0

        for ex in examples:
            results = await retrieval.retrieve(ex["query"], top_k=5)
            doc_ids = [r.document_id for r in results]

            expected_doc = ex["expected_doc_id"]
            if expected_doc in doc_ids:
                correct_at_5 += 1
            if doc_ids and doc_ids[0] == expected_doc:
                correct_at_1 += 1

    n = len(examples)
    return {
        "recall_at_5": correct_at_5 / n,
        "recall_at_1": correct_at_1 / n,
        "n_examples": n,
    }


JUDGE_PROMPT = """Valuta se la risposta dell'assistente AI è adeguata.

DOMANDA: {question}
CONTESTO FORNITO: {context}
RISPOSTA: {answer}

Criteri:
1. Faithfulness: la risposta è basata sul contesto (no allucinazioni)?
2. Relevance: la risposta affronta la domanda?
3. Completeness: tutti i punti rilevanti sono coperti?
4. Citation: cita correttamente il documento?

Return only a valid JSON object without markdown delimiters and with these fields: faithfulness,
relevance, completeness, citation_correct, overall, reasoning.
"""


async def llm_judge(question: str, context: str, answer: str) -> dict[str, Any]:
    """Score a RAG answer with a judge model more capable than the generator."""
    llm = get_llm_provider("gpt-4o")
    response = await llm.complete(
        messages=[
            Message(
                role="user",
                content=JUDGE_PROMPT.format(question=question, context=context, answer=answer),
            )
        ],
        max_tokens=500,
    )
    return json.loads(response.content)


if __name__ == "__main__":
    result = asyncio.run(eval_categorize(Path("src/eval/datasets/categorize_golden.jsonl")))
    print(json.dumps(result, indent=2))

    THRESHOLD = 0.80
    if result["accuracy"] < THRESHOLD:
        print(f"FAIL: accuracy {result['accuracy']:.1%} < threshold {THRESHOLD:.0%}")
        raise SystemExit(1)
    print(f"OK: accuracy {result['accuracy']:.1%}")
