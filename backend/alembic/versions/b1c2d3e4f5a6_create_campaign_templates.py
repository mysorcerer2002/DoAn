"""create campaign_templates + seed system templates

Revision ID: b1c2d3e4f5a6
Revises: a8b9c0d1e2f3
Create Date: 2026-04-22 09:00:00.000000

M1 của plan voucher rebuild v2.2 — tạo bảng `campaign_templates` admin-managed
+ seed 3 template baseline (welcome, birthday, loyalty-fixed) để jobs signup/birthday
có thể enroll auto-approved không cần admin tạo thủ công.

CHECK constraints (Điều 96 Luật TM + NĐ 81/2018):
- discount_type='percent' → max_discount_percent_cap IS NOT NULL
  AND max_discount_percent_cap <= 50 AND max_discount_value_cap IS NOT NULL
- discount_type='fixed' → max_discount_fixed_cap IS NOT NULL
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, Sequence[str], None] = "a8b9c0d1e2f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "campaign_templates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=60), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=20), nullable=False),
        sa.Column("program_form", sa.String(length=32), nullable=False),
        sa.Column("discount_type", sa.String(length=20), nullable=False),
        sa.Column("default_usage_guide", sa.Text(), nullable=True),
        sa.Column("default_support_contact", sa.String(length=200), nullable=True),
        sa.Column("default_terms", sa.Text(), nullable=True),
        sa.Column("max_discount_percent_cap", sa.SmallInteger(), nullable=True),
        sa.Column("max_discount_value_cap", sa.Integer(), nullable=True),
        sa.Column("max_discount_fixed_cap", sa.Integer(), nullable=True),
        sa.Column("min_order_floor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_issuances_cap", sa.Integer(), nullable=True),
        sa.Column("max_duration_days", sa.SmallInteger(), nullable=True),
        sa.Column("min_voucher_ttl_days", sa.SmallInteger(), nullable=False, server_default="7"),
        sa.Column("max_voucher_ttl_days", sa.SmallInteger(), nullable=False, server_default="30"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
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
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("code", name="uq_campaign_templates_code"),
        sa.CheckConstraint(
            "source IN ('manual','birthday','signup')",
            name="ck_campaign_templates_source",
        ),
        sa.CheckConstraint(
            "program_form IN ('giam_gia','tang_kem','may_rui_quay_so',"
            "'may_rui_truc_tiep','khach_hang_thuong_xuyen')",
            name="ck_campaign_templates_program_form",
        ),
        sa.CheckConstraint(
            "discount_type IN ('percent','fixed')",
            name="ck_campaign_templates_discount_type",
        ),
        sa.CheckConstraint(
            "discount_type <> 'percent' OR ("
            "max_discount_percent_cap IS NOT NULL "
            "AND max_discount_percent_cap > 0 "
            "AND max_discount_percent_cap <= 50 "
            "AND max_discount_value_cap IS NOT NULL "
            "AND max_discount_value_cap > 0)",
            name="ck_campaign_templates_percent_caps_valid",
        ),
        sa.CheckConstraint(
            "discount_type <> 'fixed' OR ("
            "max_discount_fixed_cap IS NOT NULL AND max_discount_fixed_cap > 0)",
            name="ck_campaign_templates_fixed_caps_valid",
        ),
        sa.CheckConstraint(
            "max_issuances_cap IS NULL OR max_issuances_cap > 0",
            name="ck_campaign_templates_max_issuances_positive",
        ),
        sa.CheckConstraint(
            "min_voucher_ttl_days > 0 AND max_voucher_ttl_days >= min_voucher_ttl_days",
            name="ck_campaign_templates_voucher_ttl_range",
        ),
    )

    op.create_index(
        "ix_campaign_templates_source",
        "campaign_templates",
        ["source"],
        unique=False,
    )
    op.create_index(
        "ix_campaign_templates_active",
        "campaign_templates",
        ["is_active"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # Seed 3 template baseline để signup/birthday jobs dùng ngay
    op.execute(
        sa.text(
            """
            INSERT INTO campaign_templates
              (code, name, description, source, program_form, discount_type,
               default_usage_guide, default_terms,
               max_discount_percent_cap, max_discount_value_cap,
               max_discount_fixed_cap, min_order_floor, max_issuances_cap,
               max_duration_days, min_voucher_ttl_days, max_voucher_ttl_days,
               version, is_active)
            VALUES
              ('system-welcome-5pct-10k',
               'Voucher chào mừng thành viên mới',
               'Template hệ thống — phát tự động cho khách đăng ký thành viên lần đầu.',
               'signup', 'giam_gia', 'percent',
               'Áp dụng cho đơn hàng đầu tiên tại cửa hàng. Xuất trình voucher khi thanh toán.',
               'Mỗi khách hàng 01 voucher duy nhất. Không áp dụng kèm khuyến mãi khác.',
               5, 10000, NULL, 0, 200, 90, 7, 30, 1, TRUE),

              ('system-birthday-10pct-30k',
               'Voucher sinh nhật thành viên',
               'Template hệ thống — phát tự động vào ngày sinh nhật thành viên.',
               'birthday', 'giam_gia', 'percent',
               'Quà tặng sinh nhật — dùng 01 lần trong tháng sinh nhật.',
               'Mỗi thành viên 01 voucher/năm. Không cộng dồn với voucher khác.',
               10, 30000, NULL, 0, NULL, 30, 7, 30, 1, TRUE),

              ('system-loyalty-fixed-10k',
               'Voucher giảm 10k đơn từ 100k',
               'Template hệ thống — shop phát thủ công cho khách thân thiết.',
               'manual', 'giam_gia', 'fixed',
               'Xuất trình voucher khi thanh toán, đơn tối thiểu 100.000đ.',
               'Không áp dụng cho đơn đã giảm giá. Không hoàn tiền.',
               NULL, NULL, 10000, 100000, 100, 60, 7, 60, 1, TRUE);
            """
        )
    )


def downgrade() -> None:
    op.drop_index("ix_campaign_templates_active", table_name="campaign_templates")
    op.drop_index("ix_campaign_templates_source", table_name="campaign_templates")
    op.drop_table("campaign_templates")
