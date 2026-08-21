from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from database.models.base import Base


class ReasonGiftStatus:
    DRAFT = "draft"
    ACTIVE = "active"
    CANCELLED = "cancelled"
    FINISHED = "finished"


class ReasonGift(Base):
    __tablename__ = "reason_gifts"

    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'active', 'cancelled', 'finished')",
            name="ck_reason_gifts_status",
        ),
        # Один draft/active подарок на автора внутри пары
        Index(
            "ix_reason_gifts_one_open_gift_per_author",
            "couple_id",
            "author_id",
            unique=True,
            postgresql_where=text("status IN ('draft', 'active')"),
        ),
        Index(
            "ix_reason_gifts_author_status",
            "author_id",
            "status",
        ),
        Index(
            "ix_reason_gifts_recipient_status",
            "recipient_id",
            "status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    couple_id: Mapped[int] = mapped_column(
        ForeignKey("couples.id"),
        index=True,
        nullable=False,
    )

    author_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id"),
        nullable=False,
    )

    recipient_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id"),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default=ReasonGiftStatus.DRAFT,
        server_default=ReasonGiftStatus.DRAFT,
        nullable=False,
    )

    # Когда получатель последний раз открыл причину
    last_opened_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Когда получателю последний раз слали напоминание
    last_reminded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    activated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class Reason(Base):
    __tablename__ = "reasons"

    __table_args__ = (
        UniqueConstraint(
            "gift_id",
            "position",
            name="uq_reasons_gift_position",
        ),
        CheckConstraint(
            "position > 0",
            name="ck_reasons_position_positive",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    gift_id: Mapped[int] = mapped_column(
        ForeignKey("reason_gifts.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    text: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    opened: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    opened_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )