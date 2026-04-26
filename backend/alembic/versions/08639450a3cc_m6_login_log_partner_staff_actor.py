"""m6_login_log_partner_staff_actor

Revision ID: 08639450a3cc
Revises: f9a0b1c2d3e4
Create Date: 2026-04-26 07:13:31.712111

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '08639450a3cc'
down_revision: Union[str, Sequence[str], None] = 'f9a0b1c2d3e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. login_log table
    op.create_table(
        "login_log",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("identifier", sa.String(255), nullable=False),
        sa.Column("ip", sa.String(45), nullable=False),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("success", sa.Boolean, nullable=False),
        sa.Column("failure_reason", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_login_log_failed_recent",
        "login_log",
        ["identifier", sa.text("created_at DESC")],
        postgresql_where=sa.text("success = false"),
    )
    op.create_index(
        "ix_login_log_user_created",
        "login_log",
        ["user_id", sa.text("created_at DESC")],
    )

    # 2. partner_staff table (chỉ chứa staff, không owner)
    op.create_table(
        "partner_staff",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("partner_id", sa.Integer, sa.ForeignKey("partners.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", name="uq_partner_staff_user"),
    )
    op.create_index("ix_partner_staff_partner", "partner_staff", ["partner_id"])

    # 3. point_ledger.actor_user_id — disable trigger để ALTER, sau đó re-enable
    op.execute("ALTER TABLE point_ledger DISABLE TRIGGER no_update_or_delete_point_ledger")
    op.add_column(
        "point_ledger",
        sa.Column(
            "actor_user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_point_ledger_actor_created",
        "point_ledger",
        ["actor_user_id", sa.text("created_at DESC")],
        postgresql_where=sa.text("actor_user_id IS NOT NULL"),
    )
    op.execute("ALTER TABLE point_ledger ENABLE TRIGGER no_update_or_delete_point_ledger")


def downgrade() -> None:
    op.execute("ALTER TABLE point_ledger DISABLE TRIGGER no_update_or_delete_point_ledger")
    op.drop_index("ix_point_ledger_actor_created", table_name="point_ledger")
    op.drop_column("point_ledger", "actor_user_id")
    op.execute("ALTER TABLE point_ledger ENABLE TRIGGER no_update_or_delete_point_ledger")

    op.drop_index("ix_partner_staff_partner", table_name="partner_staff")
    op.drop_table("partner_staff")

    op.drop_index("ix_login_log_user_created", table_name="login_log")
    op.drop_index("ix_login_log_failed_recent", table_name="login_log")
    op.drop_table("login_log")
