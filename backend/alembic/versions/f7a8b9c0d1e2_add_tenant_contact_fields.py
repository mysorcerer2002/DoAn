"""add tenant contact_phone + contact_email + address

Revision ID: f7a8b9c0d1e2
Revises: e6f7a8b9c0d1
Create Date: 2026-04-14 06:40:00.000000

Thêm 3 cột nullable vào bảng `tenants` cho thông tin liên hệ shop:
- contact_phone: SĐT liên hệ shop
- contact_email: email liên hệ shop
- address: địa chỉ shop
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "f7a8b9c0d1e2"
down_revision: Union[str, Sequence[str], None] = "e6f7a8b9c0d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tenants",
        sa.Column("contact_phone", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "tenants",
        sa.Column("contact_email", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "tenants",
        sa.Column("address", sa.String(length=500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("tenants", "address")
    op.drop_column("tenants", "contact_email")
    op.drop_column("tenants", "contact_phone")
