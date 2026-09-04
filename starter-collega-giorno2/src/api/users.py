import httpx
from fastapi import APIRouter

router = APIRouter(prefix="/api/ai", tags=["Users"])

# Directory interna LipariBank (mock in dev)
USER_DIRECTORY_URL = "http://localhost:9000/internal/users"


@router.get("/users")
def list_users() -> list[dict]:
    """Elenco utenti dalla directory interna LipariBank."""
    response = httpx.get(USER_DIRECTORY_URL, timeout=5.0)
    return response.json()
