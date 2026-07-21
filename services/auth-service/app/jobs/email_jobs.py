from __future__ import annotations

from dataclasses import dataclass, asdict
from uuid import uuid4
from datetime import datetime, timezone

@dataclass(frozen=True)
class PasswordResetEmailJob:
    job_type: str
    recipient_email: str
    reset_token:str
    job_id: str
    created_at:str
    attempts: int = 0
    max_attempts: int = 3

    @classmethod
    def create(cls, recipient_email: str, reset_token: str) -> "PasswordResetEmailJob":
        return cls(
            job_type="password_reset_email",
            recipient_email=recipient_email,
            reset_token=reset_token,
            job_id=str(uuid4()),
            created_at=datetime.now(timezone.UTC).isoformat()
        )

    def to_dict(self) -> dict[str, str]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "PasswordResetEmailJob":
        return cls(
            job_type=data["job_type"],
            recipient_email=data["recipient_email"],
            reset_token=data["reset_token"],
            job_id=data["job_id"],
            created_at=data["created_at"],
            attempts=int(data.get("attempts", 0)),
            max_attempts=int(data.get("max_attempts", 3)),
        )
    

@dataclass(frozen=True)
class PasswordChangedEmailJob:
    job_type: str
    recipient_email: str
    job_id: str
    created_at:str
    attempts: int = 0
    max_attempts: int = 3

    @classmethod
    def create(cls, recipient_email: str) -> "PasswordChangedEmailJob":
        return cls(
            job_type="password_changed_email",
            recipient_email=recipient_email,
            job_id=str(uuid4()),
            created_at=datetime.now(timezone.UTC).isoformat()
        )

    def to_dict(self) -> dict[str, str]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "PasswordChangedEmailJob":
        return cls(
            job_type=data["job_type"],
            recipient_email=data["recipient_email"],
            job_id=data["job_id"],
            created_at=data["created_at"],
            attempts=int(data.get("attempts", 0)),
            max_attempts=int(data.get("max_attempts", 3))
        )