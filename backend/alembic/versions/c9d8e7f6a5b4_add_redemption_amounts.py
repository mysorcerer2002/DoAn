"""add original_amount + discount_amount cho redemptions

Revision ID: c9d8e7f6a5b4
Revises: 08639450a3cc
Create Date: 2026-04-27 10:30:00.000000

Lưu giá trị bill khi staff dùng voucher giảm giá để thống kê.
Cả 2 cột nullable vì voucher ITEM_GIFT không cần nhập bill.
"""

from alembic import op
import sqlalchemy as sa


revision = "c9d8e7f6a5b4"
down_revision = "08639450a3cc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "redemptions",
        sa.Column("original_amount", sa.Integer(), nullable=True),
    )
    op.add_column(
        "redemptions",
        sa.Column("discount_amount", sa.Integer(), nullable=True),
    )
    op.create_check_constraint(
        "amounts_nonneg_or_null",
        "redemptions",
        "(original_amount IS NULL AND discount_amount IS NULL) "
        "OR (original_amount >= 0 AND discount_amount >= 0)",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_redemptions_amounts_nonneg_or_null", "redemptions", type_="check"
    )
    op.drop_column("redemptions", "discount_amount")
    op.drop_column("redemptions", "original_amount")
