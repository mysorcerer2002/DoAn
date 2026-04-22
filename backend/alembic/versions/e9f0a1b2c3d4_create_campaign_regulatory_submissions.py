"""create campaign_regulatory_submissions — hồ sơ Sở CT (NĐ 81/2018)

Revision ID: e9f0a1b2c3d4
Revises: d8e9f0a1b2c3
Create Date: 2026-04-22 12:30:00.000000

M5 của plan voucher rebuild v2.2. Ops staff upload các loại hồ sơ nghiệp
vụ khuyến mãi: notify_so_ct (Điều 17), dang_ky_so_ct (Điều 19), dieu_le,
du_toan, xac_nhan_so_ct, bao_cao_ket_thuc.

`xac_nhan_so_ct` tồn tại → admin mới được `approve` campaign
(approve guard ở phase 8).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "e9f0a1b2c3d4"
down_revision: Union[str, Sequence[str], None] = "d8e9f0a1b2c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "campaign_regulatory_submissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("doc_type", sa.String(length=30), nullable=False),
        sa.Column("reference_no", sa.String(length=120), nullable=True),
        sa.Column("url", sa.String(length=500), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("submitted_by_user_id", sa.Integer(), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["submitted_by_user_id"], ["users.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "doc_type IN ('notify_so_ct','dang_ky_so_ct','dieu_le','du_toan',"
            "'xac_nhan_so_ct','bao_cao_ket_thuc')",
            name="ck_campaign_regulatory_submissions_doc_type",
        ),
    )
    op.create_index(
        "ix_campaign_regulatory_submissions_campaign",
        "campaign_regulatory_submissions",
        ["campaign_id", "doc_type"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_campaign_regulatory_submissions_campaign",
        table_name="campaign_regulatory_submissions",
    )
    op.drop_table("campaign_regulatory_submissions")
