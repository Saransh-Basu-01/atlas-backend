from sqlalchemy.exc import IntegrityError
from app.models.models import User
from app.repositories.user_repository import UserRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.schemas.schemas import UserCreate,UserResponse,UserLogin,TokenPayload,TokenResponse
from app.security.password import hash_password
from sqlalchemy.ext.asyncio import AsyncSession
from app.security.password import verify_password
from app.security.jwt import create_access_token
from app.security.refresh_token import generate_refresh_token,hash_refresh_token
from app.models.refresh_token import RefreshToken
from datetime import datetime, timedelta, timezone
from app.core.config import settings

class UserAlreadyExistsError(Exception):
    pass
class InvalidCredentialsError(Exception):
    pass
class AuthService:
    """Business layer: rules + validations + transformations."""

    def __init__(self, user_repo: UserRepository,refresh_token_repo:RefreshTokenRepository,session:AsyncSession):
        self.user_repo = user_repo
        self.refresh_token_repo=refresh_token_repo
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

        raw_refresh_token = generate_refresh_token()
        refresh_token_hash = hash_refresh_token(raw_refresh_token)

        refresh_expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        refresh_token_obj = RefreshToken(
        user_id=user.id,
        token_hash=refresh_token_hash,
        expires_at=refresh_expires_at,
        )

        await self.refresh_token_repo.create(refresh_token_obj)
        await self.session.commit()

        return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh_token,
        )

    async def refresh(
        self,
        *,
        refresh_token: str,
        ip_address: str | None = None,
        device_name: str | None = None,
    ) -> TokenResponse:
        now = datetime.now(timezone.utc)
        token_hash = hash_refresh_token(refresh_token)

        # 1) find by hash
        token_row = await self.refresh_token_repo.get_by_hash(token_hash)
        if not token_row:
            raise InvalidCredentialsError("invalid refresh token")

        # 2) revoked?
        if token_row.revoked_at is not None:
            raise InvalidCredentialsError("refresh token revoked")

        # 3) expired?
        if token_row.expires_at <= now:
            raise InvalidCredentialsError("refresh token expired")

        # 4) user exists?
        user = await self.user_repo.find_by_id(token_row.user_id)
        if not user:
            raise InvalidCredentialsError("invalid refresh token")

        # 5) new access token
        access_token = create_access_token(data={"sub": str(user.id)})

        # 6) rotate refresh token (recommended)
        new_raw_refresh = generate_refresh_token()
        new_hash_refresh = hash_refresh_token(new_raw_refresh)
        new_expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        # revoke old token
        await self.refresh_token_repo.revoke_by_id(token_row.id)

        # create new token row
        new_row = RefreshToken(
            user_id=user.id,
            token_hash=new_hash_refresh,
            expires_at=new_expires_at,
            device_name=device_name,
            ip_address=ip_address,
        )
        await self.refresh_token_repo.create(new_row)

        # single commit
        await self.session.commit()

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_raw_refresh,
        )
        
