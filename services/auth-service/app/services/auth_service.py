from sqlalchemy.exc import IntegrityError
from app.models.models import User
from app.repositories.user_repository import UserRepository
from app.schemas.schemas import UserCreate,UserResponse,UserLogin,TokenPayload,TokenResponse
from app.security.password import hash_password
from sqlalchemy.ext.asyncio import AsyncSession
from app.security.password import verify_password
from app.security.jwt import create_access_token
class UserAlreadyExistsError(Exception):
    pass
class InvalidCredentialsError(Exception):
    pass
class AuthService:
    """Business layer: rules + validations + transformations."""

    def __init__(self, user_repo: UserRepository,session:AsyncSession):
        self.user_repo = user_repo
        self.session=session

    async def register(self, data: UserCreate) -> UserResponse:
        # 1) Check username exists
        username = data.username.strip()
        email = data.email.lower().strip()
        existing_username = await self.user_repo.find_by_username(username)
        if existing_username:
            raise UserAlreadyExistsError("Username already registered")

        # 2) Check email exists
        existing_email = await self.user_repo.find_by_email(email)
        if existing_email:
            raise UserAlreadyExistsError("Email already registered")

        # 3) Hash password
        password_hash = hash_password(data.password)

        # 4) Repository.create(user) -> commit + refresh inside repository
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
        )

        await self.user_repo.create(user)

        try:
            await self.session.commit()
            await self.session.refresh(user)
        except IntegrityError:
            await self.session.rollback()
            raise UserAlreadyExistsError("Username or email already exists")

        return UserResponse.model_validate(user)


    async def login(self,data:UserLogin)->TokenResponse:
        email = data.email.lower().strip()
        password=data.password
        user = await self.user_repo.find_by_email(email)
        if not user:
            raise InvalidCredentialsError("invalid credentials")
        is_valid=verify_password(password,user.password_hash)
        if not is_valid:
            raise InvalidCredentialsError("invalid credentials")
        access_token = create_access_token(data={"sub": str(user.id)})
        return TokenResponse(access_token=access_token)
        
