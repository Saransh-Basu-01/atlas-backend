from __future__ import annotations
from fastapi import Depends
from app.core.config import settings
from app.infrastructure.oauth.google.client import GoogleOAuthClient
from app.services.oauth_service import GoogleOAuthService
from app.core.config import settings
from app.repositories.user_repository import UserRepository
from repositories.oauth_repository import OAuthAccountRepository
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

def get_google_oauth_service(
         session: AsyncSession = Depends(get_db),
) -> GoogleOAuthService:
    google_client = GoogleOAuthClient(
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        redirect_uri=settings.GOOGLE_REDIRECT_URI,
    )
    return GoogleOAuthService(google_client)