"""voucher validate trigger — AFTER INSERT, check max_issuances backup

Revision ID: a2b3c4d5e6f7
Revises: f0a1b2c3d4e5
Create Date: 2026-04-22 12:40:00.000000

M13 của plan voucher rebuild v2.2. Trigger AFTER INSERT (per row) trên
`vouchers`: nếu voucher mới có status IN ('issued','used') VÀ
`campaigns.max_issuances IS NOT NULL` VÀ
`COUNT(vouchers WHERE campaign_id=NEW.campaign_id AND status IN
('issued','used')) > max_issuances`
→ RAISE EXCEPTION (ERRCODE check_violation).

**Non-mutating**: trigger không UPDATE `campaigns.issued_count` (cache đó
đang bị M7 thay bằng VIEW; phase 9 sẽ drop cột). Đây là **backup
defense**, source of truth là `pg_advisory_xact_lock('claim:'||campaign_id)`
ở service layer (phase 9).

Race guard: trigger chạy trong cùng transaction của INSERT. Ở READ COMMITTED,
nếu 2 concurrent session cùng insert voucher thứ N+1, mỗi session đếm
n_current trước khi session kia commit → cả 2 có thể pass trigger. Advisory
lock ở service layer là tuyến phòng thủ chính; trigger này chỉ bắt các
path không đi qua service (bulk SQL, admin grant, migration).

WHEN clause lọc `NEW.status IN ('issued','used')` để không phí check khi
insert cancelled/expired (không đóng góp vào count).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "a2b3c4d5e6f7"
down_revision: Union[str, Sequence[str], None] = "f0a1b2c3d4e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_CREATE_FUNCTION = """
CREATE OR REPLACE FUNCTION trg_vouchers_validate_max_issuances()
RETURNS TRIGGER AS $$
DECLARE
    v_max_issuances INT;
    v_current_count INT;
BEGIN
    SELECT max_issuances INTO v_max_issuances
    FROM campaigns
    WHERE id = NEW.campaign_id;

    IF v_max_issuances IS NULL THEN
        RETURN NULL;
    END IF;

    SELECT COUNT(*) INTO v_current_count
    FROM vouchers
    WHERE campaign_id = NEW.campaign_id
      AND status IN ('issued','used');

    IF v_current_count > v_max_issuances THEN
        RAISE EXCEPTION
            'voucher_over_capacity: campaign_id=% count=% max=%',
            NEW.campaign_id, v_current_count, v_max_issuances
            USING ERRCODE = 'check_violation';
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;
"""


_CREATE_TRIGGER = """
CREATE TRIGGER voucher_validate_max_issuances
AFTER INSERT ON vouchers
FOR EACH ROW
WHEN (NEW.status IN ('issued','used'))
EXECUTE FUNCTION trg_vouchers_validate_max_issuances();
"""


def upgrade() -> None:
    op.execute(sa.text(_CREATE_FUNCTION))
    op.execute(sa.text(_CREATE_TRIGGER))


def downgrade() -> None:
    op.execute(
        sa.text("DROP TRIGGER IF EXISTS voucher_validate_max_issuances ON vouchers;")
    )
    op.execute(
        sa.text(
            "DROP FUNCTION IF EXISTS trg_vouchers_validate_max_issuances();"
        )
    )
