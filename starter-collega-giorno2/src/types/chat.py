from datetime import datetime

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="UUID o nuovo session")
    message: str = Field(..., min_length=1, max_length=2000)


class ToolCallInfo(BaseModel):
    name: str
    arguments: dict[str, str]
    result: str | None = None


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    tool_calls: list[ToolCallInfo] = Field(default_factory=list)
    tokens_used: int = Field(..., ge=0)
    cost_eur: float = Field(..., ge=0)
    model_used: str
    created_at: datetime

    class Config:
        schema_extra = {
            "example": {
                "session_id": "s-123",
                "reply": "Ciao! Come posso aiutarti?",
                "tool_calls": [],
                "tokens_used": 10,
                "cost_eur": 0.0001,
                "model_used": "dummy",
                "created_at": "2026-01-01T10:00:00Z",
            }
        }
