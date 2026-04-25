"""drop campaign + voucher system (Phase 2 MVP cleanup)

Revision ID: c5d6e7f8a9b0
Revises: f1a2b3c4d5e6
Create Date: 2026-04-26 00:00:00.000000

Phase 2 cleanup theo spec docs/superpowers/specs/cleanup-mvp-2026-04-25.md:
xoá toàn bộ campaign + voucher + bảng phụ thuộc + cột voucher trên transactions.
Reward + redemption giữ nguyên (đó mới là wallet thực sự của MVP).
"""

from alembic import op


revision = "c5d6e7f8a9b0"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Drop materialized/regular view depending on campaigns + vouchers.
    op.execute("DROP VIEW IF EXISTS v_campaign_stats CASCADE")

    # 2. Drop tables theo đúng thứ tự FK (con trước, cha sau).
    op.execute("DROP TABLE IF EXISTS campaign_approval_events CASCADE")
    op.execute("DROP TABLE IF EXISTS campaign_regulatory_submissions CASCADE")
    op.execute("DROP TABLE IF EXISTS campaign_issuances CASCADE")
    op.execute("DROP TABLE IF EXISTS vouchers CASCADE")
    op.execute("DROP TABLE IF EXISTS campaigns CASCADE")
    op.execute("DROP TABLE IF EXISTS campaign_templates CASCADE")
    # partner_authorizations chỉ tồn tại để thoả compliance phát hành campaign.
    # Khi campaign biến mất, authorization mất luôn ý nghĩa → drop kèm Phase 2.
    op.execute("DROP TABLE IF EXISTS partner_authorization_documents CASCADE")
    op.execute("DROP TABLE IF EXISTS partner_authorizations CASCADE")

    # 3. Drop voucher-related columns trên transactions.
    # legal_discount_ratio là generated column phụ thuộc voucher_discount_amount → drop trước.
    op.execute("ALTER TABLE transactions DROP COLUMN IF EXISTS legal_discount_ratio")
    op.execute("ALTER TABLE transactions DROP COLUMN IF EXISTS voucher_id")
    op.execute("ALTER TABLE transactions DROP COLUMN IF EXISTS voucher_discount_amount")

    # 4. Prune key cũ khỏi partners.settings (json type) để Pydantic extra="forbid" không vỡ.
    op.execute(
        "UPDATE partners "
        "SET settings = (settings::jsonb - 'voucher_default_ttl_days' - 'birthday_campaign_id')::json "
        "WHERE settings::jsonb ? 'voucher_default_ttl_days' "
        "   OR settings::jsonb ? 'birthday_campaign_id'"
    )


def downgrade() -> None:
    # Phase 2 là one-way cleanup cho MVP — không support rollback dữ liệu campaign/voucher.
    raise NotImplementedError(
        "Migration c5d6e7f8a9b0 (drop campaign + voucher) là one-way."
    )
