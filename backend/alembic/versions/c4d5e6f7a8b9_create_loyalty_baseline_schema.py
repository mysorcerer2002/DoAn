"""create loyalty baseline schema (Section 2+3+4+5+6 tables)

Revision ID: c4d5e6f7a8b9
Revises: c3d4e5f6a7b8
Create Date: 2026-04-13 06:30:00.000000

Baseline migration: tạo tất cả bảng cho Section 2-6 (tenants, staff, members,
transactions, point_ledger, tiers, rules, vouchers, campaigns, notifications,
rewards, redemptions, tenant_settings_audit, verification_codes) cùng với
trigger append-only cho point_ledger.

Dùng `Base.metadata.create_all(bind, checkfirst=True)` cho upgrade — pattern
hợp lệ cho 1 baseline migration vì không thể practical viết tay 14 tables
mà giữ đồng bộ với SQLAlchemy models. `checkfirst=True` skip bảng `users`
đã tạo ở migrations trước.

Trigger `prevent_point_ledger_mutation` được tạo explicit qua op.execute để
đảm bảo append-only invariant tồn tại trong production (không chỉ ở test
fixture).
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c4d5e6f7a8b9"
down_revision: Union[str, Sequence[str], None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Tables tạo bởi migration này (theo thứ tự FK dependency).
# users đã có ở migration 458af7bebbbe → SKIP.
TABLES_TO_CREATE = [
    "tenants",
    "tenant_staff",
    "tenant_settings_audit",
    "verification_codes",
    "tiers",
    "point_rules",
    "memberships",
    "rewards",
    "redemptions",
    "campaigns",
    "vouchers",
    "transactions",
    "point_ledger",
    "notifications",
]


def upgrade() -> None:
    """Tạo các bảng Section 2-6 + trigger append-only cho point_ledger."""
    # Import models để register vào Base.metadata
    from app.models import (  # noqa: F401
        campaign,
        membership,
        notification,
        point_ledger,
        point_rule,
        redemption,
        reward,
        tenant,
        tenant_settings_audit,
        tenant_staff,
        tier,
        transaction,
        verification_code,
        voucher,
    )
    from app.models.base import Base

    bind = op.get_bind()
    # checkfirst=True → skip bảng `users` đã tạo ở migrations trước
    Base.metadata.create_all(bind, checkfirst=True)

    # Append-only trigger cho point_ledger — chống UPDATE/DELETE
    op.execute(
        """
        CREATE OR REPLACE FUNCTION prevent_point_ledger_mutation()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'point_ledger is append-only — UPDATE/DELETE not allowed';
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute("DROP TRIGGER IF EXISTS no_update_or_delete_point_ledger ON point_ledger;")
    op.execute(
        """
        CREATE TRIGGER no_update_or_delete_point_ledger
        BEFORE UPDATE OR DELETE ON point_ledger
        FOR EACH ROW EXECUTE FUNCTION prevent_point_ledger_mutation();
        """
    )


def downgrade() -> None:
    """Drop trigger + drop tables (giữ lại users)."""
    op.execute("DROP TRIGGER IF EXISTS no_update_or_delete_point_ledger ON point_ledger;")
    op.execute("DROP FUNCTION IF EXISTS prevent_point_ledger_mutation();")

    # Drop theo thứ tự ngược FK dependency
    for table_name in reversed(TABLES_TO_CREATE):
        op.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")
