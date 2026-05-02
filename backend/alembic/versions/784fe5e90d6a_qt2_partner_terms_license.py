"""qt2_partner_terms_license

Revision ID: 784fe5e90d6a
Revises: 7ab1e9299d05
Create Date: 2026-05-02 15:12:04.456531

Thêm 6 cột vào bảng partners:
  - business_license_url: URL ảnh giấy phép kinh doanh
  - terms_accepted_at: thời điểm đồng ý điều khoản
  - terms_version: phiên bản điều khoản đã ký
  - last_status_reason: lý do thay đổi trạng thái gần nhất
  - last_status_changed_by: admin thực hiện thay đổi
  - last_status_changed_at: thời điểm thay đổi trạng thái gần nhất
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '784fe5e90d6a'
down_revision: Union[str, Sequence[str], None] = '7ab1e9299d05'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("partners", sa.Column("business_license_url", sa.String(500), nullable=True))
    op.add_column("partners", sa.Column("terms_accepted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("partners", sa.Column("terms_version", sa.String(20), nullable=True))
    op.add_column("partners", sa.Column("last_status_reason", sa.String(500), nullable=True))
    op.add_column("partners", sa.Column(
        "last_status_changed_by", sa.Integer(),
        nullable=True
    ))
    op.add_column("partners", sa.Column("last_status_changed_at", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key(
        "fk_partners_last_status_changed_by_users",
        "partners", "users",
        ["last_status_changed_by"], ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_partners_last_status_changed_by_users", "partners", type_="foreignkey")
    op.drop_column("partners", "last_status_changed_at")
    op.drop_column("partners", "last_status_changed_by")
    op.drop_column("partners", "last_status_reason")
    op.drop_column("partners", "terms_version")
    op.drop_column("partners", "terms_accepted_at")
    op.drop_column("partners", "business_license_url")
