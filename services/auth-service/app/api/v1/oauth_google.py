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
        id_token = token_response.get("id_token")
       
        if not id_token:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Google token response missing id_token",
            )

        identity = oauth_service.verify_id_token(id_token)
        user, tokens = await oauth_service.login_or_create_user(identity)

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="Google OAuth processing failed",
    ) from exc
   
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
        "message": "Google login successful",
        "user_id": user.id,
        "email": user.email,
        "username": user.username,
        "access_token": tokens.access_token,
        "refresh_token": tokens.refresh_token,
        },
    )

# @router.get("/callback")
# async def google_callback(
#     request: Request,
#     code: str | None = Query(default=None),
#     state: str | None = Query(default=None),
#     error: str | None = Query(default=None),
#     error_description: str | None = Query(default=None),
#     oauth_service:GoogleOAuthService=Depends(get_google_oauth_service)
# ) -> JSONResponse:
#     print(f"🔍 Callback received - code: {code[:20]}..., state: {state[:20]}...")
    
#     if error:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=f"Google OAuth error: {error} ({error_description or 'no description'})",
#         )

#     if not code:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Missing authorization code",
#         )
#     if not state:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Missing state",
#         )

#     expected_state = request.session.get("google_oauth_state")
#     print(f"✅ Session state: {expected_state[:20] if expected_state else 'NONE'}...")
#     print(f"✅ Returned state: {state[:20]}...")
    
#     if not expected_state or state != expected_state:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Invalid OAuth state",
#         )

#     request.session.pop("google_oauth_state", None)

#     try:
#         print("🔄 Exchanging code for token...")
#         token_response = await oauth_service.exchange_code(code)
#         print(f"✅ Token response: {token_response.keys()}")
        
#         id_token = token_response.get("id_token")
        
#         if not id_token:
#             raise HTTPException(
#                 status_code=status.HTTP_502_BAD_GATEWAY,
#                 detail="Google token response missing id_token",
#             )

#         print("🔐 Verifying ID token...")
#         identity = oauth_service.verify_id_token(id_token)
#         print(f"✅ Identity: {identity.email}") 
        
#         print("👤 Creating/finding user...")
#         user = await oauth_service.login_or_create_user(identity)
#         print(f"✅ User created: {user.id}")

#     except HTTPException:
#         raise
#     except Exception as exc:
#         print(f"❌ Error: {exc}")
#         import traceback
#         traceback.print_exc()
#         raise HTTPException(
#             status_code=status.HTTP_502_BAD_GATEWAY,
#             detail="Google OAuth processing failed",
#         ) from exc
   
#     return JSONResponse(
#         status_code=status.HTTP_200_OK,
#         content={
#             "message": "Google login successful",
#             "user_id": user.id,
#             "email": user.email,
#             "username": user.username,
#         },
#     )