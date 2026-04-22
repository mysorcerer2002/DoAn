"""campaigns approval/cost — NOT NULL + CHECK + partial indexes

Revision ID: e3f4a5b6c7d8
Revises: d2e3f4a5b6c7
Create Date: 2026-04-22 10:00:00.000000

M2c của plan voucher rebuild v2.2 — sau khi M2b backfill xong, khoá các
invariant quan trọng trên `campaigns`.

Enum values enforced bằng CHECK constraints (không dùng native PG enum —
repo convention giữ String + enum.Enum Python).

Partial indexes:
- `ix_campaigns_pending_approval` → admin queue "campaign chờ duyệt"
- `ix_campaigns_post_report_due`  → post-report 45-day overdue job
- `ix_campaigns_active_approved`  → FE list campaigns đang chạy

`template_id` giữ NULLABLE — CHECK enforce "signup/birthday thì bắt buộc
template_id" (legacy manual không có template_id, NULL OK). Service layer
(M9+) sẽ yêu cầu template_id ở mọi flow enroll mới.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "e3f4a5b6c7d8"
down_revision: Union[str, Sequence[str], None] = "d2e3f4a5b6c7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. NOT NULL cho các cột đã backfill
    op.alter_column("campaigns", "program_form", nullable=False)
    op.alter_column("campaigns", "approval_status", nullable=False)
    op.alter_column("campaigns", "approval_tier", nullable=False)
    op.alter_column("campaigns", "estimated_cost", nullable=False)
    op.alter_column(
        "campaigns",
        "realized_cost",
        nullable=False,
        server_default="0",
    )

    # 2. CHECK enum + domain invariants
    op.create_check_constraint(
        "ck_campaigns_program_form",
        "campaigns",
        "program_form IN ('giam_gia','tang_kem','may_rui_quay_so',"
        "'may_rui_truc_tiep','khach_hang_thuong_xuyen')",
    )
    op.create_check_constraint(
        "ck_campaigns_approval_status",
        "campaigns",
        "approval_status IN ('draft','pending_approval','auto_approved',"
        "'approved','rejected','revision_requested')",
    )
    op.create_check_constraint(
        "ck_campaigns_approval_tier",
        "campaigns",
        "approval_tier IN ('none','notify_so_ct','dang_ky_so_ct','full_dossier')",
    )
    op.create_check_constraint(
        "ck_campaigns_estimated_cost_nonneg",
        "campaigns",
        "estimated_cost >= 0",
    )
    op.create_check_constraint(
        "ck_campaigns_realized_cost_nonneg",
        "campaigns",
        "realized_cost >= 0",
    )
    # may_rui_* (bốc thăm) theo NĐ 81 Điều 19 luôn phải đăng ký Sở CT
    op.create_check_constraint(
        "ck_campaigns_may_rui_tier",
        "campaigns",
        "program_form NOT IN ('may_rui_quay_so','may_rui_truc_tiep') "
        "OR approval_tier IN ('dang_ky_so_ct','full_dossier')",
    )
    # Rejected phải có rejection_reason + reviewer
    op.create_check_constraint(
        "ck_campaigns_rejected_needs_reason",
        "campaigns",
        "approval_status <> 'rejected' OR ("
        "rejection_reason IS NOT NULL AND reviewed_at IS NOT NULL "
        "AND reviewed_by_user_id IS NOT NULL)",
    )
    # signup/birthday bắt buộc template_id; manual (legacy) có thể NULL
    op.create_check_constraint(
        "ck_campaigns_template_required_for_system_source",
        "campaigns",
        "source NOT IN ('signup','birthday') OR template_id IS NOT NULL",
    )

    # 3. Partial indexes
    op.create_index(
        "ix_campaigns_pending_approval",
        "campaigns",
        ["tenant_id", "created_at"],
        postgresql_where=sa.text(
            "approval_status = 'pending_approval' AND deleted_at IS NULL"
        ),
    )
    op.create_index(
        "ix_campaigns_post_report_due",
        "campaigns",
        ["post_report_due_at"],
        postgresql_where=sa.text(
            "post_report_submitted_at IS NULL "
            "AND approval_tier IN ('notify_so_ct','dang_ky_so_ct','full_dossier')"
        ),
    )
    op.create_index(
        "ix_campaigns_active_approved",
        "campaigns",
        ["tenant_id", "starts_at", "ends_at"],
        postgresql_where=sa.text(
            "approval_status IN ('auto_approved','approved') "
            "AND is_active = TRUE AND deleted_at IS NULL"
        ),
    )


def downgrade() -> None:
    op.drop_index("ix_campaigns_active_approved", table_name="campaigns")
    op.drop_index("ix_campaigns_post_report_due", table_name="campaigns")
    op.drop_index("ix_campaigns_pending_approval", table_name="campaigns")

    op.drop_constraint(
        "ck_campaigns_template_required_for_system_source",
        "campaigns",
        type_="check",
    )
    op.drop_constraint(
        "ck_campaigns_rejected_needs_reason", "campaigns", type_="check"
    )
    op.drop_constraint("ck_campaigns_may_rui_tier", "campaigns", type_="check")
    op.drop_constraint(
        "ck_campaigns_realized_cost_nonneg", "campaigns", type_="check"
    )
    op.drop_constraint(
        "ck_campaigns_estimated_cost_nonneg", "campaigns", type_="check"
    )
    op.drop_constraint("ck_campaigns_approval_tier", "campaigns", type_="check")
    op.drop_constraint("ck_campaigns_approval_status", "campaigns", type_="check")
    op.drop_constraint("ck_campaigns_program_form", "campaigns", type_="check")

    op.alter_column(
        "campaigns", "realized_cost", nullable=True, server_default=None
    )
    op.alter_column("campaigns", "estimated_cost", nullable=True)
    op.alter_column("campaigns", "approval_tier", nullable=True)
    op.alter_column("campaigns", "approval_status", nullable=True)
    op.alter_column("campaigns", "program_form", nullable=True)
