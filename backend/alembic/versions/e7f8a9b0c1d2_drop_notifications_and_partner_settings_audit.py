"""drop notifications + partner_settings_audit (Phase 4 MVP cleanup)

Revision ID: e7f8a9b0c1d2
Revises: d6e7f8a9b0c1
Create Date: 2026-04-26 13:00:00.000000

Phase 4 cleanup theo spec docs/superpowers/specs/cleanup-mvp-2026-04-25.md:
- notifications: chỉ phục vụ campaign/voucher (đã drop ở Phase 2) → bỏ kèm.
- partner_settings_audit: log thay đổi shop settings; MVP final 1 owner / shop
  không cần audit log → drop.
"""

from alembic import op


revision = "e7f8a9b0c1d2"
down_revision = "d6e7f8a9b0c1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP TABLE IF EXISTS notifications CASCADE")
    op.execute("DROP TABLE IF EXISTS partner_settings_audit CASCADE")


def downgrade() -> None:
    raise NotImplementedError(
        "Migration e7f8a9b0c1d2 (drop notifications + partner_settings_audit) là one-way."
    )
