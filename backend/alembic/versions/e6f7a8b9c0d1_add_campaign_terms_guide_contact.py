"""add campaign terms + usage_guide + support_contact

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
Create Date: 2026-04-14 05:30:00.000000

Thêm 3 cột nullable vào bảng `campaigns` cho mô tả voucher chi tiết:
- terms: điều kiện áp dụng
- usage_guide: hướng dẫn sử dụng
- support_contact: liên hệ hỗ trợ (SĐT/email/link)
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "e6f7a8b9c0d1"
down_revision: Union[str, Sequence[str], None] = "d5e6f7a8b9c0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "campaigns",
        sa.Column("terms", sa.String(length=2000), nullable=True),
    )
    op.add_column(
        "campaigns",
        sa.Column("usage_guide", sa.String(length=2000), nullable=True),
    )
    op.add_column(
        "campaigns",
        sa.Column("support_contact", sa.String(length=500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("campaigns", "support_contact")
    op.drop_column("campaigns", "usage_guide")
    op.drop_column("campaigns", "terms")
