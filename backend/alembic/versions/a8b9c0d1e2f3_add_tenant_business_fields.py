"""add tenant tax_code + website + business_hours

Revision ID: a8b9c0d1e2f3
Revises: f7a8b9c0d1e2
Create Date: 2026-04-20 10:00:00.000000

Bổ sung 3 cột nullable vào bảng `tenants` cho thông tin kinh doanh mở rộng:
- tax_code: mã số thuế
- website: URL website chính của shop
- business_hours: giờ mở cửa (free text)
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "a8b9c0d1e2f3"
down_revision: Union[str, Sequence[str], None] = "f7a8b9c0d1e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tenants",
        sa.Column("tax_code", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "tenants",
        sa.Column("website", sa.String(length=500), nullable=True),
    )
    op.add_column(
        "tenants",
        sa.Column("business_hours", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("tenants", "business_hours")
    op.drop_column("tenants", "website")
    op.drop_column("tenants", "tax_code")
