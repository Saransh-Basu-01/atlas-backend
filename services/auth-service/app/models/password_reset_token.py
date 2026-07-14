from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, DateTime, Boolean, ForeignKey, func, Index,CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    __table_args__ = (
        CheckConstraint(
                "expires_at > created_at",
                name="ck_password_reset_expiry",
        ),       
        Index("ix_password_reset_tokens_token_hash", "token_hash"),
        Index("ix_password_reset_tokens_user_id", "user_id"),
        Index("ix_password_reset_tokens_expires_at", "expires_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
    ForeignKey("users.id", ondelete="CASCADE"),
    nullable=False,
)
    token_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )
    is_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    expires_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    server_default=func.now(),
    nullable=False,
    )

    # Relationship with User model
    user: Mapped["User"] = relationship("User", back_populates="reset_tokens")