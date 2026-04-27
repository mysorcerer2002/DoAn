"""add reward min purchase amount

Revision ID: da40dd6ff174
Revises: e2f3a4b5c6d7
Create Date: 2026-04-27 16:20:45.541872

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'da40dd6ff174'
down_revision: Union[str, Sequence[str], None] = 'e2f3a4b5c6d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "rewards",
        sa.Column("min_purchase_amount", sa.Integer(), nullable=True),
    )
    op.create_check_constraint(
        "min_purchase_nonneg_or_null",
        "rewards",
        "min_purchase_amount IS NULL OR min_purchase_amount > 0",
    )
    op.create_check_constraint(
        "min_purchase_only_for_voucher",
        "rewards",
        "offer_type IN ('PERCENT_DISCOUNT','FIXED_DISCOUNT') OR min_purchase_amount IS NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "min_purchase_only_for_voucher", "rewards", type_="check"
    )
    op.drop_constraint(
        "min_purchase_nonneg_or_null", "rewards", type_="check"
    )
    op.drop_column("rewards", "min_purchase_amount")
