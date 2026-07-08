from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.knowledge_item import KnowledgeCategory


class KnowledgeItemCreate(BaseModel):
    category: KnowledgeCategory
    title: str = Field(min_length=1, max_length=255)
    content_km: str | None = None
    content_en: str | None = None
    price: str | None = Field(default=None, max_length=100)
    sort_order: int = 0


class KnowledgeItemUpdate(BaseModel):
    category: KnowledgeCategory | None = None
    title: str | None = Field(default=None, min_length=1, max_length=255)
    content_km: str | None = None
    content_en: str | None = None
    price: str | None = Field(default=None, max_length=100)
    sort_order: int | None = None


class KnowledgeItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: KnowledgeCategory
    title: str
    content_km: str | None
    content_en: str | None
    price: str | None
    sort_order: int
    updated_at: datetime
