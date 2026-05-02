"""qt3_earn_percent

Đổi công thức tích điểm sang phần trăm: bỏ points_per_unit + unit_amount +
min_amount, thêm earn_percent (Numeric(5,2) NOT NULL DEFAULT 1.00). Đối tác
cũ tự đổi giá trị qua trang cấu hình; default 1% = chuẩn loyalty industry.

Revision ID: 6d84715a3902
Revises: da40dd6ff174
Create Date: 2026-05-02 13:42:34.109143
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6d84715a3902'
down_revision: Union[str, Sequence[str], None] = 'da40dd6ff174'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'point_rules',
        sa.Column(
            'earn_percent',
            sa.Numeric(5, 2),
            nullable=False,
            server_default=sa.text('1.00'),
        ),
    )
    op.drop_column('point_rules', 'points_per_unit')
    op.drop_column('point_rules', 'unit_amount')
    op.drop_column('point_rules', 'min_amount')


def downgrade() -> None:
    op.add_column(
        'point_rules',
        sa.Column('points_per_unit', sa.Numeric(10, 2), nullable=False, server_default='1'),
    )
    op.add_column(
        'point_rules',
        sa.Column('unit_amount', sa.Integer(), nullable=False, server_default='1000'),
    )
    op.add_column(
        'point_rules',
        sa.Column('min_amount', sa.Integer(), nullable=False, server_default='0'),
    )
    op.drop_column('point_rules', 'earn_percent')
