"""create campaign_service_fees — phí dịch vụ công ty ops thu shop

Revision ID: a4b5c6d7e8f9
Revises: a3b4c5d6e7f8
Create Date: 2026-04-22 13:05:00.000000

M9 của plan voucher rebuild v2.2 (section 4.2). VAT `vat_amount` và
`total_with_vat` là GENERATED STORED — DB tự tính, app không write được
(an toàn số liệu kế toán).

Partial unique `(campaign_id, fee_type) WHERE status NOT IN
('waived','refunded')` — chặn double-charge cùng loại phí cho cùng
campaign còn active.

E1 refund flow (status `refund_requested` → `refunded`) xử lý ở service
layer (phase 7/8 — reject campaign cascade).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "a4b5c6d7e8f9"
down_revision: Union[str, Sequence[str], None] = "a3b4c5d6e7f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "campaign_service_fees",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("fee_type", sa.String(length=30), nullable=False),
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.Column(
            "vat_rate",
            sa.Numeric(precision=4, scale=2),
            server_default=sa.text("10.00"),
            nullable=False,
        ),
        sa.Column(
            "vat_amount",
            sa.BigInteger(),
            sa.Computed("(amount * vat_rate / 100)::BIGINT", persisted=True),
            nullable=False,
        ),
        sa.Column(
            "total_with_vat",
            sa.BigInteger(),
            sa.Computed(
                "(amount + (amount * vat_rate / 100)::BIGINT)::BIGINT",
                persisted=True,
            ),
            nullable=False,
        ),
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("invoiced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("invoice_reference", sa.String(length=120), nullable=True),
        sa.Column(
            "e_invoice_provider",
            sa.String(length=20),
            server_default=sa.text("'manual'"),
            nullable=False,
        ),
        sa.Column(
            "e_invoice_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("refund_requested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("refunded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("refund_reason", sa.String(length=500), nullable=True),
        sa.Column("retention_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["campaign_id"], ["campaigns.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"], ["users.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "fee_type IN ('so_ct_filing','dossier_preparation','multi_province',"
            "'express','waiver')",
            name="ck_campaign_service_fees_fee_type",
        ),
        sa.CheckConstraint(
            "status IN ('draft','invoiced','paid','waived',"
            "'refund_requested','refunded')",
            name="ck_campaign_service_fees_status",
        ),
        sa.CheckConstraint(
            "e_invoice_provider IN ('manual','vnpt','viettel','misa')",
            name="ck_campaign_service_fees_e_invoice_provider",
        ),
        sa.CheckConstraint(
            "amount >= 0",
            name="ck_campaign_service_fees_amount_nonneg",
        ),
        sa.CheckConstraint(
            "vat_rate >= 0 AND vat_rate <= 99.99",
            name="ck_campaign_service_fees_vat_rate_range",
        ),
        sa.CheckConstraint(
            "retention_until >= created_at + INTERVAL '10 years'",
            name="ck_campaign_service_fees_retention_10y",
        ),
    )
    op.create_index(
        "ux_campaign_service_fees_active_per_type",
        "campaign_service_fees",
        ["campaign_id", "fee_type"],
        unique=True,
        postgresql_where=sa.text("status NOT IN ('waived','refunded')"),
    )
    op.create_index(
        "ix_campaign_service_fees_tenant_status",
        "campaign_service_fees",
        ["tenant_id", "status"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_campaign_service_fees_tenant_status",
        table_name="campaign_service_fees",
    )
    op.drop_index(
        "ux_campaign_service_fees_active_per_type",
        table_name="campaign_service_fees",
    )
    op.drop_table("campaign_service_fees")
