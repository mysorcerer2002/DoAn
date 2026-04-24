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
from app.core.limiter import limiter
from app.core.phone import InvalidPhoneError
from app.models.partner_staff import PartnerStaffRole
from app.models.user import User
from app.schemas.transaction import (
    CreateManualTransactionRequest,
    CreateQrCustomerTransactionRequest,
    TransactionResponse,
    TransactionWithMemberResponse,
)
from app.services.transaction_service import (
    InvalidVoucherError,
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
    _role: PartnerStaffRole = Depends(require_staff_in_partner),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TransactionWithMemberResponse:
    service = TransactionService(db)
    try:
        return await service.create_manual(
            partner_id=partner_id, staff_id=user.id, request=body
        )
    except InvalidPhoneError as e:
        raise HTTPException(status_code=422, detail=f"Invalid phone: {e}") from e
    except NoActivePointRuleError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except InvalidVoucherError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except IntegrityError as e:
        raise HTTPException(
            status_code=409, detail="Database integrity violation"
        ) from e


@router.post("/qr", response_model=TransactionWithMemberResponse, status_code=201)
@limiter.limit("30/minute")
async def create_qr_transaction(
    request: Request,
    body: CreateQrCustomerTransactionRequest,
    partner_id: int = Depends(get_partner_id),
    _role: PartnerStaffRole = Depends(require_staff_in_partner),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TransactionWithMemberResponse:
    """Staff quét QR khách (JWT hoặc fallback code) → tích điểm.

    Khác `/` (manual theo phone): payload là JWT/fallback code — backend
    decode ra user_id, bắt buộc user đã là member của tenant.
    """
    service = TransactionService(db)
    try:
        return await service.create_qr_customer(
            partner_id=partner_id, staff_id=user.id, request=body
        )
    except ValueError as e:
        # QR invalid / expired / không decode được
        raise HTTPException(status_code=400, detail=str(e)) from e
    except NoMembershipError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except NoActivePointRuleError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except IntegrityError as e:
        raise HTTPException(
            status_code=409, detail="Database integrity violation"
        ) from e


@router.get("", response_model=list[TransactionResponse])
async def list_transactions(
    partner_id: int = Depends(get_partner_id),
    _role: PartnerStaffRole = Depends(require_owner_in_partner),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[TransactionResponse]:
    service = TransactionService(db)
    rows = await service.list_transactions(
        partner_id=partner_id, limit=limit, offset=offset
    )
    return [TransactionResponse.model_validate(t) for t in rows]
