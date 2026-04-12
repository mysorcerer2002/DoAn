from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user, get_tenant_id, require_staff_in_tenant
from app.core.limiter import limiter
from app.core.phone import InvalidPhoneError
from app.models.tenant_staff import TenantStaffRole
from app.models.user import User
from app.schemas.transaction import (
    CreateManualTransactionRequest,
    TransactionResponse,
    TransactionWithMemberResponse,
)
from app.services.transaction_service import (
    NoActivePointRuleError,
    TransactionService,
)

router = APIRouter(prefix="/merchant/transactions", tags=["merchant-transactions"])


@router.post("", response_model=TransactionWithMemberResponse, status_code=201)
@limiter.limit("30/minute")
async def create_manual_transaction(
    request: Request,
    body: CreateManualTransactionRequest,
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_staff_in_tenant),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TransactionWithMemberResponse:
    service = TransactionService(db)
    try:
        return await service.create_manual(
            tenant_id=tenant_id, staff_id=user.id, request=body
        )
    except InvalidPhoneError as e:
        raise HTTPException(status_code=422, detail=f"Invalid phone: {e}") from e
    except NoActivePointRuleError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except IntegrityError as e:
        raise HTTPException(
            status_code=409, detail="Database integrity violation"
        ) from e


@router.get("", response_model=list[TransactionResponse])
async def list_transactions(
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_staff_in_tenant),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[TransactionResponse]:
    service = TransactionService(db)
    rows = await service.list_transactions(
        tenant_id=tenant_id, limit=limit, offset=offset
    )
    return [TransactionResponse.model_validate(t) for t in rows]
