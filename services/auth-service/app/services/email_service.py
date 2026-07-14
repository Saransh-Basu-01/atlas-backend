# services/email_service.py

import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Placeholder email service.

    Currently logs to console instead of sending real emails.
    Swap the internals later when integrating an actual provider
    (Resend, SendGrid, AWS SES, etc.).
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")

    async def send_password_reset_email(
        self,
        email: str,
        token: str,
    ) -> None:
        reset_url = f"{self.base_url}/reset-password?token={token}"

        # TODO: replace with real email dispatch later
        logger.info("──── Password Reset Email ────")
        logger.info("To:      %s", email)
        logger.info("Subject: Reset your password")
        logger.info("Link:    %s", reset_url)
        logger.info("──────────────────────────────")

        print(
            f"\n📧 PASSWORD RESET\n"
            f"   To:      {email}\n"
            f"   Subject: Reset your password\n"
            f"   Link:    {reset_url}\n"
        )