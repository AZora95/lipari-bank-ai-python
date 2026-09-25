from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.passwords import verify_password
from src.auth.tokens import ACCESS_TOKEN_TTL, create_access_token
from src.db.models import AppUser
from src.exceptions import InvalidCredentialsError
from src.types.auth import TokenResponse


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def login(self, username: str, password: str) -> TokenResponse:
        """Verifica le credenziali ed emette un access token a scadenza.

        Credenziali sbagliate: 401, e il messaggio NON dice quale delle due era sbagliata.
        """
        user = await self.session.scalar(select(AppUser).where(AppUser.username == username))
        if user is None or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError()

        token = create_access_token(subject=user.username, role=user.role)
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=int(ACCESS_TOKEN_TTL.total_seconds()),
        )