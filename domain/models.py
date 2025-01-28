from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import MetaData, BigInteger, func
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(AsyncAttrs, DeclarativeBase):
    """Основной класс, от которого наследуются остальные модели"""
    metadata = MetaData(
        naming_convention={
            "ix": "%(column_0_label)s_idx",
            "uq": "%(table_name)s_%(column_0_name)s_key",
            "ck": "%(table_name)s_%(constraint_name)s_check",
            "fk": "%(table_name)s_%(column_0_name)s_%(referred_table_name)s_fkey",
            "pk": "%(table_name)s_pkey"
        }
    )


class Status(Enum):
    PROCESSING = 1
    DECLINED = 2
    VERIFIED = 3


class Visitor(Base):
    __tablename__ = "visitor"

    chat_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    is_admin: Mapped[bool] = mapped_column(default=False)
    model: Mapped[str] = mapped_column(default="gpt-4o-mini")
    status: Mapped[int] = mapped_column(default=1)
    user_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    full_name: Mapped[Optional[str]] = mapped_column()
    username: Mapped[Optional[str]] = mapped_column()
    comment: Mapped[Optional[str]] = mapped_column()
    created_at: Mapped[Optional[datetime]] = mapped_column(server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Visitor(" \
               f"full_name={self.full_name}, " \
               f"username={self.username}, " \
               f"status={self.status}, " \
               f"model={self.model}, " \
               f"is_admin={self.is_admin}, " \
               f"chat_id={self.chat_id}, " \
               f")>"

    def short_str(self):
        return f"{self.full_name} @{self.username}"

    def __str__(self):
        return f"{self.full_name} @{self.username} со {Status(self.status)} и моделью {self.model}"
