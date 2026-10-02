from typing import Any, Literal

from pydantic import BaseModel


class Message(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str


class LLMResponse(BaseModel):
    content: str
    tokens_used: int
    cost_eur: float
    model: str


class ToolSpec(BaseModel):
    """Un tool come lo vede il modello: il nome, a cosa serve, lo schema JSON degli argomenti."""

    name: str
    description: str
    parameters: dict[str, Any]
