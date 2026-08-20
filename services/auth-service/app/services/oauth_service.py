from __future__ import annotations

from app.models.models import User
from app.models.oauth_accounts import OAuthAccount
from app.schemas.schemas import GoogleIdentity
from app.infrastructure.oauth.google.client import GoogleOAuthClient
from app.repositories.user_repository import UserRepository
from app.repositories.oauth_repository import OAuthAccountRepository


class GoogleOAuthService:
    def __init__(
        self,
        google_client: GoogleOAuthClient,
        user_repository: UserRepository,
        oauth_account_repository: OAuthAccountRepository,
    ) -> None:
        self._google_client = google_client
        self._user_repository = user_repository
        self._oauth_account_repository = oauth_account_repository

    def get_authorization_url(self) -> tuple[str, str]:
        return self._google_client.get_authorization_url()

    async def exchange_code(self, code: str) -> dict:
        return await self._google_client.exchange_code(code)

    def verify_id_token(self, id_token: str) -> GoogleIdentity:
        return self._google_client.verify_id_token(id_token)

    async def login_or_create_user(
        self,
        identity: GoogleIdentity,
    ) -> User:

        # 1. Check whether this Google account already exists
        oauth_account = (
            await self._oauth_account_repository.find_by_provider_identity(
                provider="google",
                provider_user_id=identity.sub,
            )
        )

        # 2. Existing Google account
        if oauth_account:
            user = await self._user_repository.find_by_id(
                oauth_account.user_id
            )

            if user is None:
                raise ValueError(
                    "OAuth account is linked to a missing user"
                )

            return user

        # 3. Check whether a normal user already exists
        user = await self._user_repository.find_by_email(
            identity.email
        )

        # 4. Existing user → link Google account
        if user:
            if not identity.email_verified:
                raise ValueError(
                    "Cannot link Google account: email is not verified"
                )

            oauth_account = OAuthAccount(
                user_id=user.id,
                provider="google",
                provider_user_id=identity.sub,
                provider_email=identity.email,
            )

            await self._oauth_account_repository.create(
                oauth_account
            )

            return user

        # 5. No user exists → create a new user
        user = User(
            username=f"google_{identity.sub}",
            email=identity.email,
            password_hash=None,
        )

        await self._user_repository.create(user)
        await self._user_repository.flush()
        # 6. Create OAuth account linked to the new user
        oauth_account = OAuthAccount(
            user_id=user.id,
            provider="google",
            provider_user_id=identity.sub,
            provider_email=identity.email,
        )

        await self._oauth_account_repository.create(
            oauth_account
        )
        await self._user_repository.commit()

        return user