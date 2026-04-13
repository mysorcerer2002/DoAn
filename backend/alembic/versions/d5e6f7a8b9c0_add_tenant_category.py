"""add tenant category field

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-04-13 09:00:00.000000

Thêm cột `category` vào bảng `tenants` với check constraint enum values.
Default 'other' cho các row hiện có.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "d5e6f7a8b9c0"
down_revision: Union[str, Sequence[str], None] = "c4d5e6f7a8b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tenants",
        sa.Column(
            "category",
            sa.String(length=20),
            server_default="other",
            nullable=False,
        ),
    )
    op.create_check_constraint(
        "ck_tenants_category_valid",
        "tenants",
        "category IN ('cafe', 'food', 'retail', 'beauty', 'other')",
    )
    op.create_index("ix_tenants_category", "tenants", ["category"])


def downgrade() -> None:
    op.drop_index("ix_tenants_category", table_name="tenants")
    op.drop_constraint("ck_tenants_category_valid", "tenants", type_="check")
    op.drop_column("tenants", "category")
