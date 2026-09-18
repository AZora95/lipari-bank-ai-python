"""Confronta accuracy/costo/latenza di eval_categorize su più modelli.

Richiede OPENAI_API_KEY e ANTHROPIC_API_KEY reali in .env (non i placeholder
"sk-not-set-yet") e un DATABASE_URL raggiungibile.

Uso: uv run python scripts/compare_models.py
"""

import asyncio
from pathlib import Path

from src.eval.runners import eval_categorize

MODELS_TO_TEST = ["gpt-4o-mini", "gpt-4o", "claude-haiku-4-5-20251001"]
DATASET = Path("src/eval/datasets/categorize_golden.jsonl")


async def main() -> None:
    print(f"{'model':<28} {'accuracy':>10} {'cost_eur':>10} {'latency_s':>10}")
    for model in MODELS_TO_TEST:
        result = await eval_categorize(DATASET, model=model)
        print(
            f"{model:<28} {result['accuracy']:>9.2%} "
            f"{result['total_cost']:>9.4f} {result['avg_latency_s']:>9.2f}"
        )


if __name__ == "__main__":
    asyncio.run(main())
