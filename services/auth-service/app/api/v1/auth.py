from fastapi import APIRouter, Depends, HTTPException, status,Request,Response,Cookie
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService,UserAlreadyExistsError,InvalidCredentialsError
from app.schemas.schemas import UserCreate, UserResponse,UserLogin,TokenPayload,TokenResponse,RefreshTokenRequest,ResetPasswordRequest,ResetPasswordResponse,ForgotPasswordRequest,ForgotPasswordResponse
from app.dependencies.auth import get_current_user
from app.models.models import User
from fastapi.security import OAuth2PasswordRequestForm
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.core.config import settings
from app.repositories.password_reset_token_repository import PasswordResetTokenRepository
from app.services.email_service import EmailService
from app.services.password_reset_service import PasswordResetService,InvalidOrExpiredResetTokenError

router = APIRouter(prefix="/auth", tags=["auth"])


def get_user_service(session: AsyncSession = Depends(get_db)) -> AuthService:
    repo = UserRepository(session)
    refresh_token_repo = RefreshTokenRepository(session)
    return AuthService(
    user_repo=repo,
    refresh_token_repo=refresh_token_repo,
    session=session,
) 

def get_password_service(session: AsyncSession = Depends(get_db)) -> PasswordResetService:
    repo = UserRepository(session)
    reset_token_repo = PasswordResetTokenRepository(session)
    email_service=EmailService()
    return PasswordResetService(
    user_repo=repo,
    reset_token_repo=reset_token_repo,
    email_service=email_service,
    session=session,
) 

def get_email_service():
    return EmailService()

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
    response:Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_user_service)
):
    try:
        # token = await service.login(payload) 
        # return token
        payload = UserLogin(email=form_data.username, password=form_data.password)
        tokens = await service.login(payload) 
        response.set_cookie(
            key="refresh_token",
            value=tokens.refresh_token,
            httponly=True,
            secure=settings.COOKIE_SECURE,          # set False only in local HTTP dev
            samesite="lax",
            max_age=settings.REFRESH_COOKIE_MAX_AGE_SECONDS,
            path="/",
        )
        return TokenResponse(
            access_token=tokens.access_token
        )
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
    response:Response,
    request:Request,
    refresh_token: str | None = Cookie(default=None, alias="refresh_token"),
    service:AuthService=Depends(get_user_service)
)->TokenResponse:
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing refresh token",
        )
    ip_address = request.client.host if request.client else None
    device_name = request.headers.get("user-agent")
    try:
        tokens = await service.refresh(
            refresh_token=refresh_token,
            ip_address=ip_address,
            device_name=device_name
        )
        response.set_cookie(
            key="refresh_token",
            value=tokens.refresh_token,
            httponly=True,
            secure=settings.COOKIE_SECURE,
            samesite=settings.COOKIE_SAMESITE,
            max_age=settings.REFRESH_COOKIE_MAX_AGE_SECONDS,
            path="/",
        )
        return TokenResponse(
            access_token=tokens.access_token,
        )
    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    

@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
)
async def logout_user(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias="refresh_token"),
    service: AuthService = Depends(get_user_service),
):
    # Optional: if token exists, revoke it in DB (recommended)
    if refresh_token:
        try:
            await service.revoke_refresh_token(refresh_token)  # create this method if not present
        except Exception:
            pass  # don't fail logout for this

    response.delete_cookie(
        key="refresh_token",
        path="/",
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
    )
    return {"message": "logged out successfully"}


@router.post(
    "/logout-all",
    status_code=status.HTTP_200_OK,
)
async def logout_all_devices(
    response: Response,
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_user_service),
):
    try:
        deleted_count = await service.revoke_all_refresh_tokens(current_user.id)

        response.delete_cookie(
            key="refresh_token",
            path="/",
        )

        return {
            "message": "logged out from all devices",
            "revoked_tokens": deleted_count,
        }
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="failed to logout from all devices",
        )
    
from fastapi import APIRouter, Depends, HTTPException, status,Request,Response,Cookie
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService,UserAlreadyExistsError,InvalidCredentialsError
from app.schemas.schemas import UserCreate, UserResponse,UserLogin,TokenPayload,TokenResponse,RefreshTokenRequest,ResetPasswordRequest,ResetPasswordResponse,ForgotPasswordRequest,ForgotPasswordResponse
from app.dependencies.auth import get_current_user
from app.models.models import User
from fastapi.security import OAuth2PasswordRequestForm
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.core.config import settings
from app.repositories.password_reset_token_repository import PasswordResetTokenRepository
from app.services.email_service import EmailService
from app.services.password_reset_service import PasswordResetService,InvalidOrExpiredResetTokenError

