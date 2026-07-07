from typing import Optional, List
from sqlalchemy import select,Delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import User

class UserRepository:
    """Repository layer: only talks to DB, no business rules."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_username(self,username:str)->Optional[User]:
        result=await self.session.execute(select(User).where(User.username==username))
        return result.scalar_one_or_none()

    async def find_by_id(self, user_id: int) -> Optional[User]:
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_users(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> List[User]:
        stmt = select(User)
        stmt = stmt.order_by(User.username.asc()).limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def find_by_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create(self, user:User) -> User:
        self.session.add(user)
        return user

    async def update_password(self, user_id: int, password_hash: str) -> None:
        user = await self.find_by_id(user_id)
        if not user:
            return
        user.password_hash = password_hash

    async def delete(self, user: User) -> None:
        await self.session.delete(user)
       
    
