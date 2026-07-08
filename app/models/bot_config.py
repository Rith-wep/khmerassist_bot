from datetime import datetime

from sqlalchemy import BigInteger, Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BotConfig(Base):
    __tablename__ = "bot_configs"

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id"), nullable=False, unique=True, index=True
    )
    # Fernet ciphertext, never the raw token — see app.core.security.encrypt_secret/decrypt_secret.
    telegram_bot_token_encrypted: Mapped[str] = mapped_column(String(500), nullable=False)
    owner_chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    bot_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_started_at: Mapped[datetime | None] = mapped_column(nullable=True)
