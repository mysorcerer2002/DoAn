"""qt7_reward_free_voucher

Revision ID: 6c1c7e9c631b
Revises: 784fe5e90d6a
Create Date: 2026-05-02 15:39:41.713529

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6c1c7e9c631b'
down_revision: Union[str, Sequence[str], None] = '784fe5e90d6a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """QT7: relax points_cost >= 0, relax points_spent >= 0, add valid_from to rewards."""
    # rewards: drop old double-prefixed CK, add nonneg CK, add valid_from column
    op.drop_constraint("ck_rewards_ck_rewards_points_cost_positive", "rewards", type_="check")
    op.create_check_constraint("points_cost_nonneg", "rewards", "points_cost >= 0")
    op.add_column("rewards", sa.Column("valid_from", sa.Date(), nullable=True))

    # redemptions: drop old double-prefixed CK, add nonneg CK
    op.drop_constraint("ck_redemptions_ck_redemptions_points_positive", "redemptions", type_="check")
    op.create_check_constraint("points_spent_nonneg", "redemptions", "points_spent >= 0")


def downgrade() -> None:
    """Reverse QT7 changes."""
    op.drop_constraint("ck_redemptions_points_spent_nonneg", "redemptions", type_="check")
    op.create_check_constraint("points_positive", "redemptions", "points_spent > 0")

    op.drop_column("rewards", "valid_from")
    op.drop_constraint("ck_rewards_points_cost_nonneg", "rewards", type_="check")
    op.create_check_constraint("points_cost_positive", "rewards", "points_cost > 0")
