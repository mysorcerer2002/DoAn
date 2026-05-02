from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import (
    get_current_user,
    get_partner_id,
    require_owner_in_partner,
    require_staff_in_partner,
)
from app.models.user import User
from app.core.limiter import limiter
from app.core.phone import InvalidPhoneError
from app.schemas.transaction import (
    CreateManualTransactionRequest,
    CreateQrCustomerTransactionRequest,
    CustomerLookupResponse,
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
    MembershipDisabledError,
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
    _=Depends(require_staff_in_partner),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TransactionWithMemberResponse:
    service = TransactionService(db)
    try:
        return await service.create_manual(
            partner_id=partner_id, request=body, actor_user_id=current_user.id
        )
    except InvalidPhoneError as e:
        raise HTTPException(status_code=422, detail=f"Invalid phone: {e}") from e
    except MembershipDisabledError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
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
    _=Depends(require_staff_in_partner),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TransactionWithMemberResponse:
    """Owner quét QR khách (raw user_id) → tích điểm.

    Khác `/` (manual theo phone): payload là raw user_id string — backend
    verify user tồn tại và auto-enroll nếu chưa là member.
    """
    from app.services.qr_service import (
        QrPayloadInvalidError,
        QrUserNotFoundError,
    )

    service = TransactionService(db)
    try:
        return await service.create_qr_customer(
            partner_id=partner_id, request=body, actor_user_id=current_user.id
        )
    except QrPayloadInvalidError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except QrUserNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except NoMembershipError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except MembershipDisabledError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
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


@router.get("/customer-by-phone", response_model=CustomerLookupResponse)
async def lookup_customer_by_phone(
    phone: str = Query(min_length=8, max_length=20),
    partner_id: int = Depends(get_partner_id),
    _=Depends(require_staff_in_partner),
    db: AsyncSession = Depends(get_db),
) -> CustomerLookupResponse:
    """Staff lookup khách theo SĐT trước khi tích điểm. found=False khi chưa có user — sẽ auto-create lúc submit."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from app.core.phone import normalize_phone
    from app.models.membership import Membership
    from app.models.user import User

    try:
        normalized = normalize_phone(phone)
    except InvalidPhoneError as e:
        raise HTTPException(status_code=422, detail=f"SĐT không hợp lệ: {e}") from e

    user = await db.scalar(
        select(User).where(User.phone == normalized, User.is_active.is_(True))
    )
    if user is None:
        return CustomerLookupResponse(found=False)

    membership = await db.scalar(
        select(Membership)
        .options(selectinload(Membership.current_tier))
        .where(Membership.user_id == user.id, Membership.partner_id == partner_id)
    )
    return CustomerLookupResponse(
        found=True,
        user_id=user.id,
        phone=user.phone,
        full_name=user.full_name,
        email=user.email,
        points_balance=user.points_balance,
        is_member=membership is not None,
        is_active=membership.is_active if membership else None,
        lifetime_earned=membership.lifetime_earned if membership else None,
        current_tier_name=(
            membership.current_tier.name
            if membership and membership.current_tier
            else None
        ),
    )


@router.get("/customer-by-qr", response_model=CustomerLookupResponse)
async def lookup_customer_by_qr(
    qr: str = Query(min_length=1, max_length=500),
    partner_id: int = Depends(get_partner_id),
    _=Depends(require_staff_in_partner),
    db: AsyncSession = Depends(get_db),
) -> CustomerLookupResponse:
    """Staff lookup khách từ QR scan. 400 nếu QR invalid, 404 nếu user không tồn tại.
    is_member=False nếu chưa là thành viên — auto-enroll xảy ra khi submit tích điểm."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from app.models.membership import Membership
    from app.models.user import User

    try:
        user_id = int(qr.strip())
        if user_id <= 0:
            raise ValueError
    except (ValueError, AttributeError) as e:
        raise HTTPException(status_code=400, detail="QR không hợp lệ.") from e

    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=404, detail="Không tìm thấy khách hàng từ QR."
        )

    membership = await db.scalar(
        select(Membership)
        .options(selectinload(Membership.current_tier))
        .where(Membership.user_id == user.id, Membership.partner_id == partner_id)
    )

    return CustomerLookupResponse(
        found=True,
        user_id=user.id,
        phone=user.phone,
        full_name=user.full_name,
        email=user.email,
        points_balance=user.points_balance,
        is_member=membership is not None,
        is_active=membership.is_active if membership else None,
        lifetime_earned=membership.lifetime_earned if membership else None,
        current_tier_name=(
            membership.current_tier.name
            if membership and membership.current_tier
            else None
        ),
    )


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
    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=422,
            detail="date_from phải nhỏ hơn hoặc bằng date_to",
        )
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
