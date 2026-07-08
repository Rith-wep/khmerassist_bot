"""Prints a summary of the database so you can eyeball the import result.

Run after the migration and the import script:
    python scripts/verify_import.py
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import inspect

from app.db.session import SessionLocal, engine
from app.models import Business, BotConfig, Conversation, KnowledgeItem, Lead, Message, User

MODELS = [Business, User, BotConfig, KnowledgeItem, Conversation, Message, Lead]


def main() -> None:
    inspector = inspect(engine)
    print("Tables in database:")
    for table_name in sorted(inspector.get_table_names()):
        print(f"  - {table_name}")

    db = SessionLocal()
    try:
        print("\nRow counts:")
        for model in MODELS:
            count = db.query(model).count()
            print(f"  - {model.__tablename__}: {count}")

        print("\nBusinesses:")
        for business in db.query(Business).all():
            print(f"  [{business.id}] {business.name} ({business.business_type.value}, {business.status.value})")

            bot_config = db.query(BotConfig).filter(BotConfig.business_id == business.id).first()
            if bot_config:
                print(
                    f"      bot_config: owner_chat_id={bot_config.owner_chat_id}, "
                    f"token=***{bot_config.telegram_bot_token_encrypted[-6:]} (encrypted), "
                    f"active={bot_config.is_active}"
                )

            items = (
                db.query(KnowledgeItem)
                .filter(KnowledgeItem.business_id == business.id)
                .order_by(KnowledgeItem.sort_order)
                .all()
            )
            print(f"      knowledge_items ({len(items)}):")
            for item in items:
                price_part = f" - {item.price}" if item.price else ""
                print(f"        [{item.category.value}] {item.title}{price_part}")

            leads = db.query(Lead).filter(Lead.business_id == business.id).all()
            print(f"      leads ({len(leads)}):")
            for lead in leads:
                print(f"        {lead.customer_name} / {lead.phone} - {lead.interest}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
