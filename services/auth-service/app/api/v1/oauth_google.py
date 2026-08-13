from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse

from app.dependencies.oauth import get_google_oauth_service
from app.services.oauth_service import GoogleOAuthService

router = APIRouter(prefix="/auth/google", tags=["auth"])


@router.get("/login")
def google_login(
    oauth_service: GoogleOAuthService = Depends(get_google_oauth_service),
) -> RedirectResponse:
    authorization_url, _state = oauth_service.get_authorization_url()
    # state will be persisted later when callback is implemented
    return RedirectResponse(url=authorization_url, status_code=302)