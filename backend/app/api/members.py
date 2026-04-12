from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_tenant_id, require_staff_in_tenant
from app.models.tenant_staff import TenantStaffRole
from app.schemas.ledger import LedgerEntryResponse
from app.schemas.member import MemberResponse
from app.services.ledger_service import LedgerService
from app.services.member_service import MemberService

router = APIRouter(prefix="/merchant/members", tags=["merchant-members"])


@router.get("", response_model=list[MemberResponse])
async def list_members(
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_staff_in_tenant),
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
) -> list[MemberResponse]:
    service = MemberService(db)
    members = await service.list_members(
        tenant_id=tenant_id, limit=limit, offset=offset
    )
    return [
        MemberResponse(
            membership_id=m.id,
            tenant_id=m.tenant_id,
            user_id=m.user_id,
            user_phone=m.user.phone,
            user_full_name=m.user.full_name,
            user_email=m.user.email,
            points_balance=m.points_balance,
            total_points_earned=m.total_points_earned,
            current_tier_id=m.current_tier_id,
            current_tier_name=m.current_tier.name if m.current_tier else None,
            joined_at=m.joined_at,
            last_activity_at=m.last_activity_at,
            is_new=False,
        )
        for m in members
    ]


@router.get("/{membership_id}", response_model=MemberResponse)
async def get_member(
    membership_id: int,
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_staff_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> MemberResponse:
    service = MemberService(db)
    m = await service.get_member_by_id(
        tenant_id=tenant_id, membership_id=membership_id
    )
    if m is None:
        raise HTTPException(status_code=404, detail="Member not found")
    return MemberResponse(
        membership_id=m.id,
        tenant_id=m.tenant_id,
        user_id=m.user_id,
        user_phone=m.user.phone,
        user_full_name=m.user.full_name,
        user_email=m.user.email,
        points_balance=m.points_balance,
        total_points_earned=m.total_points_earned,
        current_tier_id=m.current_tier_id,
        current_tier_name=m.current_tier.name if m.current_tier else None,
        joined_at=m.joined_at,
        last_activity_at=m.last_activity_at,
        is_new=False,
    )


@router.get("/{membership_id}/ledger", response_model=list[LedgerEntryResponse])
async def get_member_ledger(
    membership_id: int,
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_staff_in_tenant),
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> list[LedgerEntryResponse]:
    service = LedgerService(db)
    rows = await service.get_history(
        tenant_id=tenant_id, membership_id=membership_id, limit=limit
    )
    return [LedgerEntryResponse.model_validate(r) for r in rows]
