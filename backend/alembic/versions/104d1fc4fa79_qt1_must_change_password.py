"""qt1_must_change_password

Add must_change_password flag để buộc user dùng temp password phải đổi
mật khẩu trước khi truy cập tính năng khác.

Revision ID: 104d1fc4fa79
Revises: 6d84715a3902
Create Date: 2026-05-02 14:23:22.916653

"""

from alembic import op
import sqlalchemy as sa

revision = "104d1fc4fa79"
down_revision = "6d84715a3902"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "must_change_password",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "must_change_password")
