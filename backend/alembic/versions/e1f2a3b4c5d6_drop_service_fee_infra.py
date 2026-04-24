"""drop service fee infrastructure

Revision ID: e1f2a3b4c5d6
Revises: 162e25afc796
Create Date: 2026-04-24

**One-way migration** — downgrade = pass (không restore schema).
Lý do: spec 2026-04-24-partner-earn-rules-and-transactions section 3.1.
- CI round-trip test `upgrade → downgrade → upgrade` không crash
- Production rollback = revert commit + redeploy (không dùng alembic downgrade trực tiếp)

Drop:
- 2 check constraints: ck_campaigns_service_fee_status, ck_campaigns_service_fee_total_nonneg
- 2 columns trên campaigns: service_fee_status, service_fee_total
- 2 indexes + table campaign_service_fees
- 1 index + table campaign_fee_schedules

GIỮ: authorization_id, fk_campaigns_authorization_id, partner_authorizations
(managed service model, không phải fee).
"""

from alembic import op
import sqlalchemy as sa


revision = "e1f2a3b4c5d6"
down_revision = "162e25afc796"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "ck_campaigns_service_fee_status", "campaigns", type_="check"
    )
    op.drop_constraint(
        "ck_campaigns_service_fee_total_nonneg", "campaigns", type_="check"
    )
    op.drop_column("campaigns", "service_fee_status")
    op.drop_column("campaigns", "service_fee_total")

    op.drop_index(
        "ix_campaign_service_fees_partner_status",
        table_name="campaign_service_fees",
    )
    op.drop_index(
        "ux_campaign_service_fees_active_per_type",
        table_name="campaign_service_fees",
    )
    op.drop_table("campaign_service_fees")

    op.drop_index(
        "ux_campaign_fee_schedules_active_per_type",
        table_name="campaign_fee_schedules",
    )
    op.drop_table("campaign_fee_schedules")


def downgrade() -> None:
    """One-way — không restore schema. Xem docstring module."""
    pass
