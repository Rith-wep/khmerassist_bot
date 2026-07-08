"""initial schema

Revision ID: d2c7e9e6fd5f
Revises:
Create Date: 2026-07-08 01:23:41.249779

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "d2c7e9e6fd5f"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "businesses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "business_type",
            sa.Enum("clinic", "shop", "real_estate", "other", name="business_type"),
            nullable=False,
            server_default="other",
        ),
        sa.Column("default_language", sa.String(length=10), nullable=False, server_default="km"),
        sa.Column(
            "plan",
            sa.Enum("trial", "basic", "standard", "premium", name="plan"),
            nullable=False,
            server_default="trial",
        ),
        sa.Column(
            "status",
            sa.Enum("active", "paused", "cancelled", name="business_status"),
            nullable=False,
            server_default="active",
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id", name="pk_businesses"),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("business_id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "role",
            sa.Enum("owner", "staff", name="user_role"),
            nullable=False,
            server_default="owner",
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(
            ["business_id"], ["businesses.id"], name="fk_users_business_id_businesses"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
    )
    op.create_index("ix_users_business_id", "users", ["business_id"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "bot_configs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("business_id", sa.Integer(), nullable=False),
        sa.Column("telegram_bot_token_encrypted", sa.String(length=500), nullable=False),
        sa.Column("owner_chat_id", sa.BigInteger(), nullable=False),
        sa.Column("bot_username", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_started_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["business_id"], ["businesses.id"], name="fk_bot_configs_business_id_businesses"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_bot_configs"),
    )
    op.create_index("ix_bot_configs_business_id", "bot_configs", ["business_id"], unique=True)

    op.create_table(
        "knowledge_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("business_id", sa.Integer(), nullable=False),
        sa.Column(
            "category",
            sa.Enum(
                "service", "faq", "hours", "location", "policy", "other",
                name="knowledge_category",
            ),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content_km", sa.Text(), nullable=True),
        sa.Column("content_en", sa.Text(), nullable=True),
        sa.Column("price", sa.String(length=100), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(
            ["business_id"], ["businesses.id"], name="fk_knowledge_items_business_id_businesses"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_knowledge_items"),
    )
    op.create_index("ix_knowledge_items_business_id", "knowledge_items", ["business_id"])
    op.create_index(
        "ix_knowledge_items_business_sort", "knowledge_items", ["business_id", "sort_order"]
    )

    op.create_table(
        "conversations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("business_id", sa.Integer(), nullable=False),
        sa.Column("customer_chat_id", sa.BigInteger(), nullable=False),
        sa.Column("customer_name", sa.String(length=255), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column(
            "last_message_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column("handed_off", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.ForeignKeyConstraint(
            ["business_id"], ["businesses.id"], name="fk_conversations_business_id_businesses"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_conversations"),
    )
    op.create_index("ix_conversations_business_id", "conversations", ["business_id"])
    op.create_index(
        "ix_conversations_business_chat", "conversations", ["business_id", "customer_chat_id"]
    )
    op.create_index(
        "ix_conversations_business_last_message",
        "conversations",
        ["business_id", "last_message_at"],
    )

    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("business_id", sa.Integer(), nullable=False),
        sa.Column(
            "direction",
            sa.Enum("customer", "bot", name="message_direction"),
            nullable=False,
        ),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(
            ["business_id"], ["businesses.id"], name="fk_messages_business_id_businesses"
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.id"],
            name="fk_messages_conversation_id_conversations",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_messages"),
    )
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])
    op.create_index("ix_messages_business_id", "messages", ["business_id"])
    op.create_index("ix_messages_business_created", "messages", ["business_id", "created_at"])

    op.create_table(
        "leads",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("business_id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("customer_name", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("interest", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column(
            "notified_owner", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.ForeignKeyConstraint(
            ["business_id"], ["businesses.id"], name="fk_leads_business_id_businesses"
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["conversations.id"], name="fk_leads_conversation_id_conversations"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_leads"),
    )
    op.create_index("ix_leads_business_id", "leads", ["business_id"])
    op.create_index("ix_leads_conversation_id", "leads", ["conversation_id"])
    op.create_index("ix_leads_business_created", "leads", ["business_id", "created_at"])


def downgrade() -> None:
    op.drop_table("leads")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("knowledge_items")
    op.drop_table("bot_configs")
    op.drop_table("users")
    op.drop_table("businesses")

    bind = op.get_bind()
    for enum_name in (
        "message_direction",
        "knowledge_category",
        "user_role",
        "business_status",
        "plan",
        "business_type",
    ):
        sa.Enum(name=enum_name).drop(bind, checkfirst=True)
