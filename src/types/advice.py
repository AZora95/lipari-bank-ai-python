from typing import Any, Literal

from pydantic import BaseModel, Field

# i livelli della matrice in src/auth/acl.py: un livello che non c'è nessun ruolo lo vedrebbe
Visibility = Literal["public", "internal", "risk_only", "compliance_only"]


class IngestRequest(BaseModel):
    document_id: str = Field(..., max_length=100)
    content: str = Field(..., min_length=10)
    metadata: dict[str, Any] | None = None
    visibility: Visibility = "public"


class IngestResponse(BaseModel):
    chunk_count: int
    embedding_dim: int


class AdviceRequest(BaseModel):
    question: str = Field(..., min_length=5, max_length=1000)


class Citation(BaseModel):
    document_id: str
    chunk_id: str
    excerpt: str
    similarity: float


class AdviceResponse(BaseModel):
    answer: str
    citations: list[Citation]
    tokens_used: int
    cost_eur: float
    rewritten_query: str | None = Field(
        None,
        description="La query con cui il sistema ha cercato:"
        "serve a capire le risposte fuori bersaglio",
    )
