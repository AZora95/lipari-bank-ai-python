from decimal import Decimal
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.deps import UserContext, get_current_user
from src.cache import get_redis
from src.config import settings
from src.db.session import get_db
from src.llm.client import LLMProvider
from src.llm.embedding_client import EmbeddingClient
from src.llm.factory import get_embedder, get_llm_provider
from src.llm.rewriter import QueryRewriter
from src.observability.ledger import CostLedger
from src.services.ingest_service import IngestService
from src.services.rag_service import RAGService
from src.services.retrieval_service import RetrievalService
from src.types.advice import AdviceRequest, AdviceResponse, IngestRequest, IngestResponse

router = APIRouter(prefix="/api/ai", tags=["Advice"])

REWRITER_SYSTEM = (Path(__file__).parent.parent / "prompts" / "rewriter_system.md").read_text(
    encoding="utf-8"
)


def get_rewriter() -> QueryRewriter:
    return QueryRewriter(get_llm_provider(), REWRITER_SYSTEM, cache=get_redis())


@router.post("/advice", response_model=AdviceResponse)
async def advice(
    req: AdviceRequest,
    user: Annotated[UserContext, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],  # la stessa sessione del servizio
    rewriter: Annotated[QueryRewriter, Depends(get_rewriter)],
    llm: Annotated[LLMProvider, Depends(get_llm_provider)],
    embedder: Annotated[EmbeddingClient, Depends(get_embedder)],
) -> AdviceResponse:
    rag = RAGService(
        rewriter=rewriter,
        embedder=embedder,
        retrieval=RetrievalService(session, embedder),
        llm=llm,
    )
    risposta = await rag.answer(req, user)
    # Giorno 9: la risposta nel registro. Dal Giorno 10 il costo comprende anche la riscrittura
    CostLedger(session).aggiungi(
        endpoint="advice",
        username=user.username,
        model=settings.default_model,
        tokens=risposta.tokens_used,
        cost_eur=Decimal(str(risposta.cost_eur)),
    )
    await session.commit()
    return risposta


@router.post("/documents/ingest", response_model=IngestResponse)
async def ingest(
    req: IngestRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    embedder: Annotated[EmbeddingClient, Depends(get_embedder)],
) -> IngestResponse:
    service = IngestService(db, embedder)
    chunk_count, embedding_dim = await service.ingest_document(
        req.document_id, req.content, req.metadata, visibility=req.visibility
    )
    return IngestResponse(chunk_count=chunk_count, embedding_dim=embedding_dim)
