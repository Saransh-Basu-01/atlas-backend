from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.user_repository import UserRepository
from app.services.auth_service import UserService
from app.schemas.schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
    TokenResponse,
)

router = APIRouter(prefix="/users", tags=["Users v1"])


def get_user_service(session: AsyncSession = Depends(get_db)) -> UserService:
    repo = UserRepository(session)
    return UserService(repo)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    payload: UserCreate,
    service: UserService = Depends(get_user_service),
):
    try:
        user = await service.register_user(
            username=payload.username,
            email=payload.email,
            password=payload.password,
        )
        return user
    except ValueError as e:
        # e.g. duplicate email / duplicate username
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
async def login_user(
    payload: UserLogin,
    service: UserService = Depends(get_user_service),
):
    try:
        tokens = await service.login_user(
            email=payload.email,
            password=payload.password,
        )
        return tokens
    except ValueError as e:
        # invalid credentials
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
async def get_user_by_id(
    user_id: int,
    service: UserService = Depends(get_user_service),
):
    user = await service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
async def update_user(
    user_id: int,
    payload: UserUpdate,
    service: UserService = Depends(get_user_service),
):
    try:
        updated_user = await service.update_user(
            user_id=user_id,
            username=payload.username,
            email=payload.email,
        )
        if not updated_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return updated_user
    except ValueError as e:
        # e.g. duplicate email/username
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))