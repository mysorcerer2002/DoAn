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
    """Append-only ledger ghi mọi biến động điểm (global cross-shop, scope user_id).

    PostgreSQL trigger `no_update_or_delete_point_ledger` chặn UPDATE/DELETE.
    """
    __tablename__ = "point_ledger"
    __table_args__ = (
        # Suffix-only — convention prepend `ck_point_ledger_` → final
        # `ck_point_ledger_balance_nonneg`. Khác với rows hiện hữu bị
        # double-prefix (debt cũ); migration M5 không tái-tạo CK này.
        CheckConstraint("balance_after >= 0", name="balance_nonneg"),
        Index("ix_point_ledger_user_created", "user_id", "created_at"),
        Index("ix_point_ledger_partner_created", "partner_id", "created_at"),
        Index(
            "ix_point_ledger_actor_created",
            "actor_user_id",
            "created_at",
            postgresql_where="actor_user_id IS NOT NULL",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    partner_id: Mapped[int] = mapped_column(
        ForeignKey("partners.id", ondelete="RESTRICT"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
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
    actor_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
