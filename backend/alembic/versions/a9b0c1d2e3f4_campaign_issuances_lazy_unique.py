"""campaign_issuances — partial unique cho lazy-create ON CONFLICT

Revision ID: a9b0c1d2e3f4
Revises: b8c9d0e1f2a3
Create Date: 2026-04-22 14:00:00.000000

Phase 9 voucher rebuild v2.2 — VoucherService.claim lazy-create
`campaign_issuances` row bằng ON CONFLICT DO UPDATE RETURNING id.
ON CONFLICT target cần unique index. Lazy row phân biệt với batch
shop tự đặt tên qua `name IS NULL`:

- Shop owner tạo batch thủ công: `name` có giá trị ("Batch ra mắt",
  "Tặng VIP đầu tháng",…) → không match partial unique → không đụng.
- Auto-batch từ claim()/signup_job/birthday_job: `name IS NULL` →
  match partial unique → ON CONFLICT reuse row có sẵn.

Index: `(campaign_id, issue_mode) WHERE name IS NULL AND deleted_at IS NULL`.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "a9b0c1d2e3f4"
down_revision: Union[str, Sequence[str], None] = "b8c9d0e1f2a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "uq_campaign_issuances_lazy_auto",
        "campaign_issuances",
        ["campaign_id", "issue_mode"],
        unique=True,
        postgresql_where=sa.text("name IS NULL AND deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_campaign_issuances_lazy_auto", table_name="campaign_issuances"
    )
