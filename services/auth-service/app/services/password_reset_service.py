from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.password_reset_token import PasswordResetToken
from app.repositories.password_reset_token_repository import PasswordResetTokenRepository
from app.repositories.user_repository import UserRepository
from app.security.reset_token import generate_reset_token, hash_reset_token
from app.security.password import hash_password
from app.services.email_service import EmailService
from app.jobs.email_jobs import PasswordResetEmailJob,PasswordChangedEmailJob
from app.infrastructure.queue.base import QueueClient

class InvalidOrExpiredResetTokenError(Exception):
    pass


class PasswordResetService:
    """
    Only password recovery use-cases:
      - forgot_password()
      - reset_password()
    """

    def __init__(
        self,
        user_repo: UserRepository,
        reset_token_repo: PasswordResetTokenRepository,
        queue_client: QueueClient,
        session: AsyncSession,
    ):
        self.user_repo = user_repo
        self.reset_token_repo = reset_token_repo
        self.queue_client = queue_client
        self.session = session

    async def forgot_password(self, email: str
                              ) ->None:
        """
        Creates a reset token for an existing user and returns RAW token
        (caller should email it to user).
        For unknown email, returns empty string to avoid user enumeration.
        """
        email = email.lower().strip()
        user = await self.user_repo.find_by_email(email)
        if not user:
            # Avoid leaking whether email exists
            return ""

        # Optional cleanup of old tokens for this user
        await self.reset_token_repo.delete_all_for_user(user.id)

        raw_token = generate_reset_token()
        token_hash = hash_reset_token(raw_token)

        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
        )

        reset_token = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,   
            expires_at=expires_at,
            is_used=False,
        )
        await self.reset_token_repo.create(reset_token)
        await self.session.commit()
        job = PasswordResetEmailJob.create(
            recipient_email=user.email,
            reset_token=raw_token,
        )
        await self.queue_client.enqueue(
            queue_name="email_jobs",
            payload=job.to_dict(),
        )
        return 

    async def reset_password(self, raw_token: str, new_password: str) -> None:
        """
        Validates reset token, marks token as used, updates user password.
        Raises InvalidOrExpiredResetTokenError when invalid.
        """
        token_hash = hash_reset_token(raw_token)
        token_row = await self.reset_token_repo.get_by_hash(token_hash)

        now = datetime.now(timezone.utc)
        if (
            not token_row
            or token_row.is_used
            or token_row.expires_at <= now
        ):
            raise InvalidOrExpiredResetTokenError("Invalid or expired reset token")

        user = await self.user_repo.find_by_id(token_row.user_id)
        if not user:
            raise InvalidOrExpiredResetTokenError("Invalid reset token user")

        hashed = hash_password(new_password)
        user.password_hash = hashed

        # Mark token used
        await self.reset_token_repo.mark_used(token_row.id)

        await self.session.commit()
        job=PasswordChangedEmailJob.create(
            recipient_email=user.email,
        )
        await self.queue_client.enqueue(
            queue_name="email_jobs",
            payload=job.to_dict(),
        )
