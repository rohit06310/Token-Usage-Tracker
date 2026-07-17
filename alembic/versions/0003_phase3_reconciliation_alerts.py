"""
Phase 3 schema migration.

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-06

Changes:
  - Add `confidence_level` enum column to `providers`
  - Create `reconciliation_results` table
  - Create `alerts_sent` table
  - Create `job_runs` table
"""

from typing import Sequence, Union
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. confidence_level to providers
    confidence_level_enum = sa.Enum(
        "verified", "self_logged_only", "unreliable",
        name="confidence_level_enum",
        create_type=True,
    )
    confidence_level_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "ai_providers",
        sa.Column(
            "confidence_level",
            confidence_level_enum,
            nullable=False,
            server_default="self_logged_only",
        ),
    )

    # 2. reconciliation_results
    reconciliation_status_enum = sa.Enum(
        "matched", "mismatched", "no_official_data",
        name="reconciliation_status_enum",
        create_type=True,
    )

    op.create_table(
        "ai_reconciliation_results",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("provider_id", UUID(as_uuid=True), sa.ForeignKey("ai_providers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("self_logged_tokens", sa.Integer(), nullable=False),
        sa.Column("provider_reported_tokens", sa.Integer(), nullable=False),
        sa.Column("difference", sa.Integer(), nullable=False),
        sa.Column("percent_diff", sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column("status", reconciliation_status_enum, nullable=False),
        sa.Column("checked_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_ai_reconciliation_results_provider_id", "ai_reconciliation_results", ["provider_id"])
    op.create_index("ix_ai_reconciliation_results_period_start", "ai_reconciliation_results", ["period_start"])
    op.create_index("ix_ai_reconciliation_results_status", "ai_reconciliation_results", ["status"])

    # 3. alerts_sent
    op.create_table(
        "ai_alerts_sent",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("provider_id", UUID(as_uuid=True), sa.ForeignKey("ai_providers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("alert_type", sa.String(length=50), nullable=False),
        sa.Column("threshold_percent", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_ai_alerts_sent_provider_id", "ai_alerts_sent", ["provider_id"])
    op.create_index("ix_ai_alerts_sent_alert_type", "ai_alerts_sent", ["alert_type"])
    op.create_index("ix_ai_alerts_sent_window_start", "ai_alerts_sent", ["window_start"])

    # 4. job_runs
    job_status_enum = sa.Enum(
        "success", "failed", "running",
        name="job_status_enum",
        create_type=True,
    )

    op.create_table(
        "ai_job_runs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("job_name", sa.String(length=100), nullable=False),
        sa.Column("status", job_status_enum, nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_ai_job_runs_job_name", "ai_job_runs", ["job_name"])
    op.create_index("ix_ai_job_runs_status", "ai_job_runs", ["status"])


def downgrade() -> None:
    op.drop_table("ai_job_runs")
    sa.Enum(name="job_status_enum").drop(op.get_bind(), checkfirst=True)

    op.drop_table("ai_alerts_sent")
    
    op.drop_table("ai_reconciliation_results")
    sa.Enum(name="reconciliation_status_enum").drop(op.get_bind(), checkfirst=True)

    op.drop_column("ai_providers", "confidence_level")
    sa.Enum(name="confidence_level_enum").drop(op.get_bind(), checkfirst=True)
