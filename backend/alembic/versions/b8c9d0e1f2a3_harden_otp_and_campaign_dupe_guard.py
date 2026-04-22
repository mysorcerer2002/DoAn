"""Harden OTP + chặn duplicate campaign pending per template.

Phase 6 review fixes (C2 + C3):

- Thêm `verification_codes.context_hash` để bind OTP với payload cụ thể
  (vd: hash của enroll form). Verify fail nếu context mismatch → chặn
  tamper form giữa request-otp và sign.

- Partial unique index `campaigns (tenant_id, template_id)
  WHERE approval_status IN ('draft','pending_approval')` — chặn 2 sign
  request cùng template tạo 2 campaign pending song song. Bảo hiểm thêm
  cho race OTP đã fix ở verification_code_service (FOR UPDATE).

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-04-22
"""

import sqlalchemy as sa
from alembic import op


revision = "b8c9d0e1f2a3"
down_revision = "a7b8c9d0e1f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "verification_codes",
        sa.Column("context_hash", sa.String(length=64), nullable=True),
    )

    op.create_index(
        "uq_campaigns_tenant_template_active_pending",
        "campaigns",
        ["tenant_id", "template_id"],
        unique=True,
        postgresql_where=sa.text(
            "approval_status IN ('draft', 'pending_approval') "
            "AND template_id IS NOT NULL"
        ),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_campaigns_tenant_template_active_pending",
        table_name="campaigns",
    )
    op.drop_column("verification_codes", "context_hash")
