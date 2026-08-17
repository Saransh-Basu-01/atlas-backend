from __future__ import annotations

import secrets
from urllib.parse import urlencode
import httpx
TOKEN_URL = "https://oauth2.googleapis.com/token"

class GoogleOAuthClient:
    AUTH_BASE_URL = "https://accounts.google.com/o/oauth2/v2/auth"

    def __init__(self, client_id: str,client_secret: str, redirect_uri: str) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri

    def get_authorization_url(self) -> tuple[str, str]:
        """
        Returns:
            (authorization_url, state)
        """
        state = secrets.token_urlsafe(32)

        params = {
            "client_id": self._client_id,
            "redirect_uri": self._redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            # optional but recommended:
            "access_type": "offline",
            "prompt": "consent",
        }

        authorization_url = f"{self.AUTH_BASE_URL}?{urlencode(params)}"
        return authorization_url, state

    async def exchange_code(self, code: str) -> dict:
        payload = {
            "code": code,
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "redirect_uri": self._redirect_uri,
            "grant_type": "authorization_code",
        }

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                self.TOKEN_URL,
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

        if response.status_code != 200:
            # include Google response body for easier debugging
            raise RuntimeError(f"Google token exchange failed: {response.text}")

        return response.json()


    async def verify_id_token(id_token):
        