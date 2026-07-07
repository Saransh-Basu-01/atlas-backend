from typing import Optional
from passlib.context import CryptContext

from app.models.models import User
from app.repositories.user_repository import UserRepository


class UserAlreadyExistsError(Exception):
    pass


class UserNotFoundError(Exception):
    pass


class UserService:
    """Business layer: rules + validations + transformations."""

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    async def create_user(self, name: str, email: str, password: str) -> User:
        # 1) Business rule: duplicate email not allowed
        existing = await self.user_repo.find_by_email(email)
        if existing:
            raise UserAlreadyExistsError("Email already registered")

        # 2) Business rule: hash password before storing
        hashed_password = self.pwd_context.hash(password)

        # 3) Business rule: default active user (example)
        return await self.user_repo.create(
            name=name.strip(),
            email=email.lower().strip(),
            hashed_password=hashed_password,
            is_active=True,
        )

    async def get_user_profile(self, user_id: int) -> User:
        user = await self.user_repo.find_by_id(user_id)
        if not user:
            raise UserNotFoundError("User not found")
        return user

    async def change_password(self, user_id: int, new_password: str) -> None:
        user = await self.user_repo.find_by_id(user_id)
        if not user:
            raise UserNotFoundError("User not found")

        # Example password rule
        if len(new_password) < 8:
            raise ValueError("Password must be at least 8 characters long")

        hashed_password = self.pwd_context.hash(new_password)
        await self.user_repo.update_password(user_id=user_id, hashed_password=hashed_password)