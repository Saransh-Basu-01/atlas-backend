from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Integer,String,func
from sqlalchemy.orm import Mapped,mapped_column,relationship
from db  import Base 
class User(Base):
    __tablename__="users"
    id:Mapped[int]=mapped_column(Integer,primary_key=True,index=True)
    username:Mapped[str]=mapped_column(String(50),unique=True,nullable=False,index=True)
    email:Mapped[str]=mapped_column(String(120),unique=True,nullable=False,index=True)
    password_hash:Mapped[str]=mapped_column(String(200),nullable=False)
    created_at: Mapped[datetime] = mapped_column(
    default=func.now(), # or func.now()
    nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
    default=func.now(), 
    onupdate=func.now(),
    nullable=False
    )