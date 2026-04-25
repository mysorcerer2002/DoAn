"""Phase 1 cleanup MVP — drop verification_codes + is_shadow + password_changed_at

Revision ID: f1a2b3c4d5e6
Revises: f8a9b0c1d2e3
Create Date: 2026-04-25

Mục đích (theo spec docs/superpowers/specs/cleanup-mvp-2026-04-25.md §M1):
- DROP TABLE verification_codes (CASCADE).
- DROP COLUMN users.is_shadow.
- DROP COLUMN users.password_changed_at.
- DROP CHECK ck_users_ck_users_login_identifier (đề cập is_shadow nên phải drop trước column).

Trade-off: bỏ password_changed_at đồng nghĩa JWT đã cấp trước khi đổi mật khẩu
vẫn hợp lệ tới hết TTL (60 phút mặc định). MVP đồ án chấp nhận.
"""
from alembic import op
import sqlalchemy as sa


revision = "f1a2b3c4d5e6"
down_revision = "f8a9b0c1d2e3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop check constraint trước vì nó reference is_shadow.
    # Dùng raw SQL — naming convention auto-prefix sẽ làm lệch tên thật.
    op.execute(
        'ALTER TABLE users DROP CONSTRAINT IF EXISTS ck_users_ck_users_login_identifier'
    )

    # Drop columns trên users.
    op.drop_column("users", "is_shadow")
    op.drop_column("users", "password_changed_at")

    # Drop bảng verification_codes (CASCADE để không vướng FK nếu sót).
    op.execute("DROP TABLE IF EXISTS verification_codes CASCADE")


def downgrade() -> None:
    raise NotImplementedError(
        "Phase 1 cleanup MVP là one-way; không hỗ trợ downgrade."
    )
