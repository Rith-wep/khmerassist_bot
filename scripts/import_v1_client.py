"""One-time import: v1_legacy's business_info.md + leads.json -> the v2 database.

Creates the first business row (the existing client), its knowledge_items,
its bot_configs row (token encrypted), and its historical leads/conversations.

Run once, after the initial migration has been applied:
    python scripts/import_v1_client.py
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import dotenv_values

from app.core.security import encrypt_secret
from app.db.session import SessionLocal
from app.repositories.bot_config import BotConfigRepository
from app.repositories.business import BusinessRepository
from app.repositories.conversation import ConversationRepository
from app.repositories.knowledge_item import KnowledgeItemRepository
from app.repositories.lead import LeadRepository

ROOT = Path(__file__).resolve().parent.parent
V1_DIR = ROOT / "v1_legacy"
BUSINESS_INFO_PATH = V1_DIR / "business" / "business_info.md"
LEADS_PATH = V1_DIR / "leads.json"
V1_ENV_PATH = V1_DIR / ".env"


def split_sections(md_text: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current = None
    buffer: list[str] = []
    for line in md_text.splitlines():
        header = re.match(r"^##\s+(.*)", line)
        if header:
            if current:
                sections[current] = "\n".join(buffer).strip()
            current = header.group(1).strip()
            buffer = []
        elif current:
            buffer.append(line)
    if current:
        sections[current] = "\n".join(buffer).strip()
    return sections


def extract_km_en(section_text: str) -> tuple[str | None, str | None]:
    km = re.search(r"-\s*Khmer:\s*(.+)", section_text)
    en = re.search(r"-\s*English:\s*(.+)", section_text)
    return (km.group(1).strip() if km else None, en.group(1).strip() if en else None)


def parse_services_table(section_text: str) -> list[tuple[str, str, str]]:
    rows = []
    for line in section_text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 3:
            continue
        if cells[0].lower().startswith("service") or set(cells[0]) <= {"-", " "}:
            continue
        rows.append((cells[0], cells[1], cells[2]))
    return rows


def parse_faqs(section_text: str) -> list[tuple[str, str]]:
    faqs = []
    entries = re.split(r"\n(?=\d+\.\s+)", section_text.strip())
    for entry in entries:
        entry = entry.strip()
        match = re.match(r"\d+\.\s+(.*)", entry, re.DOTALL)
        if not match:
            continue
        lines = match.group(1).splitlines()
        question = lines[0].strip().replace("**", "")
        answer = " ".join(line.strip() for line in lines[1:] if line.strip())
        faqs.append((question, answer))
    return faqs


def build_knowledge_rows(sections: dict[str, str]) -> list[dict]:
    rows: list[dict] = []

    if "Location" in sections:
        km, en = extract_km_en(sections["Location"])
        rows.append(
            {"category": "location", "title": "Location", "content_km": km, "content_en": en, "sort_order": 1}
        )

    if "Phone number" in sections:
        phone = sections["Phone number"].lstrip("- ").strip()
        rows.append(
            {"category": "other", "title": "Phone Number", "content_km": phone, "content_en": phone, "sort_order": 2}
        )

    if "Opening hours" in sections:
        km, en = extract_km_en(sections["Opening hours"])
        rows.append(
            {"category": "hours", "title": "Opening Hours", "content_km": km, "content_en": en, "sort_order": 3}
        )

    services_key = next((k for k in sections if k.lower().startswith("services and prices")), None)
    if services_key:
        for i, (en_name, km_name, price) in enumerate(parse_services_table(sections[services_key])):
            rows.append(
                {
                    "category": "service",
                    "title": en_name,
                    "content_km": km_name,
                    "content_en": en_name,
                    "price": price,
                    "sort_order": 10 + i,
                }
            )

    faq_key = next((k for k in sections if "frequently asked" in k.lower()), None)
    if faq_key:
        for i, (question, answer) in enumerate(parse_faqs(sections[faq_key])):
            rows.append(
                {
                    "category": "faq",
                    "title": question,
                    "content_en": answer,
                    "sort_order": 20 + i,
                }
            )

    return rows


def main() -> None:
    md_text = BUSINESS_INFO_PATH.read_text(encoding="utf-8")
    sections = split_sections(md_text)
    _, business_name = extract_km_en(sections.get("Clinic name", ""))
    business_name = business_name or "Imported Business"

    v1_env = dotenv_values(V1_ENV_PATH)
    telegram_token = v1_env.get("TELEGRAM_BOT_TOKEN")
    owner_chat_id = v1_env.get("OWNER_CHAT_ID")
    if not telegram_token or not owner_chat_id:
        raise SystemExit("v1_legacy/.env is missing TELEGRAM_BOT_TOKEN or OWNER_CHAT_ID")

    leads_data = json.loads(LEADS_PATH.read_text(encoding="utf-8")) if LEADS_PATH.exists() else []

    db = SessionLocal()
    try:
        business_repo = BusinessRepository(db)
        existing = [b for b in business_repo.list_all() if b.name == business_name]
        if existing:
            print(f"Business '{business_name}' already imported (id={existing[0].id}). Skipping.")
            return

        business = business_repo.create(
            name=business_name,
            business_type="clinic",
            default_language="km",
            plan="trial",
            status="active",
        )
        db.flush()

        bot_config_repo = BotConfigRepository(db, business.id)
        bot_config_repo.create(
            telegram_bot_token_encrypted=encrypt_secret(telegram_token),
            owner_chat_id=int(owner_chat_id),
            is_active=True,
        )

        knowledge_repo = KnowledgeItemRepository(db, business.id)
        for row in build_knowledge_rows(sections):
            knowledge_repo.create(**row)

        conversation_repo = ConversationRepository(db, business.id)
        lead_repo = LeadRepository(db, business.id)
        for lead in leads_data:
            timestamp = datetime.fromisoformat(lead["timestamp"])
            conversation = conversation_repo.create(
                customer_chat_id=int(lead["chat_id"]),
                customer_name=lead.get("name"),
                started_at=timestamp,
                last_message_at=timestamp,
                handed_off=False,
            )
            db.flush()
            lead_repo.create(
                conversation_id=conversation.id,
                customer_name=lead.get("name"),
                phone=lead.get("phone"),
                interest=lead.get("interest"),
                created_at=timestamp,
                notified_owner=True,
            )

        db.commit()
        print(f"Imported business '{business_name}' (id={business.id}).")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
