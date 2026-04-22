"""alter campaigns — thêm authorization_id + service_fee_total + service_fee_status

Revision ID: a7b8c9d0e1f2
Revises: a6b7c8d9e0f1
Create Date: 2026-04-22 13:15:00.000000

M11 của plan voucher rebuild v2.2 (section 4.4). Đóng liên kết giữa bảng
`campaigns` ↔ các bảng managed service mới:

- `authorization_id` FK → tenant_authorizations ON DELETE SET NULL
  (E3 edge case — xoá authorization không được kéo campaign đi theo).
- `service_fee_total` BIGINT ≥ 0 — cache tổng phí (VND, đã bao VAT) để
  list/detail campaign không cần join `campaign_service_fees` mỗi request.
- `service_fee_status` VARCHAR(30) CHECK IN
  ('none','estimated','invoiced','paid') — status rollup cho shop owner.

Default `service_fee_total=0` + `service_fee_status='none'` để backfill
an toàn các campaign cũ (chưa có phí dịch vụ — SERVICE_FEE_ENABLED ở đồ
án là False, legacy campaign vẫn render được).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "a7b8c9d0e1f2"
down_revision: Union[str, Sequence[str], None] = "a6b7c8d9e0f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "campaigns",
        sa.Column("authorization_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_campaigns_authorization_id",
        "campaigns",
        "tenant_authorizations",
        ["authorization_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.add_column(
        "campaigns",
        sa.Column(
            "service_fee_total",
            sa.BigInteger(),
            server_default=sa.text("0"),
            nullable=False,
        ),
    )
    op.add_column(
        "campaigns",
        sa.Column(
            "service_fee_status",
            sa.String(length=30),
            server_default=sa.text("'none'"),
            nullable=False,
        ),
    )
    op.create_check_constraint(
        "ck_campaigns_service_fee_total_nonneg",
        "campaigns",
        "service_fee_total >= 0",
    )
    op.create_check_constraint(
        "ck_campaigns_service_fee_status",
        "campaigns",
        "service_fee_status IN ('none','estimated','invoiced','paid')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_campaigns_service_fee_status", "campaigns", type_="check"
    )
    op.drop_constraint(
        "ck_campaigns_service_fee_total_nonneg", "campaigns", type_="check"
    )
    op.drop_column("campaigns", "service_fee_status")
    op.drop_column("campaigns", "service_fee_total")
    op.drop_constraint(
        "fk_campaigns_authorization_id", "campaigns", type_="foreignkey"
    )
    op.drop_column("campaigns", "authorization_id")
