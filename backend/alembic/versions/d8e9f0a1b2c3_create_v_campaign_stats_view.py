"""create v_campaign_stats view — realtime issued/used/cancelled/realized

Revision ID: d8e9f0a1b2c3
Revises: c7d8e9f0a1b2
Create Date: 2026-04-22 12:00:00.000000

M7 của plan voucher rebuild v2.2 — Option B (reviewer pick): bỏ cache
`campaigns.issued_count`, dùng VIEW COUNT realtime tránh deadlock với
atomic UPDATE claim (E2).

View trả mỗi campaign 1 row:
- `issued_count`: voucher status IN ('issued','used') — số đã phát còn hiệu lực + đã dùng.
- `used_count`: voucher status='used'.
- `cancelled_count`: voucher status='cancelled' (E1 reject-cascade, C3).
- `realized_cost`: SUM(transactions.voucher_discount_amount) qua voucher_id join.

Phase 9 sẽ rewrite `VoucherService.claim` để đọc view + lock theo
pg_advisory_xact_lock thay vì atomic UPDATE `issued_count`. TRƯỚC khi
drop cột `campaigns.issued_count` (plan M7 ghi "drop cột nếu còn được
đọc ở code, migrate trước") — tạm giữ cột để code hiện tại không vỡ,
phase 9 mới drop.

Scope đồ án chấp nhận view LEFT JOIN vouchers + transactions không index
phụ (risk row ở section 10 plan). N10 defer materialized view.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "d8e9f0a1b2c3"
down_revision: Union[str, Sequence[str], None] = "c7d8e9f0a1b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            CREATE OR REPLACE VIEW v_campaign_stats AS
            SELECT
                c.id AS campaign_id,
                COUNT(v.id) FILTER (
                    WHERE v.status IN ('issued','used')
                ) AS issued_count,
                COUNT(v.id) FILTER (WHERE v.status = 'used') AS used_count,
                COUNT(v.id) FILTER (
                    WHERE v.status = 'cancelled'
                ) AS cancelled_count,
                COALESCE(
                    SUM(
                        CASE WHEN t.id IS NOT NULL
                             THEN t.voucher_discount_amount
                             ELSE 0
                        END
                    ),
                    0
                )::BIGINT AS realized_cost
            FROM campaigns c
            LEFT JOIN vouchers v ON v.campaign_id = c.id
            LEFT JOIN transactions t ON t.voucher_id = v.id
            GROUP BY c.id;
            """
        )
    )
    op.execute(
        sa.text(
            "COMMENT ON VIEW v_campaign_stats IS "
            "'Plan voucher rebuild v2.2 M7 — realtime stats; thay cột cache "
            "campaigns.issued_count. Phase 9 sẽ drop cột cache.';"
        )
    )


def downgrade() -> None:
    op.execute(sa.text("DROP VIEW IF EXISTS v_campaign_stats;"))
