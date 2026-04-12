import enum

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class LedgerReason(str, enum.Enum):
    EARN = "earn"
    REDEEM = "redeem"
    ADJUST = "adjust"
    EXPIRE = "expire"
    REFUND = "refund"


class LedgerRefType(str, enum.Enum):
    TRANSACTION = "transaction"
    REDEMPTION = "redemption"
    MANUAL = "manual"
    SYSTEM = "system"


class PointLedger(Base, TimestampMixin):
    """Append-only ledger ghi mọi biến động điểm.

    PostgreSQL trigger chặn UPDATE/DELETE — xem migration.
    """
    __tablename__ = "point_ledger"
    __table_args__ = (
        CheckConstraint("balance_after >= 0", name="ck_point_ledger_balance_nonneg"),
        Index("ix_point_ledger_membership_created", "membership_id", "created_at"),
        Index("ix_point_ledger_tenant_created", "tenant_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False
    )
    membership_id: Mapped[int] = mapped_column(
        ForeignKey("memberships.id", ondelete="RESTRICT"), nullable=False
    )
    delta: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[LedgerReason] = mapped_column(
        String(20), nullable=False
    )
    ref_type: Mapped[LedgerRefType] = mapped_column(
        String(20), nullable=False
    )
    ref_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
