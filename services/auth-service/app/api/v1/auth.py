from fastapi import APIRouter, Depends, HTTPException, status,Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService,UserAlreadyExistsError,InvalidCredentialsError
from app.schemas.schemas import UserCreate, UserResponse,UserLogin,TokenPayload,TokenResponse,RefreshTokenRequest
from app.dependencies.auth import get_current_user
from app.models.models import User
from fastapi.security import OAuth2PasswordRequestForm
from app.repositories.refresh_token_repository import RefreshTokenRepository
router = APIRouter(prefix="/auth", tags=["auth"])


def get_user_service(session: AsyncSession = Depends(get_db)) -> AuthService:
    repo = UserRepository(session)
    refresh_token_repo = RefreshTokenRepository(session)
    return AuthService(
    user_repo=repo,
    refresh_token_repo=refresh_token_repo,
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
    # payload: UserLogin,
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_user_service),
):
    try:
        # token = await service.login(payload) 
        # return token
        payload = UserLogin(email=form_data.username, password=form_data.password)
        return await service.login(payload)
    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    
@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def read_me(
    current_user: User = Depends(get_current_user),
):
    return current_user

@router.post("/refresh",
             response_model=TokenResponse,
             status_code=status.HTTP_200_OK)
async def refresh_tokens(
    payload:RefreshTokenRequest,
    request:Request,
    service:AuthService=Depends(get_user_service)
)->TokenResponse:
    ip_address = request.client.host if request.client else None
    device_name = request.headers.get("user-agent")
    try:
        tokens = await service.refresh(
            refresh_token=payload.refresh_token,
            ip_address=ip_address,
            device_name=device_name
        )
        return tokens
    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    