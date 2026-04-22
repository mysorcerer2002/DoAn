"""backfill campaigns approval/cost fields for legacy rows

Revision ID: d2e3f4a5b6c7
Revises: c1d2e3f4a5b6
Create Date: 2026-04-22 09:45:00.000000

M2b của plan voucher rebuild v2.2 — backfill 4 legacy campaigns trước khi
M2c ALTER NOT NULL.

Rules backfill (plan section 6.1):
- `program_form='giam_gia'` — legacy chỉ có discount, không có bốc thăm/tặng kèm.
- `approval_status='auto_approved'` — legacy không qua flow duyệt mới, coi như
  tự duyệt (tương thích với `CAMPAIGN_AUTO_THRESHOLD=500k`).
- `approval_tier='none'` — dưới threshold notify, không cần nộp CT.
- `estimated_cost = COALESCE(max_discount, discount_value) * COALESCE(max_issuances, 0)`
  — best-effort ước lượng; legacy không có max_issuances (NULL) → estimated_cost=0.
- `realized_cost=0` — chưa có logic tính realized, sẽ update sau ở voucher redemption.
- `post_report_submitted_at`: với campaign đã kết thúc (`ends_at < NOW()`) → set
  NOW() (deemed filed, skip post-report job). Count hiện tại = 0 nên no-op,
  nhưng statement chạy an toàn cho future rerun.

Template linkage — M2c sẽ CHECK `source NOT IN ('signup','birthday') OR
template_id IS NOT NULL`. Nên M2b **bắt buộc** backfill template_id cho
legacy signup/birthday campaigns dựa theo mapping source → template code:
- source='signup'   → `system-welcome-5pct-10k`
- source='birthday' → `system-birthday-10pct-30k`

Manual legacy giữ NULL (CHECK cho phép).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "d2e3f4a5b6c7"
down_revision: Union[str, Sequence[str], None] = "c1d2e3f4a5b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE campaigns
               SET program_form     = COALESCE(program_form, 'giam_gia'),
                   approval_status  = COALESCE(approval_status, 'auto_approved'),
                   approval_tier    = COALESCE(approval_tier, 'none'),
                   estimated_cost   = COALESCE(
                       estimated_cost,
                       COALESCE(max_discount, discount_value)
                         * COALESCE(max_issuances, 0)
                   ),
                   realized_cost    = COALESCE(realized_cost, 0)
             WHERE program_form IS NULL
                OR approval_status IS NULL
                OR approval_tier IS NULL
                OR estimated_cost IS NULL
                OR realized_cost IS NULL;
            """
        )
    )

    # Backfill template_id cho legacy signup/birthday — bắt buộc cho M2c CHECK.
    # template_version_snapshot = template.version (hiện tại = 1).
    op.execute(
        sa.text(
            """
            UPDATE campaigns c
               SET template_id               = t.id,
                   template_version_snapshot = t.version
              FROM campaign_templates t
             WHERE c.template_id IS NULL
               AND (
                     (c.source = 'signup'   AND t.code = 'system-welcome-5pct-10k')
                  OR (c.source = 'birthday' AND t.code = 'system-birthday-10pct-30k')
                   );
            """
        )
    )

    # Deemed-filed cho campaigns đã kết thúc trước migration — skip post-report job.
    op.execute(
        sa.text(
            """
            UPDATE campaigns
               SET post_report_submitted_at = NOW()
             WHERE ends_at < NOW()
               AND post_report_submitted_at IS NULL;
            """
        )
    )


def downgrade() -> None:
    # Backfill không reversible deterministic — chỉ clear các cột M2a đã add
    # để M2a downgrade (drop_column) chạy sạch. Nếu muốn rollback chuẩn,
    # downgrade M2c → M2b → M2a tuần tự.
    op.execute(
        sa.text(
            """
            UPDATE campaigns
               SET program_form    = NULL,
                   approval_status = NULL,
                   approval_tier   = NULL,
                   estimated_cost  = NULL,
                   realized_cost   = NULL,
                   post_report_submitted_at = NULL
             WHERE TRUE;
            """
        )
    )
