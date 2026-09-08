from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.repos import ChatRepository
from src.exceptions import ChatSessionNotFoundError
from src.types.chat import ChatRequest, ChatResponse


class ChatService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ChatRepository(session)

    async def chat(self, req: ChatRequest, user_id: str) -> ChatResponse:
        if req.session_id and req.session_id != "new":
            chat = await self.repo.find_session(req.session_id)
            if not chat:
                raise ChatSessionNotFoundError(req.session_id)
        else:
            chat = await self.repo.create_session(user_id=user_id)

        turn = len(chat.messages) + 1

        await self.repo.add_message(chat.id, "user", req.message)

        assistant_reply = f"Echo (messaggio #{turn}): {req.message}"
        await self.repo.add_message(
            chat.id,
            "assistant",
            assistant_reply,
            tokens=10,
            cost_eur=0.0001,
            model_used="dummy",
        )

        return ChatResponse(
            session_id=chat.id,
            reply=assistant_reply,
            tokens_used=10,
            cost_eur=0.0001,
            model_used="dummy",
            created_at=datetime.now(UTC),
        )
