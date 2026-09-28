from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from openai.types.chat import ChatCompletionToolParam
from pydantic import BaseModel


@dataclass(frozen=True)
class Tool:
    """Un tool esposto al modello: contratto pubblico più implementazione."""

    name: str
    description: str
    args_model: type[BaseModel]
    run: Callable[[Any], Awaitable[str]]  # riceve un'istanza di args_model, già validata
    scrive: bool = True  # chi non lo dichiara è trattato come chi scrive

    def to_openai_schema(self) -> ChatCompletionToolParam:
        schema = self.args_model.model_json_schema()
        schema.pop("title", None)
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": schema,
            },
        }
