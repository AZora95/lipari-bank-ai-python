from pathlib import Path

import pytest

from src.eval.runners import eval_rag

pytestmark = pytest.mark.eval


async def test_rag_recall_5() -> None:
    result = await eval_rag(Path("src/eval/datasets/rag_golden.jsonl"))
    assert result["recall_at_5"] >= 0.70
    assert result["recall_at_1"] >= 0.50  # top-1 più stringente
