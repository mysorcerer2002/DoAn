from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_partner_id, require_owner_in_partner
from app.schemas.ledger import LedgerEntryResponse
from app.schemas.member import MemberResponse
from app.services.ledger_service import LedgerService
from app.services.member_service import MemberService

router = APIRouter(prefix="/partner/members", tags=["partner-members"])


@router.get("", response_model=list[MemberResponse])
async def list_members(
    partner_id: int = Depends(get_partner_id),
    _=Depends(require_owner_in_partner),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[MemberResponse]:
    service = MemberService(db)
    members = await service.list_members(
        partner_id=partner_id, limit=limit, offset=offset
    )
    return [
        MemberResponse(
            membership_id=m.id,
            partner_id=m.partner_id,
            user_id=m.user_id,
            user_phone=m.user.phone,
            user_full_name=m.user.full_name,
            user_email=m.user.email,
            points_balance=m.user.points_balance,
            lifetime_earned=m.lifetime_earned,
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
    partner_id: int = Depends(get_partner_id),
    _=Depends(require_owner_in_partner),
    db: AsyncSession = Depends(get_db),
) -> MemberResponse:
    service = MemberService(db)
    m = await service.get_member_by_id(
        partner_id=partner_id, membership_id=membership_id
    )
    if m is None:
        raise HTTPException(status_code=404, detail="Member not found")
    return MemberResponse(
        membership_id=m.id,
        partner_id=m.partner_id,
        user_id=m.user_id,
        user_phone=m.user.phone,
        user_full_name=m.user.full_name,
        user_email=m.user.email,
        points_balance=m.user.points_balance,
        lifetime_earned=m.lifetime_earned,
        current_tier_id=m.current_tier_id,
        current_tier_name=m.current_tier.name if m.current_tier else None,
        joined_at=m.joined_at,
        last_activity_at=m.last_activity_at,
        is_new=False,
    )


@router.get("/{membership_id}/ledger", response_model=list[LedgerEntryResponse])
async def get_member_ledger(
    membership_id: int,
    partner_id: int = Depends(get_partner_id),
    _=Depends(require_owner_in_partner),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> list[LedgerEntryResponse]:
    """Lịch sử điểm của member trong shop hiện tại (filter theo partner_id)."""
    from sqlalchemy import select
    from app.models.membership import Membership

    member_user_id = await db.scalar(
        select(Membership.user_id).where(
            Membership.id == membership_id,
            Membership.partner_id == partner_id,
        )
    )
    if member_user_id is None:
        raise HTTPException(status_code=404, detail="Member not found")

    service = LedgerService(db)
    rows = await service.get_history(
        user_id=member_user_id, partner_id=partner_id, limit=limit
    )
    return [LedgerEntryResponse.model_validate(r) for r in rows]
