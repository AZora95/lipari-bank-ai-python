from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.services.chat_service import ChatService
from src.types.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/api/ai", tags=["Chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, session: AsyncSession = Depends(get_db)) -> ChatResponse:
    service = ChatService(session)
    # user_id hardcoded: l'autenticazione è fuori scope in questo percorso 8gg.
    return await service.chat(req, user_id="dummy-user")


@router.get("/chat/{session_id}/messages")
async def list_messages(session_id: str, session: AsyncSession = Depends(get_db)) -> list[dict]:
    service = ChatService(session)
    messages = await service.repo.list_messages(session_id)
    return [
        {"role": m.role, "content": m.content, "created_at": m.created_at.isoformat()}
        for m in messages
    ]
