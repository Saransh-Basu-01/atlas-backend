from __future__ import annotations

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.oauth_accounts import OAuthAccount


class OAuthAccountRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_provider_identity(
        self,
        provider: str,
        provider_user_id: str,
    ) -> Optional[OAuthAccount]:
        stmt = select(OAuthAccount).where(
            OAuthAccount.provider == provider,
            OAuthAccount.provider_user_id == provider_user_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_user_and_provider(
        self,
        user_id: int,
        provider: str,
    ) -> Optional[OAuthAccount]:
        stmt = select(OAuthAccount).where(
            OAuthAccount.user_id == user_id,
            OAuthAccount.provider == provider,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, oauth_account: OAuthAccount) -> OAuthAccount:
        self.session.add(oauth_account)
        return oauth_account

    async def delete(self, oauth_account: OAuthAccount) -> None:
        await self.session.delete(oauth_account)