router = APIRouter(prefix="/auth", tags=["auth"])


def get_user_service(session: AsyncSession = Depends(get_db)) -> AuthService:
    repo = UserRepository(session)
    refresh_token_repo = RefreshTokenRepository(session)
    return AuthService(
    user_repo=repo,
    refresh_token_repo=refresh_token_repo,
    session=session,
) 

def get_password_service(session: AsyncSession = Depends(get_db)) -> PasswordResetService:
    repo = UserRepository(session)
    reset_token_repo = PasswordResetTokenRepository(session)
    email_service=EmailService()
    return PasswordResetService(
    user_repo=repo,
    reset_token_repo=reset_token_repo,
    email_service=email_service,
    session=session,
) 

def get_email_service():
    return EmailService()

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
    response:Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_user_service)
):
    try:
        # token = await service.login(payload) 
        # return token
        payload = UserLogin(email=form_data.username, password=form_data.password)
        tokens = await service.login(payload) 
        response.set_cookie(
            key="refresh_token",
            value=tokens.refresh_token,
            httponly=True,
            secure=settings.COOKIE_SECURE,          # set False only in local HTTP dev
            samesite="lax",
            max_age=settings.REFRESH_COOKIE_MAX_AGE_SECONDS,
            path="/",
        )
        return TokenResponse(
            access_token=tokens.access_token
        )
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
    response:Response,
    request:Request,
    refresh_token: str | None = Cookie(default=None, alias="refresh_token"),
    service:AuthService=Depends(get_user_service)
)->TokenResponse:
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing refresh token",
        )
    ip_address = request.client.host if request.client else None
    device_name = request.headers.get("user-agent")
    try:
        tokens = await service.refresh(
            refresh_token=refresh_token,
            ip_address=ip_address,
            device_name=device_name
        )
        response.set_cookie(
            key="refresh_token",
            value=tokens.refresh_token,
            httponly=True,
            secure=settings.COOKIE_SECURE,
            samesite=settings.COOKIE_SAMESITE,
            max_age=settings.REFRESH_COOKIE_MAX_AGE_SECONDS,
            path="/",
        )
        return TokenResponse(
            access_token=tokens.access_token,
        )
    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    

@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
)
async def logout_user(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias="refresh_token"),
    service: AuthService = Depends(get_user_service),
):
    # Optional: if token exists, revoke it in DB (recommended)
    if refresh_token:
        try:
            await service.revoke_refresh_token(refresh_token)  # create this method if not present
        except Exception:
            pass  # don't fail logout for this

    response.delete_cookie(
        key="refresh_token",
        path="/",
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
    )
    return {"message": "logged out successfully"}


@router.post(
    "/logout-all",
    status_code=status.HTTP_200_OK,
)
async def logout_all_devices(
    response: Response,
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_user_service),
):
    try:
        deleted_count = await service.revoke_all_refresh_tokens(current_user.id)

        response.delete_cookie(
            key="refresh_token",
            path="/",
        )

        return {
            "message": "logged out from all devices",
            "revoked_tokens": deleted_count,
        }
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="failed to logout from all devices",
        )
    
@router.post("/forgot-password", response_model=ForgotPasswordResponse, status_code=status.HTTP_200_OK)
async def forgot_password(
    payload: ForgotPasswordRequest,
    service: PasswordResetService = Depends(get_password_service),
):
    await service.forgot_password(payload.email)
    return ForgotPasswordResponse(
        message="If an account with that email exists, a reset link has been sent."
    )


@router.post(
    "/reset-password",
    response_model=ResetPasswordResponse,
    status_code=status.HTTP_200_OK,
)
async def reset_password(
    payload: ResetPasswordRequest,
    service: PasswordResetService = Depends(get_password_service),
):
    try:
        new_password_ = payload.new_password
        await service.reset_password(payload.token, new_password_)
    except InvalidOrExpiredResetTokenError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    return ResetPasswordResponse(message="Password has been reset successfully.")

# @router.post(
#     "/reset-password",
#     response_model=ResetPasswordResponse,
#     status_code=status.HTTP_200_OK,
# )
# async def reset_password(
#     payload: ResetPasswordRequest,
#     service: PasswordResetService = Depends(get_password_service),
# ):
#     try:
#         new_password_ = payload.new_password
#         await service.reset_password(payload.token, new_password_)
#     except InvalidOrExpiredResetTokenError:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Invalid or expired reset token",
#         )

#     return ResetPasswordResponse(message="Password has been reset successfully.")