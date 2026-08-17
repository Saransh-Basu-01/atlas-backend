from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse, JSONResponse

from app.dependencies.oauth import get_google_oauth_service
from app.services.oauth_service import GoogleOAuthService

router = APIRouter(prefix="/auth/google", tags=["auth"])


@router.get("/login")
def google_login(
    request: Request,
    oauth_service: GoogleOAuthService = Depends(get_google_oauth_service),
) -> RedirectResponse:
    authorization_url, state = oauth_service.get_authorization_url()

    # TEMP: store state in session (requires SessionMiddleware in main.py)
    request.session["google_oauth_state"] = state

    return RedirectResponse(url=authorization_url, status_code=status.HTTP_302_FOUND)


@router.get("/callback")
async def google_callback(
    request: Request,
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    error_description: str | None = Query(default=None),
    oauth_service:GoogleOAuthService=Depends(get_google_oauth_service)
) -> JSONResponse:
    # 1) Google returned an OAuth error
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Google OAuth error: {error} ({error_description or 'no description'})",
        )

    # 2) Validate required params
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing authorization code",
        )
    if not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing state",
        )

    # 3) CSRF protection: compare returned state with session state
    expected_state = request.session.get("google_oauth_state")
    if not expected_state or state != expected_state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OAuth state",
        )

    # one-time use state
    request.session.pop("google_oauth_state", None)

    try:
        token_response=await oauth_service.exchange_code(code)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to exchange authorization code with Google",
        ) from exc
   
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": "Google token exchange successful",
            "has_id_token": "id_token" in token_response,
            "has_access_token": "access_token" in token_response,
        },
    )