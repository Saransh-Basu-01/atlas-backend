from __future__ import annotations
from datetime import datetime,timezone
from typing import Sequence

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.password_reset_token import PasswordResetToken

class PasswordResetTokenRepository:
    def __init__(self,session:AsyncSession):
        self.session=session

    async def create(self,password_reset_token:PasswordResetToken)->PasswordResetToken:
        self.session.add(password_reset_token)
        return password_reset_token
    
    async def get_by_id(self,token_id:int)->PasswordResetToken|None:
        return await self.session.get(PasswordResetToken,token_id)

    async def get_by_hash(self, token_hash: str) -> PasswordResetToken | None:
        stmt = select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_expired(self, *, now: datetime | None = None) -> int:
        now = now or datetime.now(timezone.utc)
        stmt = delete(PasswordResetToken).where(PasswordResetToken.expires_at <= now)
        result = await self.session.execute(stmt)
        return result.rowcount or 0

    async def delete_all_for_user(self, user_id: int) -> int:
        stmt = delete(PasswordResetToken).where(PasswordResetToken.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.rowcount or 0
    
    async def mark_used(self, token_id: int) -> bool:
        stmt = (
        update(PasswordResetToken)
        .where(
        PasswordResetToken.id == token_id,
        PasswordResetToken.is_used.is_(False),
        )
        .values(is_used=True)
        )
        result = await self.session.execute(stmt)
        return (result.rowcount or 0) > 0