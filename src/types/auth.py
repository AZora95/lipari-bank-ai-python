from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="Bearer token JWT emesso dal login")
    token_type: str = Field(default="bearer", description="Tipo di token rilasciato")
    expires_in: int = Field(1800, ge=1, description="Scadenza del token in secondi")