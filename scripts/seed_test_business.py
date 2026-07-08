"""One-time seed: creates a second business ("Test Phone Shop") so multi-bot
tenant isolation (build step 3) can be proven against real, different data.

Run interactively (prompts for the new bot's token and owner chat ID,
so neither ends up in shell history):
    python scripts/seed_test_business.py
"""
import sys
from getpass import getpass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.security import encrypt_secret
from app.db.session import SessionLocal
from app.repositories.bot_config import BotConfigRepository
from app.repositories.business import BusinessRepository
from app.repositories.knowledge_item import KnowledgeItemRepository

BUSINESS_NAME = "Test Phone Shop"

KNOWLEDGE_ROWS = [
    {
        "category": "location",
        "title": "Location",
        "content_en": "Shop 42, Street 214, Phnom Penh",
        "content_km": "ហាងលេខ ៤២ ផ្លូវ ២១៤ រាជធានីភ្នំពេញ",
        "sort_order": 1,
    },
    {
        "category": "hours",
        "title": "Opening Hours",
        "content_en": "Every day, 8:00 AM - 8:00 PM",
        "content_km": "រាល់ថ្ងៃ ម៉ោង ៨:០០ ព្រឹក ដល់ ៨:០០ យប់",
        "sort_order": 2,
    },
    {
        "category": "service",
        "title": "iPhone 15",
        "content_en": "iPhone 15",
        "content_km": "អាយហ្វូន ១៥",
        "price": "$780",
        "sort_order": 10,
    },
    {
        "category": "service",
        "title": "Samsung Galaxy S24",
        "content_en": "Samsung Galaxy S24",
        "content_km": "សាំសុង ហ្គាឡាក់ស៊ី S24",
        "price": "$650",
        "sort_order": 11,
    },
    {
        "category": "service",
        "title": "Xiaomi Redmi Note 13",
        "content_en": "Xiaomi Redmi Note 13",
        "content_km": "ស៊ាវមី រ៉េតមីណូត ១៣",
        "price": "$180",
        "sort_order": 12,
    },
    {
        "category": "service",
        "title": "Oppo Reno 11",
        "content_en": "Oppo Reno 11",
        "content_km": "អុបផូ រេណូ ១១",
        "price": "$320",
        "sort_order": 13,
    },
    {
        "category": "service",
        "title": "Vivo Y36",
        "content_en": "Vivo Y36",
        "content_km": "វីវ៉ូ Y36",
        "price": "$150",
        "sort_order": 14,
    },
    {
        "category": "faq",
        "title": "Do you offer warranty?",
        "content_en": "Yes, all phones come with a 12-month shop warranty.",
        "sort_order": 20,
    },
    {
        "category": "faq",
        "title": "Can I trade in my old phone?",
        "content_en": "Yes, bring your old phone in for a trade-in valuation.",
        "sort_order": 21,
    },
    {
        "category": "faq",
        "title": "Do you offer installment payment?",
        "content_en": "Yes, installments are available over 3, 6, or 12 months with partner providers.",
        "sort_order": 22,
    },
]


def main() -> None:
    db = SessionLocal()
    try:
        business_repo = BusinessRepository(db)
        existing = [b for b in business_repo.list_all() if b.name == BUSINESS_NAME]
        if existing:
            print(f"Business '{BUSINESS_NAME}' already exists (id={existing[0].id}). Skipping.")
            return

        token = getpass("Telegram bot token for the phone shop's bot (input hidden): ").strip()
        owner_chat_id_raw = input("Owner's Telegram chat ID: ").strip()
        if not token or not owner_chat_id_raw:
            raise SystemExit("Both a bot token and an owner chat ID are required.")

        business = business_repo.create(
            name=BUSINESS_NAME,
            business_type="shop",
            default_language="km",
            plan="trial",
            status="active",
        )
        db.flush()

        BotConfigRepository(db, business.id).create(
            telegram_bot_token_encrypted=encrypt_secret(token),
            owner_chat_id=int(owner_chat_id_raw),
            is_active=True,
        )

        knowledge_repo = KnowledgeItemRepository(db, business.id)
        for row in KNOWLEDGE_ROWS:
            knowledge_repo.create(**row)

        db.commit()
        print(f"Created business '{BUSINESS_NAME}' (id={business.id}) with {len(KNOWLEDGE_ROWS)} knowledge_items.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
