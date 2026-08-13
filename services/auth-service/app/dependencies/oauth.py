from __future__ import annotations

from app.core.config import settings
from app.infrastructure.oauth.google.client import GoogleOAuthClient
from app.services.oauth_service import GoogleOAuthService


def get_google_oauth_service() -> GoogleOAuthService:
    google_client = GoogleOAuthClient(
        client_id=settings.GOOGLE_CLIENT_ID,
        redirect_uri=settings.GOOGLE_REDIRECT_URI,
    )
    return GoogleOAuthService(google_client)