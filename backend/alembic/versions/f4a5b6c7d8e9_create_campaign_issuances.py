"""create campaign_issuances — lô phát voucher của campaign

Revision ID: f4a5b6c7d8e9
Revises: e3f4a5b6c7d8
Create Date: 2026-04-22 10:30:00.000000

M3 của plan voucher rebuild v2.2 — tạo bảng `campaign_issuances` để tách
voucher thành các **lô phát** (batch). Một campaign có thể có nhiều lô:
- Lô auto-job (signup/birthday) chạy hằng ngày.
- Lô manual shop phát cho VIP trước khi mở public.
- Lô bulk distribution shop chủ động tạo.

Benefits:
- Trace lô nào phát voucher nào (audit + reconcile).
- Override `voucher_ttl_days` per-batch (không đụng campaign).
- Counter `issued_count` per-batch — giới hạn từng lô độc lập với
  `campaigns.max_issuances` (nhưng SUM(issued_count) ≤ campaigns.max_issuances
  enforced ở service layer).

`issue_mode`:
- `manual`             — staff/owner phát tay
- `bulk_distribution`  — shop import CSV/generate bulk
- `signup_job`         — APScheduler signup job
- `birthday_job`       — APScheduler birthday job
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "f4a5b6c7d8e9"
down_revision: Union[str, Sequence[str], None] = "e3f4a5b6c7d8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "campaign_issuances",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "tenant_id",
            sa.Integer(),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "campaign_id",
            sa.Integer(),
            sa.ForeignKey("campaigns.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=200), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=True),
        sa.Column(
            "issued_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("issue_mode", sa.String(length=30), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("voucher_ttl_days", sa.SmallInteger(), nullable=True),
        sa.Column(
            "created_by_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "issued_count >= 0",
            name="ck_campaign_issuances_issued_count_nonneg",
        ),
        sa.CheckConstraint(
            "quantity IS NULL OR quantity > 0",
            name="ck_campaign_issuances_quantity_positive",
        ),
        sa.CheckConstraint(
            "quantity IS NULL OR issued_count <= quantity",
            name="ck_campaign_issuances_issued_within_quantity",
        ),
        sa.CheckConstraint(
            "starts_at IS NULL OR ends_at IS NULL OR ends_at > starts_at",
            name="ck_campaign_issuances_ends_after_starts",
        ),
        sa.CheckConstraint(
            "voucher_ttl_days IS NULL OR voucher_ttl_days > 0",
            name="ck_campaign_issuances_voucher_ttl_positive",
        ),
        sa.CheckConstraint(
            "issue_mode IN ('manual','bulk_distribution','signup_job','birthday_job')",
            name="ck_campaign_issuances_issue_mode",
        ),
    )

    op.create_index(
        "ix_campaign_issuances_campaign",
        "campaign_issuances",
        ["campaign_id"],
    )
    op.create_index(
        "ix_campaign_issuances_tenant_active",
        "campaign_issuances",
        ["tenant_id", "created_at"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "ix_campaign_issuances_tenant_active", table_name="campaign_issuances"
    )
    op.drop_index("ix_campaign_issuances_campaign", table_name="campaign_issuances")
    op.drop_table("campaign_issuances")
