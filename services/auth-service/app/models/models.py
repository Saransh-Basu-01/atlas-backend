from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, func, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    __table_args__ = (
        CheckConstraint("char_length(username) >= 3", name="ck_users_username_min_len"),
        Index("ix_users_username", "username"),
        Index("ix_users_email", "email"),
        Index("ix_users_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True,index=True)
    email: Mapped[str] = mapped_column(String(120), nullable=False, unique=True,index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )