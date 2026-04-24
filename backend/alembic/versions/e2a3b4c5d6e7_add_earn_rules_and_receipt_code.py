"""add earn rules use_tiers, tier earn_multiplier, transaction receipt_code

Revision ID: e2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-04-24

Gộp Part B + Part C cùng 1 revision (3 target table khác nhau, không conflict).
"""

from alembic import op
import sqlalchemy as sa


revision = "e2a3b4c5d6e7"
down_revision = "e1f2a3b4c5d6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Part B.1 — point_rules.use_tiers
    op.add_column(
        "point_rules",
        sa.Column(
            "use_tiers",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )

    # Part B.2 — tiers.earn_multiplier + check constraint
    op.add_column(
        "tiers",
        sa.Column(
            "earn_multiplier",
            sa.Numeric(precision=3, scale=2),
            server_default=sa.text("1.00"),
            nullable=False,
        ),
    )
    op.create_check_constraint(
        "earn_multiplier_range",
        "tiers",
        "earn_multiplier >= 0.50 AND earn_multiplier <= 5.00",
    )

    # Part C — transactions.receipt_code + partial unique index
    op.add_column(
        "transactions",
        sa.Column("receipt_code", sa.String(length=50), nullable=True),
    )
    op.create_index(
        "ux_transactions_partner_receipt_code",
        "transactions",
        ["partner_id", "receipt_code"],
        unique=True,
        postgresql_where=sa.text("receipt_code IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "ux_transactions_partner_receipt_code", table_name="transactions"
    )
    op.drop_column("transactions", "receipt_code")

    op.drop_constraint(
        "earn_multiplier_range", "tiers", type_="check"
    )
    op.drop_column("tiers", "earn_multiplier")

    op.drop_column("point_rules", "use_tiers")
