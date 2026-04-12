import enum

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class TransactionMethod(str, enum.Enum):
    MANUAL = "manual"
    QR_SHOP = "qr_shop"
    QR_CUSTOMER = "qr_customer"


class Transaction(Base, TimestampMixin):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("gross_amount >= 0", name="ck_transactions_gross_nonneg"),
        CheckConstraint("net_amount >= 0", name="ck_transactions_net_nonneg"),
        CheckConstraint(
            "net_amount <= gross_amount", name="ck_transactions_net_le_gross"
        ),
        CheckConstraint("points_earned >= 0", name="ck_transactions_points_nonneg"),
        Index("ix_transactions_tenant_created", "tenant_id", "created_at"),
        Index("ix_transactions_membership_created", "membership_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False
    )
    membership_id: Mapped[int] = mapped_column(
        ForeignKey("memberships.id", ondelete="RESTRICT"), nullable=False
    )
    staff_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    gross_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    voucher_id: Mapped[int | None] = mapped_column(
        ForeignKey("vouchers.id", ondelete="SET NULL"), nullable=True
    )
    voucher_discount_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    net_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    points_earned: Mapped[int] = mapped_column(Integer, nullable=False)
    method: Mapped[TransactionMethod] = mapped_column(
        String(20), nullable=False
    )
    note: Mapped[str | None] = mapped_column(String(1000), nullable=True)
