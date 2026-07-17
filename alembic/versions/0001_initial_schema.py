"""
Initial schema migration.

Revision ID: 0001
Revises: (none — this is the first migration)
Create Date: 2026-07-06

Creates tables:
  - providers
  - api_keys
  - usage_logs
  - rate_limits
"""

from typing import Sequence, Union
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ----------------------------------------------------------------
    # providers
    # ----------------------------------------------------------------
    op.create_table(
        "ai_providers",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(120), nullable=False, unique=True),
        sa.Column("slug", sa.String(60), nullable=False, unique=True),
        sa.Column("base_url", sa.String(500), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_ai_providers_slug", "ai_providers", ["slug"])

    # ----------------------------------------------------------------
    # api_keys
    # ----------------------------------------------------------------
    op.create_table(
        "ai_api_keys",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "provider_id",
            UUID(as_uuid=True),
            sa.ForeignKey("ai_providers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("encrypted_key", sa.Text, nullable=False),
        sa.Column("label", sa.String(200), nullable=False, server_default="default"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_ai_api_keys_provider_id", "ai_api_keys", ["provider_id"])

    # ----------------------------------------------------------------
    # usage_logs
    # ----------------------------------------------------------------
    op.create_table(
        "ai_usage_logs",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "provider_id",
            UUID(as_uuid=True),
            sa.ForeignKey("ai_providers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("model", sa.String(200), nullable=False),
        sa.Column("tokens_in", sa.Integer, nullable=False, server_default="0"),
        sa.Column("tokens_out", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "cost",
            sa.Numeric(precision=18, scale=8),
            nullable=False,
            server_default="0",
        ),
        sa.Column("project_tag", sa.String(200), nullable=True),
        sa.Column("raw_response", JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_ai_usage_logs_provider_id", "ai_usage_logs", ["provider_id"])
    op.create_index("ix_ai_usage_logs_model", "ai_usage_logs", ["model"])
    op.create_index("ix_ai_usage_logs_project_tag", "ai_usage_logs", ["project_tag"])
    op.create_index("ix_ai_usage_logs_created_at", "ai_usage_logs", ["created_at"])

    # ----------------------------------------------------------------
    # rate_limits
    # ----------------------------------------------------------------
    op.create_table(
        "ai_rate_limits",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "provider_id",
            UUID(as_uuid=True),
            sa.ForeignKey("ai_providers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("tier_name", sa.String(100), nullable=False),
        sa.Column("rpm", sa.Integer, nullable=True),
        sa.Column("tpm", sa.Integer, nullable=True),
        sa.Column("rpd", sa.Integer, nullable=True),
        sa.Column("effective_date", sa.Date, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_ai_rate_limits_provider_id", "ai_rate_limits", ["provider_id"])


def downgrade() -> None:
    op.drop_table("ai_rate_limits")
    op.drop_table("ai_usage_logs")
    op.drop_table("ai_api_keys")
    op.drop_table("ai_providers")
