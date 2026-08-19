from __future__ import annotations
from app.models.oauth_accounts import OAuthAccount
from app.schemas.schemas import GoogleIdentity,GoogleLoginRequest,OAuthAccountCreate
from app.infrastructure.oauth.google.client import GoogleOAuthClient

class GoogleOAuthService:
    def __init__(self, google_client: GoogleOAuthClient) -> None:
        self._google_client = google_client

    def get_authorization_url(self) -> tuple[str, str]:
        # Service delegates construction details to client
        return self._google_client.get_authorization_url()

    async def exchange_code(self,code:str)->dict:
        return await self._google_client.exchange_code(code)

    def verify_id_token(self, id_token: str) -> GoogleIdentity:
        return self._google_client.verify_id_token(id_token)
