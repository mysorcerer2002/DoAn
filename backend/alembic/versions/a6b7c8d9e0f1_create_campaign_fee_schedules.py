"""create campaign_fee_schedules — bảng giá phí dịch vụ + seed 5 row

Revision ID: a6b7c8d9e0f1
Revises: a4b5c6d7e8f9
Create Date: 2026-04-22 13:10:00.000000

M10 của plan voucher rebuild v2.2 (section 4.3). v1 seed-only (admin CRUD
defer). Partial unique `(fee_type) WHERE is_active=TRUE` — chỉ 1 version
hiện hành / loại phí, đổi giá → bump version + deactivate version cũ.

Seed 5 row (plan line 371):
- so_ct_filing = 500.000 VND (Điều 17)
- dossier_preparation = 1.000.000 VND (chuẩn bị bộ hồ sơ)
- multi_province = 2.000.000 VND (Điều 19 phạm vi liên tỉnh)
- express = 500.000 VND (phí nhanh, gộp vào tổng)
- waiver = 0 (cho demo account / internal test)
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "a6b7c8d9e0f1"
down_revision: Union[str, Sequence[str], None] = "a4b5c6d7e8f9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "campaign_fee_schedules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("fee_type", sa.String(length=30), nullable=False),
        sa.Column(
            "trigger_rule",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("base_amount", sa.BigInteger(), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("TRUE"),
            nullable=False,
        ),
        sa.Column(
            "version",
            sa.Integer(),
            server_default=sa.text("1"),
            nullable=False,
        ),
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
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "fee_type IN ('so_ct_filing','dossier_preparation','multi_province',"
            "'express','waiver')",
            name="ck_campaign_fee_schedules_fee_type",
        ),
        sa.CheckConstraint(
            "base_amount >= 0",
            name="ck_campaign_fee_schedules_base_amount_nonneg",
        ),
        sa.CheckConstraint(
            "version > 0",
            name="ck_campaign_fee_schedules_version_positive",
        ),
        sa.UniqueConstraint(
            "fee_type", "version", name="uq_campaign_fee_schedules_type_version"
        ),
    )
    op.create_index(
        "ux_campaign_fee_schedules_active_per_type",
        "campaign_fee_schedules",
        ["fee_type"],
        unique=True,
        postgresql_where=sa.text("is_active = TRUE"),
    )

    # Seed 5 row bảng giá mặc định.
    op.execute(
        sa.text(
            """
            INSERT INTO campaign_fee_schedules
                (fee_type, trigger_rule, base_amount, is_active, version)
            VALUES
                ('so_ct_filing', '{}'::jsonb, 500000, TRUE, 1),
                ('dossier_preparation', '{}'::jsonb, 1000000, TRUE, 1),
                ('multi_province', '{}'::jsonb, 2000000, TRUE, 1),
                ('express', '{}'::jsonb, 500000, TRUE, 1),
                ('waiver', '{}'::jsonb, 0, TRUE, 1);
            """
        )
    )


def downgrade() -> None:
    op.drop_index(
        "ux_campaign_fee_schedules_active_per_type",
        table_name="campaign_fee_schedules",
    )
    op.drop_table("campaign_fee_schedules")
