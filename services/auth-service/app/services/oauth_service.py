from __future__ import annotations
from app.schemas.schemas import GoogleIdentity
from app.infrastructure.oauth.google.client import GoogleOAuthClient
from app.repositories.user_repository import UserRepository
from app.repositories.oauth_repository import OAuthAccountRepository
class GoogleOAuthService:
    def __init__(self, 
        google_client:GoogleOAuthClient,
        user_repository: UserRepository,
        oauth_account_repository: OAuthAccountRepository,
                 ) -> None:
        self._google_client = google_client
        self._user_repository = user_repository
        self._oauth_account_repository = oauth_account_repository

    def get_authorization_url(self) -> tuple[str, str]:
        # Service delegates construction details to client
        return self._google_client.get_authorization_url()

    async def exchange_code(self,code:str)->dict:
        return await self._google_client.exchange_code(code)

    def verify_id_token(self, id_token: str) -> GoogleIdentity:
        return self._google_client.verify_id_token(id_token)
