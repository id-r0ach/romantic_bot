from datetime import datetime

from sqlalchemy import ForeignKey, String, DateTime, func, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import Base


class Couple(Base):
    __tablename__ = "couples"

    id: Mapped[int] = mapped_column(primary_key=True)

    user1_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"))
    user2_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.telegram_id"), nullable=True)

    status: Mapped[str] = mapped_column(String(10), default="pending")
    invite_code: Mapped[str] = mapped_column(String(6), unique=True, index=True)
    invite_expires: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    activated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Связи — чтобы потом получать имя партнёра без лишних запросов
    user1 = relationship("User", foreign_keys=[user1_id], primaryjoin="Couple.user1_id == User.telegram_id")
    user2 = relationship("User", foreign_keys=[user2_id], primaryjoin="Couple.user2_id == User.telegram_id")