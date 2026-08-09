from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from database.models.base import Base


class Memory(Base):
    __tablename__ = "memories"
    __table_args__ = (
        Index("ix_memories_couple_id_memory_date", "couple_id", "memory_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    couple_id: Mapped[int] = mapped_column(
        ForeignKey("couples.id"),
        nullable=False,
    )

    author_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id"),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    memory_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Пока не используем, оставляем под будущие фото.
    photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Нужно для идемпотентных напоминаний о годовщинах.
    last_notified: Mapped[date | None] = mapped_column(Date, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )