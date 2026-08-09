from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from database.models.base import Base


class RelationshipTree(Base):
    __tablename__ = "relationship_trees"

    couple_id: Mapped[int] = mapped_column(
        ForeignKey("couples.id"),
        primary_key=True,
    )

    xp: Mapped[int] = mapped_column(default=0, server_default="0", nullable=False)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )