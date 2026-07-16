import resend

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

        resend.Emails.send(params)