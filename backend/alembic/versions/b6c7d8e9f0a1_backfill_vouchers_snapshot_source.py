"""backfill vouchers discount_snapshot + issue_source for legacy rows

Revision ID: b6c7d8e9f0a1
Revises: a5b6c7d8e9f0
Create Date: 2026-04-22 11:00:00.000000

M4b của plan voucher rebuild v2.2.

Backfill rule (plan section 3.3 — 5 keys bắt buộc):
- `discount_snapshot` = `{discount_type, discount_value, max_discount,
   min_order, terms_hash}`.
- `terms_hash` = SHA-256 hex của `campaigns.terms` (NULL → hash rỗng string
  để giữ keys schema đồng nhất). Legacy voucher snapshot hash "at time of
  migration", không phải "at time of issue" — service layer M9+ phải hiểu
  legacy hash = current hash (không diff).
- `issue_source = 'legacy'` — enum value riêng để phân biệt voucher tạo
  trước khi có issuance tracking.
- `issuance_id` giữ NULL: legacy không thuộc lô nào. M4c sẽ giữ nullable
  cho issuance_id (không enforce NOT NULL — service mới luôn set).

Current state: 7 vouchers (6 issued + 1 used).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "b6c7d8e9f0a1"
down_revision: Union[str, Sequence[str], None] = "a5b6c7d8e9f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # pgcrypto cho hàm digest() — cần cho terms_hash SHA-256. Idempotent.
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS pgcrypto;"))

    op.execute(
        sa.text(
            """
            UPDATE vouchers v
               SET discount_snapshot = jsonb_build_object(
                       'discount_type',  c.discount_type,
                       'discount_value', c.discount_value,
                       'max_discount',   c.max_discount,
                       'min_order',      c.min_order,
                       'terms_hash',     encode(
                           digest(COALESCE(c.terms, ''), 'sha256'), 'hex')
                   ),
                   issue_source = COALESCE(v.issue_source, 'legacy')
              FROM campaigns c
             WHERE v.campaign_id = c.id
               AND (v.discount_snapshot IS NULL OR v.issue_source IS NULL);
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE vouchers
               SET discount_snapshot = NULL,
                   issue_source = NULL
             WHERE issue_source = 'legacy';
            """
        )
    )
