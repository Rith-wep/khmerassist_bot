from datetime import datetime

from sqlalchemy import BigInteger, Boolean, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.time import utcnow
from app.db.base import Base


class Conversation(Base):
    __tablename__ = "conversations"
    __table_args__ = (
        Index("ix_conversations_business_chat", "business_id", "customer_chat_id"),
        Index("ix_conversations_business_last_message", "business_id", "last_message_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id"), nullable=False, index=True
    )
    customer_chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    customer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    started_at: Mapped[datetime] = mapped_column(default=utcnow)
    last_message_at: Mapped[datetime] = mapped_column(default=utcnow)
    handed_off: Mapped[bool] = mapped_column(Boolean, default=False)
