from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken

class RefreshTokenRepository:
    def __init__(self,session:AsyncSession):
        self.session=session

    async def create(self,refresh_token:RefreshToken)->RefreshToken:
        self.session.add(refresh_token)
        return refresh_token
    
    async def get_by_id(self,token_id:int)->RefreshToken|None:
        return await self.session.get(RefreshToken,token_id)

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def revoke_by_hash(self, token_hash: str) -> bool:
        now = datetime.now(timezone.utc)
        stmt = (
            update(RefreshToken)
            .where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )
        result = await self.session.execute(stmt)
        return result.rowcount or 0

    async def revoke_by_id(self, token_id: int) -> bool:
        now = datetime.now(timezone.utc)
        stmt = (
            update(RefreshToken)
            .where(
                RefreshToken.id == token_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )
        result = await self.session.execute(stmt)
        return result.rowcount or 0

    async def delete_all_for_user(self, user_id: int) -> int:
        stmt = delete(RefreshToken).where(RefreshToken.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.rowcount or 0

    async def delete_expired(self, *, now: datetime | None = None) -> int:
        now = now or datetime.now(timezone.utc)
        stmt = delete(RefreshToken).where(RefreshToken.expires_at <= now)
        result = await self.session.execute(stmt)
        return result.rowcount or 0

    async def list_active_sessions_for_user(
        self,
        user_id: int,
        *,
        now: datetime | None = None,
        limit: int = 100,
    ) -> Sequence[RefreshToken]:
        now = now or datetime.now(timezone.utc)
        stmt = (
            select(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.expires_at > now,
            )
            .order_by(RefreshToken.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def delete_by_hash(self, token_hash: str) -> bool:
        stmt = delete(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await self.session.execute(stmt)
        return (result.rowcount or 0) > 0
