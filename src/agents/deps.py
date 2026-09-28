from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.db.repos import AccountRepository, MovementRepository
from src.db.session import get_db
from src.llm.embedding_client import EmbeddingClient
from src.services.alerts import AlertService
from src.services.retrieval_service import RetrievalService


@dataclass(frozen=True)
class Deps:
    accounts: AccountRepository
    movements: MovementRepository
    alerts: AlertService
    retrieval: RetrievalService
    embedder: EmbeddingClient
    openai: AsyncOpenAI  # il client grezzo: `complete` del Giorno 4 non ha i tool
    model: str


@lru_cache
def _openai_client() -> AsyncOpenAI:
    # uno per processo, riusato: il pool di connessioni vive nel client (Giorno 4)
    return AsyncOpenAI(api_key=settings.openai_api_key, timeout=20.0)


async def get_deps(db: Annotated[AsyncSession, Depends(get_db)]) -> Deps:
    return Deps(
        accounts=AccountRepository(db),
        movements=MovementRepository(db),
        alerts=AlertService(db),
        retrieval=RetrievalService(db),
        embedder=EmbeddingClient(),
        openai=_openai_client(),
        model=settings.default_model,
    )
