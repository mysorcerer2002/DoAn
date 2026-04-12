"""add unique partial index on email and phone

Revision ID: a1b2c3d4e5f6
Revises: 458af7bebbbe
Create Date: 2026-04-12 20:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "458af7bebbbe"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Thêm partial unique index cho email và phone (chỉ khi NOT NULL)."""
    op.create_index(
        "ix_users_email_unique",
        "users",
        ["email"],
        unique=True,
        postgresql_where="email IS NOT NULL",
    )
    op.create_index(
        "ix_users_phone_unique",
        "users",
        ["phone"],
        unique=True,
        postgresql_where="phone IS NOT NULL",
    )


def downgrade() -> None:
    """Xóa unique index."""
    op.drop_index("ix_users_phone_unique", table_name="users")
    op.drop_index("ix_users_email_unique", table_name="users")
