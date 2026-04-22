"""alter transactions add legal_discount_ratio GENERATED

Revision ID: b0c1d2e3f4a5
Revises: a9b0c1d2e3f4
Create Date: 2026-04-22 13:40:00.000000

M12 của plan voucher rebuild v2.2 — Thêm cột `legal_discount_ratio`
(NUMERIC(5,2) GENERATED ALWAYS AS (voucher_discount_amount::NUMERIC /
NULLIF(gross_amount,0) * 100) STORED). NĐ 81 Điều 7 quy định mức giảm
giá tối đa 50% trừ đợt tập trung — column này để audit + warn service
layer (không CHECK cứng, đợt tập trung có thể vượt hợp lệ).

Acceptance #16: auto-compute khi INSERT/UPDATE transaction; service warn
khi > 50.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "b0c1d2e3f4a5"
down_revision: Union[str, Sequence[str], None] = "a9b0c1d2e3f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            ALTER TABLE transactions
            ADD COLUMN legal_discount_ratio NUMERIC(5,2)
            GENERATED ALWAYS AS (
                voucher_discount_amount::NUMERIC
                / NULLIF(gross_amount, 0) * 100
            ) STORED;
            """
        )
    )
    op.execute(
        sa.text(
            "COMMENT ON COLUMN transactions.legal_discount_ratio IS "
            "'Plan voucher rebuild v2.2 M12 — % giảm vs gross (NĐ 81 Đ7 ≤50%); "
            "GENERATED STORED, warn ở service khi >50 (không CHECK cứng vì "
            "đợt tập trung khuyến mại có thể vượt hợp lệ).';"
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text("ALTER TABLE transactions DROP COLUMN IF EXISTS legal_discount_ratio;")
    )
