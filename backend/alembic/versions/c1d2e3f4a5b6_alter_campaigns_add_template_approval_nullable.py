"""alter campaigns — add template/approval/cost columns (nullable)

Revision ID: c1d2e3f4a5b6
Revises: b1c2d3e4f5a6
Create Date: 2026-04-22 09:30:00.000000

M2a của plan voucher rebuild v2.2 — mở đường cho `campaigns` liên kết
`campaign_templates`, chứa approval tier + cost tracking + audit fields.

Pattern bắt buộc (plan I5): **add nullable → backfill → NOT NULL + CHECK**.
M2a chỉ add cột nullable để migration không vỡ với 4 legacy campaigns đang có.
M2b sẽ backfill (`approval_status='auto_approved'`, `approval_tier='none'`,
`estimated_cost=COALESCE(max_discount*max_issuances, 0)`, `realized_cost=0`).
M2c sẽ ALTER NOT NULL + thêm CHECK + partial indexes.

Không bao gồm:
- `authorization_id` → add ở M11 (sau khi `tenant_authorizations` tạo ở M8,
  với `ON DELETE SET NULL` cho E3 FK purge safety).
- Các cột service-fee (`service_fee_*`) → add ở M9.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "c1d2e3f4a5b6"
down_revision: Union[str, Sequence[str], None] = "b1c2d3e4f5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Template linkage
    op.add_column(
        "campaigns",
        sa.Column(
            "template_id",
            sa.Integer(),
            sa.ForeignKey("campaign_templates.id", ondelete="RESTRICT"),
            nullable=True,
        ),
    )
    op.add_column(
        "campaigns",
        sa.Column("template_version_snapshot", sa.Integer(), nullable=True),
    )

    # Program form — tách khỏi CampaignSource, driver chính cho approval tier
    op.add_column(
        "campaigns",
        sa.Column("program_form", sa.String(length=32), nullable=True),
    )

    # Approval tier state machine
    op.add_column(
        "campaigns",
        sa.Column("approval_status", sa.String(length=30), nullable=True),
    )
    op.add_column(
        "campaigns",
        sa.Column("approval_tier", sa.String(length=30), nullable=True),
    )

    # Cost tracking — BIGINT vì estimated_cost có thể > 2.1 tỷ (percent × max_issuances)
    op.add_column(
        "campaigns",
        sa.Column("estimated_cost", sa.BigInteger(), nullable=True),
    )
    op.add_column(
        "campaigns",
        sa.Column("realized_cost", sa.BigInteger(), nullable=True),
    )

    # Ops timeline — ops_filing_started_at dùng để chặn revoke (C4)
    op.add_column(
        "campaigns",
        sa.Column(
            "ops_filing_started_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "campaigns",
        sa.Column(
            "post_report_due_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "campaigns",
        sa.Column(
            "post_report_submitted_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    # Audit — ai tạo / ai review
    op.add_column(
        "campaigns",
        sa.Column(
            "created_by_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "campaigns",
        sa.Column(
            "reviewed_by_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "campaigns",
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "campaigns",
        sa.Column("rejection_reason", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("campaigns", "rejection_reason")
    op.drop_column("campaigns", "reviewed_at")
    op.drop_column("campaigns", "reviewed_by_user_id")
    op.drop_column("campaigns", "created_by_user_id")
    op.drop_column("campaigns", "post_report_submitted_at")
    op.drop_column("campaigns", "post_report_due_at")
    op.drop_column("campaigns", "ops_filing_started_at")
    op.drop_column("campaigns", "realized_cost")
    op.drop_column("campaigns", "estimated_cost")
    op.drop_column("campaigns", "approval_tier")
    op.drop_column("campaigns", "approval_status")
    op.drop_column("campaigns", "program_form")
    op.drop_column("campaigns", "template_version_snapshot")
    op.drop_column("campaigns", "template_id")
