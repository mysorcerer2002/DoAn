"""create tenant_authorizations — giấy uỷ quyền điện tử shop → ops

Revision ID: a3b4c5d6e7f8
Revises: a2b3c4d5e6f7
Create Date: 2026-04-22 13:00:00.000000

M8 của plan voucher rebuild v2.2 (section 4.1). v1 scope `per_campaign`
only; `click_to_sign` (dev/demo) và `otp_email` (prod) là 2 method duy
nhất. `signature_payload` JSONB lưu dấu vết pháp lý đầy đủ (I2 plan).

Partial unique `(tenant_id, campaign_id) WHERE scope='per_campaign' AND
revoked_at IS NULL` — đảm bảo 1 shop chỉ có 1 uỷ quyền active cho 1
campaign tại 1 thời điểm.

Retention 10 năm (Luật Kế toán Điều 41) — hard delete chỉ sau
`retention_until = signed_at + 10 năm`.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "a3b4c5d6e7f8"
down_revision: Union[str, Sequence[str], None] = "a2b3c4d5e6f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tenant_authorizations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("scope", sa.String(length=30), nullable=False),
        sa.Column("campaign_id", sa.Integer(), nullable=True),
        sa.Column("document_content_hash", sa.String(length=64), nullable=False),
        sa.Column("document_url", sa.String(length=500), nullable=True),
        sa.Column("signed_by_user_id", sa.Integer(), nullable=False),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("signature_method", sa.String(length=30), nullable=False),
        sa.Column(
            "signature_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_reason", sa.Text(), nullable=True),
        sa.Column("retention_until", sa.DateTime(timezone=True), nullable=False),
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
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["campaign_id"], ["campaigns.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["signed_by_user_id"], ["users.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "scope IN ('per_campaign')",
            name="ck_tenant_authorizations_scope",
        ),
        sa.CheckConstraint(
            "signature_method IN ('click_to_sign','otp_email')",
            name="ck_tenant_authorizations_signature_method",
        ),
        sa.CheckConstraint(
            "scope <> 'per_campaign' OR campaign_id IS NOT NULL",
            name="ck_tenant_authorizations_per_campaign_requires_campaign",
        ),
        sa.CheckConstraint(
            "valid_until > valid_from",
            name="ck_tenant_authorizations_valid_window",
        ),
        sa.CheckConstraint(
            "retention_until >= signed_at + INTERVAL '10 years'",
            name="ck_tenant_authorizations_retention_10y",
        ),
    )
    op.create_index(
        "ux_tenant_authorizations_active_per_campaign",
        "tenant_authorizations",
        ["tenant_id", "campaign_id"],
        unique=True,
        postgresql_where=sa.text(
            "scope = 'per_campaign' AND revoked_at IS NULL"
        ),
    )


def downgrade() -> None:
    op.drop_index(
        "ux_tenant_authorizations_active_per_campaign",
        table_name="tenant_authorizations",
    )
    op.drop_table("tenant_authorizations")
