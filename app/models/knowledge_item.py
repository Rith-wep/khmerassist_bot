import enum
from datetime import datetime

from sqlalchemy import Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.time import utcnow
from app.db.base import Base


class KnowledgeCategory(str, enum.Enum):
    service = "service"
    faq = "faq"
    hours = "hours"
    location = "location"
    policy = "policy"
    other = "other"


class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"
    __table_args__ = (Index("ix_knowledge_items_business_sort", "business_id", "sort_order"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id"), nullable=False, index=True
    )
    category: Mapped[KnowledgeCategory] = mapped_column(
        Enum(KnowledgeCategory, name="knowledge_category"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content_km: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Free-form (e.g. "$15" or "$20 - $40"), not numeric — real client price lists include ranges.
    price: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)
