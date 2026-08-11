from __future__ import annotations
from datetime import datetime
from sqlalchemy import (
    String,
    ForeignKey,
    DateTime,
    func,
    UniqueConstraint,
    Index,
    CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

class OAuthAccount(Base):
    __tablename__ = "oauth_accounts"

    __table_args__ = (
        # prevent empty provider/provider_user_id
        CheckConstraint("char_length(provider) >= 2", name="ck_oauth_accounts_provider_min_len"),
        CheckConstraint(
            "char_length(provider_user_id) >= 1",
            name="ck_oauth_accounts_provider_user_id_not_empty",
        ),

        # same external identity can't link to multiple users
        UniqueConstraint(
            "provider",
            "provider_user_id",
            name="uq_oauth_accounts_provider_provider_user_id",
        ),

        # one linked account per provider per user (recommended)
        UniqueConstraint(
            "user_id",
            "provider",
            name="uq_oauth_accounts_user_id_provider",
        ),

        Index("ix_oauth_accounts_user_id", "user_id"),
        Index("ix_oauth_accounts_provider", "provider"),
        Index("ix_oauth_accounts_provider_user_id", "provider_user_id"),
        Index("ix_oauth_accounts_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # e.g. "google", "github"
    provider: Mapped[str] = mapped_column(String(30), nullable=False)

    # e.g. Google "sub", GitHub user id as string
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False)

    # optional provider-side email snapshot
    provider_email: Mapped[str | None] = mapped_column(String(120), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User", back_populates="oauth_accounts")