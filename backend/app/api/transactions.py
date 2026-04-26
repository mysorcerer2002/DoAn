from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import (
    get_partner_id,
    require_owner_in_partner,
)
from app.core.limiter import limiter
from app.core.phone import InvalidPhoneError
from app.schemas.transaction import (
    CreateManualTransactionRequest,
    CreateQrCustomerTransactionRequest,
    TransactionDetailResponse,
    TransactionListResponse,
    TransactionUpdateRequest,
    TransactionWithMemberResponse,
)
from app.services.partner_transaction_service import (
    DuplicateReceiptCodeError,
    PartnerTransactionService,
    TransactionNotFoundError,
)
from app.services.transaction_service import (
    NoActivePointRuleError,
    NoMembershipError,
    TransactionService,
)

router = APIRouter(prefix="/partner/transactions", tags=["partner-transactions"])


@router.post("", response_model=TransactionWithMemberResponse, status_code=201)
@limiter.limit("30/minute")
async def create_manual_transaction(
    request: Request,
    body: CreateManualTransactionRequest,
    partner_id: int = Depends(get_partner_id),
    _=Depends(require_owner_in_partner),
    db: AsyncSession = Depends(get_db),
) -> TransactionWithMemberResponse:
    service = TransactionService(db)
    try:
        return await service.create_manual(partner_id=partner_id, request=body)
    except InvalidPhoneError as e:
        raise HTTPException(status_code=422, detail=f"Invalid phone: {e}") from e
    except NoActivePointRuleError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except IntegrityError as e:
        if "ux_transactions_partner_receipt_code" in str(getattr(e, "orig", "")):
            raise HTTPException(
                status_code=409,
                detail="Mã hoá đơn đã tồn tại, vui lòng dùng mã khác.",
            ) from e
        raise HTTPException(
            status_code=409, detail="Vi phạm ràng buộc dữ liệu"
        ) from e


@router.post("/qr", response_model=TransactionWithMemberResponse, status_code=201)
@limiter.limit("30/minute")
async def create_qr_transaction(
    request: Request,
    body: CreateQrCustomerTransactionRequest,
    partner_id: int = Depends(get_partner_id),
    _=Depends(require_owner_in_partner),
    db: AsyncSession = Depends(get_db),
) -> TransactionWithMemberResponse:
    """Owner quét QR khách (raw user_id) → tích điểm.

    Khác `/` (manual theo phone): payload là raw user_id string — backend
    verify user tồn tại và là member của partner.
    """
    from app.services.qr_service import (
        QrPayloadInvalidError,
        QrUserNotFoundError,
        QrUserNotMemberError,
    )

    service = TransactionService(db)
    try:
        return await service.create_qr_customer(partner_id=partner_id, request=body)
    except QrPayloadInvalidError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except (QrUserNotFoundError, QrUserNotMemberError) as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except NoMembershipError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except NoActivePointRuleError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except IntegrityError as e:
        if "ux_transactions_partner_receipt_code" in str(getattr(e, "orig", "")):
            raise HTTPException(
                status_code=409,
                detail="Mã hoá đơn đã tồn tại, vui lòng dùng mã khác.",
            ) from e
        raise HTTPException(
            status_code=409, detail="Vi phạm ràng buộc dữ liệu"
        ) from e


@router.get("", response_model=TransactionListResponse)
async def list_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    date_from: date | None = None,
    date_to: date | None = None,
    q: str | None = None,
    db: AsyncSession = Depends(get_db),
    partner_id: int = Depends(get_partner_id),
    _=Depends(require_owner_in_partner),
) -> TransactionListResponse:
    svc = PartnerTransactionService(db)
    return await svc.list(
        partner_id=partner_id,
        page=page,
        page_size=page_size,
        date_from=date_from,
        date_to=date_to,
        q=q,
    )


@router.get("/{transaction_id}", response_model=TransactionDetailResponse)
async def get_transaction(
    transaction_id: int,
    db: AsyncSession = Depends(get_db),
    partner_id: int = Depends(get_partner_id),
    _=Depends(require_owner_in_partner),
) -> TransactionDetailResponse:
    svc = PartnerTransactionService(db)
    try:
        return await svc.get_detail(partner_id, transaction_id)
    except TransactionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.patch("/{transaction_id}", response_model=TransactionDetailResponse)
async def update_transaction(
    transaction_id: int,
    payload: TransactionUpdateRequest,
    db: AsyncSession = Depends(get_db),
    partner_id: int = Depends(get_partner_id),
    _=Depends(require_owner_in_partner),
) -> TransactionDetailResponse:
    svc = PartnerTransactionService(db)
    try:
        return await svc.update(partner_id, transaction_id, payload)
    except TransactionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except DuplicateReceiptCodeError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
