"""add partner banner_url

Revision ID: f8a9b0c1d2e3
Revises: e2a3b4c5d6e7
Create Date: 2026-04-25 12:00:00.000000

Thêm cột nullable `banner_url` vào bảng `partners` để partner có ảnh bìa
hiển thị ở header trang chi tiết (UX tham khảo Zalo loyalty).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "f8a9b0c1d2e3"
down_revision: Union[str, Sequence[str], None] = "e2a3b4c5d6e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "partners",
        sa.Column("banner_url", sa.String(length=500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("partners", "banner_url")
