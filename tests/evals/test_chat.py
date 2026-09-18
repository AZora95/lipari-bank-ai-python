from pathlib import Path

import pytest

from src.eval.runners import eval_chat_llm_judge

pytestmark = pytest.mark.eval


async def test_chat_judge_score_threshold() -> None:
    result = await eval_chat_llm_judge(Path("src/eval/datasets/chat_golden.jsonl"))
    assert result["avg_score"] >= 0.70, f"Avg judge score: {result['avg_score']:.2f}"
