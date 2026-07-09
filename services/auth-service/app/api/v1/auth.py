from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService,UserAlreadyExistsError,InvalidCredentialsError
from app.schemas.schemas import UserCreate, UserResponse,UserLogin,TokenPayload,TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


def get_user_service(session: AsyncSession = Depends(get_db)) -> AuthService:
    repo = UserRepository(session)
    return AuthService(
    user_repo=repo,
    session=session,
) 


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    payload: UserCreate,
    service: AuthService = Depends(get_user_service),
):
    try:
        # service.register expects a UserCreate object (as in your code)
        user = await service.register(payload)
        return user
    except UserAlreadyExistsError as e:
        raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=str(e),
        )
    

@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
async def login_user(
    payload: UserLogin,
    service: AuthService = Depends(get_user_service),
):
    try:
        token = await service.login(payload)
        return token
    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )