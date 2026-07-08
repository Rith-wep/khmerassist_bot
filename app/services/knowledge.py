"""Assembles a business's knowledge_items into the same facts text v1 read
from business_info.md, so the AI's system instruction gets equivalent content.
"""
from app.models.knowledge_item import KnowledgeItem


def build_business_info_text(items: list[KnowledgeItem]) -> str:
    by_category: dict[str, list[KnowledgeItem]] = {}
    for item in items:
        by_category.setdefault(item.category.value, []).append(item)

    lines: list[str] = []

    for item in by_category.get("location", []):
        lines.append(f"## {item.title}")
        if item.content_km:
            lines.append(f"- Khmer: {item.content_km}")
        if item.content_en:
            lines.append(f"- English: {item.content_en}")
        lines.append("")

    for item in by_category.get("hours", []):
        lines.append(f"## {item.title}")
        if item.content_km:
            lines.append(f"- Khmer: {item.content_km}")
        if item.content_en:
            lines.append(f"- English: {item.content_en}")
        lines.append("")

    for item in by_category.get("other", []):
        lines.append(f"## {item.title}")
        lines.append(f"- {item.content_en or item.content_km}")
        lines.append("")

    services = by_category.get("service", [])
    if services:
        lines.append("## Services and prices")
        lines.append("| Service (English) | Service (Khmer) | Price |")
        lines.append("|---|---|---|")
        for item in services:
            lines.append(f"| {item.content_en or item.title} | {item.content_km or ''} | {item.price or ''} |")
        lines.append("")

    policies = by_category.get("policy", [])
    if policies:
        lines.append("## Policies")
        for item in policies:
            lines.append(f"### {item.title}")
            if item.content_en:
                lines.append(item.content_en)
            if item.content_km:
                lines.append(item.content_km)
        lines.append("")

    faqs = by_category.get("faq", [])
    if faqs:
        lines.append("## Frequently asked questions")
        for i, item in enumerate(faqs, 1):
            lines.append(f"{i}. **{item.title}**")
            if item.content_en:
                lines.append(f"   {item.content_en}")
            if item.content_km:
                lines.append(f"   {item.content_km}")
        lines.append("")

    return "\n".join(lines).strip()
