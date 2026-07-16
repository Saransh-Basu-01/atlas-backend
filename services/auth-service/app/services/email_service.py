import resend
import asyncio
from app.core.config import settings


class EmailService:
    def __init__(self):
        resend.api_key = settings.resend_api_key

    async def send_password_reset_email(
        self,
        email: str,
        token: str,
    ):
        reset_link = (
            f"{settings.frontend_url}"
            f"/reset-password?token={token}"
        )

        params = {
            "from": settings.email_from,
            "to": [email],
            "subject": "Reset your password",
            "html": f"""
                <h2>Password Reset</h2>

                <p>You requested a password reset.</p>

                <p>
                    <a href="{reset_link}">
                        Reset Password
                    </a>
                </p>

                <p>
                    If you didn't request this,
                    ignore this email.
                </p>
            """,
        }

        await asyncio.to_thread(resend.Emails.send, params)

    async def send_password_changed_email(self, email: str) -> None:
        params = {
            "from": settings.email_from,
            "to": [email],
            "subject": "Your password was changed",
            "html": """
                <h2>Password Changed</h2>
                <p>Your account password was changed successfully.</p>
                <p>If this was not you, please secure your account immediately.</p>
            """,
        }

        # keep async endpoint non-blocking while resend call is sync
        await asyncio.to_thread(resend.Emails.send, params)