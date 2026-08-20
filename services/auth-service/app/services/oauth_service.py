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

    async def login_or_create_user(self,identity:GoogleIdentity):
        oauth_account=await self._oauth_account_repository.find_by_provider_identity(
            provider='google',
            provider_user_id=identity.sub
        )
        if oauth_account:
            user = await self._user_repository.find_by_id(oauth_account.user_id)
            if user is None:
                raise ValueError("OAuth account is  linked to a missing user")
            return user
        user = None
        if identity.email:
            user = await self._user_repository.find_by_email(identity.email)

        if user:
        # Security rule: only auto-link if email is verified by Google
            if not identity.email_verified:
                raise ValueError(
                    "Cannot link Google account to existing user: email is not verified"
                )

            await self._oauth_account_repository.create(
            provider="google",
            provider_user_id=identity.sub,
            user_id=user.id,
            provider_email=identity.email,
            )
        # no commit/rollback orchestration yet per your phase plan
            return user

    # 4) No user exists by email: create new user, then link oauth account
        user = await self._user_repository.create(
            email=identity.email,
            username=identity.name,
        )

        await self._oauth_account_repository.create(
            provider="google",
            provider_user_id=identity.sub,
            user_id=user.id,
            provider_email=identity.email,
        )

    # no commit/rollback orchestration yet per your phase plan
        return user