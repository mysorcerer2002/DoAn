"""add user check constraints and password_changed_at

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-04-13 06:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add check constraints + password_changed_at column."""
    op.create_check_constraint(
        "ck_users_valid_role",
        "users",
        "system_role IN ('regular', 'admin', 'super_admin')",
    )
    op.create_check_constraint(
        "ck_users_login_identifier",
        "users",
        "is_shadow = true OR email IS NOT NULL OR phone IS NOT NULL",
    )
    op.add_column(
        "users",
        sa.Column(
            "password_changed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Drop password_changed_at + check constraints."""
    op.drop_column("users", "password_changed_at")
    op.drop_constraint("ck_users_login_identifier", "users", type_="check")
    op.drop_constraint("ck_users_valid_role", "users", type_="check")
