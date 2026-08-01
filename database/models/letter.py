from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from database.models.base import Base  # <-- Исправленный путь


class Letter(Base):
    __tablename__ = "letters"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    couple_id: Mapped[int] = mapped_column(ForeignKey("couples.id"))
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.telegram_id"))
    receiver_id: Mapped[int] = mapped_column(ForeignKey("users.telegram_id"))

    text: Mapped[str] = mapped_column(String(4096))
    open_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    
    status: Mapped[str] = mapped_column(String(20), server_default="pending")
    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), 
        nullable=True, 
        default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )