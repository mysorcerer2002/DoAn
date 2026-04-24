import enum
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Computed,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    text as sa_text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.membership import Membership
    from app.models.user import User
    from app.models.voucher import Voucher


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
        Index("ix_transactions_partner_created", "partner_id", "created_at"),
        Index("ix_transactions_membership_created", "membership_id", "created_at"),
        Index(
            "ux_transactions_partner_receipt_code",
            "partner_id",
            "receipt_code",
            unique=True,
            postgresql_where=sa_text("receipt_code IS NOT NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    partner_id: Mapped[int] = mapped_column(
        ForeignKey("partners.id", ondelete="RESTRICT"), nullable=False
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
    receipt_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # Phase 10 M12 — GENERATED STORED (DB tự tính), read-only trong app.
    legal_discount_ratio: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        Computed(
            "voucher_discount_amount::NUMERIC / NULLIF(gross_amount, 0) * 100",
            persisted=True,
        ),
        nullable=True,
    )

    membership: Mapped["Membership"] = relationship(
        "Membership", foreign_keys=[membership_id], lazy="noload"
    )
    staff: Mapped["User | None"] = relationship(
        "User", foreign_keys=[staff_id], lazy="noload"
    )
    voucher: Mapped["Voucher | None"] = relationship(
        "Voucher", foreign_keys=[voucher_id], lazy="noload"
    )
