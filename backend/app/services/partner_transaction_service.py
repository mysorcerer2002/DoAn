from datetime import date, datetime, time
from sqlalchemy import Select, and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.membership import Membership
from app.models.transaction import Transaction
from app.schemas.transaction import (
    TransactionDetailResponse,
    TransactionListItem,
    TransactionListResponse,
    TransactionUpdateRequest,
)


class TransactionNotFoundError(Exception):
    pass


class DuplicateReceiptCodeError(Exception):
    pass


class PartnerTransactionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def _base_select(self, partner_id: int) -> Select:
        return (
            select(Transaction)
            .where(Transaction.partner_id == partner_id)
            .options(
                joinedload(Transaction.membership).joinedload(Membership.user),
            )
        )

    async def list(
        self,
        partner_id: int,
        *,
        page: int = 1,
        page_size: int = 20,
        date_from: date | None = None,
        date_to: date | None = None,
        q: str | None = None,
    ) -> TransactionListResponse:
        page = max(1, page)
        page_size = max(1, min(page_size, 100))

        extra: list = []
        if date_from:
            extra.append(Transaction.created_at >= datetime.combine(date_from, time.min))
        if date_to:
            extra.append(Transaction.created_at < datetime.combine(date_to, time.max))
        if q:
            extra.append(Transaction.receipt_code == q)

        total_stmt = (
            select(func.count())
            .select_from(Transaction)
            .where(Transaction.partner_id == partner_id)
        )
        if extra:
            total_stmt = total_stmt.where(and_(*extra))
        total = (await self.db.scalar(total_stmt)) or 0

        stmt = self._base_select(partner_id).order_by(Transaction.created_at.desc())
        if extra:
            stmt = stmt.where(and_(*extra))
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        rows = (await self.db.scalars(stmt)).unique().all()

        items = [self._to_list_item(t) for t in rows]
        return TransactionListResponse(
            items=items, total=total, page=page, page_size=page_size
        )

    async def get_detail(
        self, partner_id: int, transaction_id: int
    ) -> TransactionDetailResponse:
        stmt = self._base_select(partner_id).where(Transaction.id == transaction_id)
        txn = (await self.db.scalars(stmt)).unique().one_or_none()
        if txn is None:
            raise TransactionNotFoundError(
                f"Không tìm thấy giao dịch id={transaction_id}"
            )
        return self._to_detail(txn)

    async def update(
        self,
        partner_id: int,
        transaction_id: int,
        payload: TransactionUpdateRequest,
    ) -> TransactionDetailResponse:
        from sqlalchemy.exc import IntegrityError

        txn = await self.db.get(Transaction, transaction_id)
        if txn is None or txn.partner_id != partner_id:
            raise TransactionNotFoundError(
                f"Không tìm thấy giao dịch id={transaction_id}"
            )

        data = payload.model_dump(exclude_unset=True)
        for key, value in data.items():
            setattr(txn, key, value)

        try:
            await self.db.flush()
        except IntegrityError as e:
            await self.db.rollback()
            if "ux_transactions_partner_receipt_code" in str(e.orig):
                raise DuplicateReceiptCodeError(
                    "Mã hoá đơn đã tồn tại, vui lòng dùng mã khác."
                ) from e
            raise

        return await self.get_detail(partner_id, transaction_id)

    @staticmethod
    def _to_list_item(t: Transaction) -> TransactionListItem:
        member_user = t.membership.user if t.membership else None
        return TransactionListItem(
            id=t.id,
            created_at=t.created_at,
            receipt_code=t.receipt_code,
            membership_display_name=(
                member_user.full_name or member_user.phone
                if member_user
                else "(đã xoá)"
            ),
            gross_amount=t.gross_amount,
            net_amount=t.net_amount,
            points_earned=t.points_earned,
            method=t.method.value if hasattr(t.method, "value") else str(t.method),
        )

    @staticmethod
    def _to_detail(t: Transaction) -> TransactionDetailResponse:
        base = PartnerTransactionService._to_list_item(t).model_dump()
        return TransactionDetailResponse(
            **base,
            note=t.note,
        )
