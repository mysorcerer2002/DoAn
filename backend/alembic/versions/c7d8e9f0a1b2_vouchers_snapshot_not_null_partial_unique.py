"""vouchers — NOT NULL snapshot/source + rebuild partial unique index

Revision ID: c7d8e9f0a1b2
Revises: b6c7d8e9f0a1
Create Date: 2026-04-22 11:15:00.000000

M4c của plan voucher rebuild v2.2.

1. NOT NULL cho `discount_snapshot` + `issue_source` sau M4b backfill.
2. Drop + recreate `uq_vouchers_active_per_member_per_campaign` để exclude
   `cancelled` — voucher cancelled KHÔNG block claim mới cùng campaign
   (logic: khách được phát lại nếu voucher trước bị huỷ).

`issuance_id` giữ nullable — legacy rows NULL, service mới luôn set.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "c7d8e9f0a1b2"
down_revision: Union[str, Sequence[str], None] = "b6c7d8e9f0a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("vouchers", "discount_snapshot", nullable=False)
    op.alter_column("vouchers", "issue_source", nullable=False)

    # Rebuild partial unique index để exclude 'cancelled'
    op.drop_index(
        "uq_vouchers_active_per_member_per_campaign", table_name="vouchers"
    )
    op.create_index(
        "uq_vouchers_active_per_member_per_campaign",
        "vouchers",
        ["campaign_id", "membership_id"],
        unique=True,
        postgresql_where=sa.text(
            "status NOT IN ('used','expired','cancelled')"
        ),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_vouchers_active_per_member_per_campaign", table_name="vouchers"
    )
    op.create_index(
        "uq_vouchers_active_per_member_per_campaign",
        "vouchers",
        ["campaign_id", "membership_id"],
        unique=True,
        postgresql_where=sa.text("status NOT IN ('used','expired')"),
    )

    op.alter_column("vouchers", "issue_source", nullable=True)
    op.alter_column("vouchers", "discount_snapshot", nullable=True)
