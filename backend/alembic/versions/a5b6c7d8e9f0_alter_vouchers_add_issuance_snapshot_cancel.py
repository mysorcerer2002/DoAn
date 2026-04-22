"""alter vouchers — add issuance_id, discount_snapshot, cancel fields (nullable)

Revision ID: a5b6c7d8e9f0
Revises: f4a5b6c7d8e9
Create Date: 2026-04-22 10:45:00.000000

M4a của plan voucher rebuild v2.2 — mở rộng `vouchers` để:
1. Trace về lô phát (`issuance_id`, `issued_by_user_id`, `issue_source`).
2. Snapshot rule discount tại thời điểm phát (`discount_snapshot` JSONB)
   để campaign sửa sau không ảnh hưởng voucher cũ.
3. Support trạng thái `cancelled` (E2 spec — cancel với lý do, log-only
   notification theo user decision 2026-04-22).

Bổ sung CHECK `status IN (...)` bao trùm cả `cancelled` vì hiện tại schema
chưa enforce enum ở DB. `uq_vouchers_active_per_member_per_campaign` partial
index sẽ update ở M4c để exclude thêm `cancelled`.

Pattern tuần tự:
- M4a (file này) : add nullable + CHECK status.
- M4b            : backfill discount_snapshot + issue_source='legacy'.
- M4c            : NOT NULL discount_snapshot + issue_source + update partial unique.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "a5b6c7d8e9f0"
down_revision: Union[str, Sequence[str], None] = "f4a5b6c7d8e9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "vouchers",
        sa.Column(
            "issuance_id",
            sa.Integer(),
            sa.ForeignKey("campaign_issuances.id", ondelete="RESTRICT"),
            nullable=True,
        ),
    )
    op.add_column(
        "vouchers",
        sa.Column(
            "issued_by_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "vouchers",
        sa.Column("issue_source", sa.String(length=30), nullable=True),
    )
    op.add_column(
        "vouchers",
        sa.Column(
            "discount_snapshot",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.add_column(
        "vouchers",
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "vouchers",
        sa.Column("cancelled_reason", sa.Text(), nullable=True),
    )

    op.create_check_constraint(
        "ck_vouchers_status",
        "vouchers",
        "status IN ('issued','used','expired','cancelled')",
    )
    # cancelled → phải có cancelled_at + reason
    op.create_check_constraint(
        "ck_vouchers_cancelled_needs_meta",
        "vouchers",
        "status <> 'cancelled' OR ("
        "cancelled_at IS NOT NULL AND cancelled_reason IS NOT NULL)",
    )
    # PG CHECK với NULL trả UNKNOWN → pass. Không cần `IS NULL OR` prefix
    # (M4c sẽ NOT NULL sau khi backfill ở M4b).
    op.create_check_constraint(
        "ck_vouchers_issue_source",
        "vouchers",
        "issue_source IN ("
        "'legacy','manual','bulk_distribution','signup_job','birthday_job')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_vouchers_issue_source", "vouchers", type_="check")
    op.drop_constraint("ck_vouchers_cancelled_needs_meta", "vouchers", type_="check")
    op.drop_constraint("ck_vouchers_status", "vouchers", type_="check")

    op.drop_column("vouchers", "cancelled_reason")
    op.drop_column("vouchers", "cancelled_at")
    op.drop_column("vouchers", "discount_snapshot")
    op.drop_column("vouchers", "issue_source")
    op.drop_column("vouchers", "issued_by_user_id")
    op.drop_column("vouchers", "issuance_id")
