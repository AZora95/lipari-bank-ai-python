from pathlib import Path

import pytest

from src.eval.runners import eval_categorize

pytestmark = pytest.mark.eval


async def test_categorize_accuracy_threshold() -> None:
    result = await eval_categorize(Path("src/eval/datasets/categorize_golden.jsonl"))
    assert result["accuracy"] >= 0.80, f"Accuracy: {result['accuracy']:.1%}"
