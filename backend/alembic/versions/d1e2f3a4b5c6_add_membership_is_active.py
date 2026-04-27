"""add is_active flag cho memberships

Revision ID: d1e2f3a4b5c6
Revises: c9d8e7f6a5b4
Create Date: 2026-04-27 12:00:00.000000

Cờ khoá thành viên ở từng đối tác. Khi is_active=False, transaction_service
chặn tích điểm; staff vẫn xem được lịch sử của member trong UI.
"""

from alembic import op
import sqlalchemy as sa


revision = "d1e2f3a4b5c6"
down_revision = "c9d8e7f6a5b4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "memberships",
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )


def downgrade() -> None:
    op.drop_column("memberships", "is_active")
