"""
Phase 2 schema migration.

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-06

Changes:
  - Add `status` column (enum: success/failed) to usage_logs
  - Create `provider_reported_usage` table
"""

from typing import Sequence, Union
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ----------------------------------------------------------------
    # 1. Add `status` enum + column to usage_logs
    # ----------------------------------------------------------------
    # Create the Postgres enum type first
    call_status_enum = sa.Enum(
        "success", "failed",
        name="call_status_enum",
        create_type=True,
    )
    call_status_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "ai_usage_logs",
        sa.Column(
            "status",
            call_status_enum,
            nullable=False,
            server_default="success",
            comment="Whether the API call succeeded or failed.",
        ),
    )
    op.create_index("ix_usage_logs_status", "ai_usage_logs", ["status"])

    # ----------------------------------------------------------------
    # 2. Create provider_reported_usage
    # ----------------------------------------------------------------
    op.create_table(
        "ai_provider_reported_usage",
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
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("total_tokens", sa.Integer, nullable=True),
        sa.Column("total_cost", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "source",
            sa.String(200),
            nullable=False,
            server_default="api",
        ),
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
    op.create_index(
        "ix_provider_reported_usage_provider_id",
        "ai_provider_reported_usage",
        ["provider_id"],
    )
    op.create_index(
        "ix_provider_reported_usage_period_start",
        "ai_provider_reported_usage",
        ["period_start"],
    )


def downgrade() -> None:
    op.drop_table("ai_provider_reported_usage")
    op.drop_index("ix_usage_logs_status", table_name="ai_usage_logs")
    op.drop_column("ai_usage_logs", "status")
    sa.Enum(name="call_status_enum").drop(op.get_bind(), checkfirst=True)
