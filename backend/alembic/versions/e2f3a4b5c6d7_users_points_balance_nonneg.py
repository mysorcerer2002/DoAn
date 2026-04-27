"""thêm CHECK users.points_balance >= 0

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
Create Date: 2026-04-27 14:00:00.000000

Sau migration HYBRID f9a0b1c2d3e4 (ví điểm global), `users.points_balance`
backfill = SUM(point_ledger.delta). Nếu seed cũ set membership.points_balance
trực tiếp mà không có entry ledger tương ứng, backfill ra số âm. CHECK này
chốt cứng để tương lai mọi UPDATE (kể cả ad-hoc SQL) không thể đẩy balance
xuống dưới 0.
"""

from alembic import op


revision = "e2f3a4b5c6d7"
down_revision = "d1e2f3a4b5c6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Defensive: env nào còn dư âm (do seed cũ trước reseed) thì kéo về 0 để CHECK
    # apply được. No-op khi DB đã sạch.
    op.execute("UPDATE users SET points_balance = 0 WHERE points_balance < 0")
    op.create_check_constraint(
        "points_balance_nonneg",
        "users",
        "points_balance >= 0",
    )


def downgrade() -> None:
    op.drop_constraint("ck_users_points_balance_nonneg", "users", type_="check")
