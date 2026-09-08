import httpx
from fastapi import APIRouter

from src.types.user import User

router = APIRouter(prefix="/api/ai", tags=["Users"])

# Directory interna LipariBank (mock in dev)
USER_DIRECTORY_URL = "http://localhost:9000/internal/users"


@router.get("/users")
async def list_users() -> list[User]:
    async with httpx.AsyncClient() as client:
        """Elenco utenti dalla directory interna LipariBank."""
        response = await client.get(USER_DIRECTORY_URL, timeout=5.0)
    return [User.model_validate(item) for item in response.json()]
