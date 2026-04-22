"""create campaign_approval_events — audit log duyệt campaign

Revision ID: f0a1b2c3d4e5
Revises: e9f0a1b2c3d4
Create Date: 2026-04-22 12:35:00.000000

M6 của plan voucher rebuild v2.2. Append-only: mỗi transition duyệt →
1 event. Phục vụ audit Sở CT và report nội bộ.

event_type: submitted | auto_approved | ops_started | approved | rejected |
revision_requested | cancelled_by_shop.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "f0a1b2c3d4e5"
down_revision: Union[str, Sequence[str], None] = "e9f0a1b2c3d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "campaign_approval_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=30), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["campaign_id"], ["campaigns.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id"], ["users.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "event_type IN ('submitted','auto_approved','ops_started','approved',"
            "'rejected','revision_requested','cancelled_by_shop')",
            name="ck_campaign_approval_events_event_type",
        ),
    )
    op.create_index(
        "ix_campaign_approval_events_campaign_at",
        "campaign_approval_events",
        ["campaign_id", "at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_campaign_approval_events_campaign_at",
        table_name="campaign_approval_events",
    )
    op.drop_table("campaign_approval_events")
