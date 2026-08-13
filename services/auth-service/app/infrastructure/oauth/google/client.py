from __future__ import annotations

import secrets
from urllib.parse import urlencode


class GoogleOAuthClient:
    AUTH_BASE_URL = "https://accounts.google.com/o/oauth2/v2/auth"

    def __init__(self, client_id: str, redirect_uri: str) -> None:
        self._client_id = client_id
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