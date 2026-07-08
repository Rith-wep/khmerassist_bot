import enum
from datetime import datetime

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.time import utcnow
from app.db.base import Base


class BusinessType(str, enum.Enum):
    clinic = "clinic"
    shop = "shop"
    real_estate = "real_estate"
    other = "other"


class Plan(str, enum.Enum):
    trial = "trial"
    basic = "basic"
    standard = "standard"
    premium = "premium"


class BusinessStatus(str, enum.Enum):
    active = "active"
    paused = "paused"
    cancelled = "cancelled"


class Business(Base):
    __tablename__ = "businesses"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    business_type: Mapped[BusinessType] = mapped_column(
        Enum(BusinessType, name="business_type"), default=BusinessType.other
    )
    default_language: Mapped[str] = mapped_column(String(10), default="km")
    plan: Mapped[Plan] = mapped_column(Enum(Plan, name="plan"), default=Plan.trial)
    status: Mapped[BusinessStatus] = mapped_column(
        Enum(BusinessStatus, name="business_status"), default=BusinessStatus.active
    )
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
