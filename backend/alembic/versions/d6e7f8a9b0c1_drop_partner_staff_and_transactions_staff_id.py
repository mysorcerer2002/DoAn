"""drop partner_staff + transactions.staff_id (Phase 3 MVP cleanup)

Revision ID: d6e7f8a9b0c1
Revises: c5d6e7f8a9b0
Create Date: 2026-04-26 12:00:00.000000

Phase 3 cleanup theo spec docs/superpowers/specs/cleanup-mvp-2026-04-25.md:
MVP final = mỗi shop chỉ có 1 owner (đã có partners.owner_user_id).
Bảng partner_staff không còn dùng → drop. Cột transactions.staff_id cũng
không còn nghĩa (mọi giao dịch đều do owner thao tác) → drop kèm.
"""

from alembic import op


revision = "d6e7f8a9b0c1"
down_revision = "c5d6e7f8a9b0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Drop FK transactions.staff_id → users.id rồi drop column.
    op.execute("ALTER TABLE transactions DROP COLUMN IF EXISTS staff_id")

    # 2. Drop bảng partner_staff (CASCADE để gỡ kèm index + FK).
    op.execute("DROP TABLE IF EXISTS partner_staff CASCADE")


def downgrade() -> None:
    raise NotImplementedError(
        "Migration d6e7f8a9b0c1 (drop partner_staff + transactions.staff_id) là one-way."
    )
