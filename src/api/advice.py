from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.llm.embedding_client import EmbeddingClient
from src.llm.factory import get_llm_provider
from src.services.ingest_service import IngestService
from src.services.rag_service import RAGService
from src.services.retrieval_service import RetrievalService
from src.types.advice import AdviceRequest, AdviceResponse, IngestRequest, IngestResponse

router = APIRouter(prefix="/api/ai", tags=["Advice"])


@router.post("/advice", response_model=AdviceResponse)
async def advice(req: AdviceRequest, db: AsyncSession = Depends(get_db)) -> AdviceResponse:
    embedding_client = EmbeddingClient()
    retrieval = RetrievalService(db, embedding_client)
    rag = RAGService(retrieval, get_llm_provider())
    return await rag.answer(req)


@router.post("/documents/ingest", response_model=IngestResponse)
async def ingest(req: IngestRequest, db: AsyncSession = Depends(get_db)) -> IngestResponse:
    embedding_client = EmbeddingClient()
    service = IngestService(db, embedding_client)
    chunk_count, embedding_dim = await service.ingest_document(
        req.document_id, req.content, req.metadata
    )
    return IngestResponse(chunk_count=chunk_count, embedding_dim=embedding_dim)
