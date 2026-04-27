from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user, get_partner_id, require_owner_in_partner
from app.models.membership import Membership
from app.models.point_ledger import LedgerReason, LedgerRefType
from app.models.user import User
from app.schemas.ledger import LedgerEntryResponse
from app.schemas.member import MemberResponse
from app.services.ledger_service import LedgerService
from app.services.member_service import MemberService

router = APIRouter(prefix="/partner/members", tags=["partner-members"])


class AdjustPointsRequest(BaseModel):
    delta: int = Field(..., description="Số điểm cộng/trừ; phải khác 0")
    description: str = Field(min_length=3, max_length=300)


class UpdateMemberRequest(BaseModel):
    is_active: bool


def _to_response(m: Membership) -> MemberResponse:
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
        is_active=m.is_active,
        is_new=False,
    )


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
    return [_to_response(m) for m in members]


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
    return _to_response(m)


@router.get("/{membership_id}/ledger", response_model=list[LedgerEntryResponse])
async def get_member_ledger(
    membership_id: int,
    partner_id: int = Depends(get_partner_id),
    _=Depends(require_owner_in_partner),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> list[LedgerEntryResponse]:
    """Lịch sử điểm của member trong shop hiện tại (filter theo partner_id)."""
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


@router.post("/{membership_id}/adjust-points", response_model=MemberResponse)
async def adjust_member_points(
    membership_id: int,
    body: AdjustPointsRequest,
    partner_id: int = Depends(get_partner_id),
    _=Depends(require_owner_in_partner),
    actor: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MemberResponse:
    """Owner cộng/trừ điểm thủ công cho member.

    Atomic UPDATE...WHERE points_balance + :delta >= 0 RETURNING tránh
    TOCTOU. Rowcount=0 → không đủ số dư để trừ → 400.
    Ghi PointLedger reason=ADJUST với actor_user_id để audit.
    KHÔNG đụng lifetime_earned (adjust = correction, không phải earning).
    """
    if body.delta == 0:
        raise HTTPException(status_code=400, detail="delta phải khác 0")

    service = MemberService(db)
    m = await service.get_member_by_id(
        partner_id=partner_id, membership_id=membership_id
    )
    if m is None:
        raise HTTPException(status_code=404, detail="Member not found")

    result = await db.execute(
        update(User)
        .where(
            User.id == m.user_id,
            User.points_balance + body.delta >= 0,
        )
        .values(points_balance=User.points_balance + body.delta)
        .returning(User.points_balance)
    )
    row = result.first()
    if row is None:
        raise HTTPException(
            status_code=400,
            detail="Số dư của khách không đủ để trừ điểm.",
        )
    new_balance = int(row[0])

    ledger = LedgerService(db)
    await ledger.log_entry(
        partner_id=partner_id,
        user_id=m.user_id,
        delta=body.delta,
        reason=LedgerReason.ADJUST,
        ref_type=LedgerRefType.MANUAL,
        ref_id=None,
        new_balance=new_balance,
        description=body.description,
        actor_user_id=actor.id,
    )
    await db.commit()

    refreshed = await service.get_member_by_id(
        partner_id=partner_id, membership_id=membership_id
    )
    if refreshed is None:
        raise HTTPException(status_code=404, detail="Member not found")
    return _to_response(refreshed)


@router.patch("/{membership_id}", response_model=MemberResponse)
async def update_member(
    membership_id: int,
    body: UpdateMemberRequest,
    partner_id: int = Depends(get_partner_id),
    _=Depends(require_owner_in_partner),
    db: AsyncSession = Depends(get_db),
) -> MemberResponse:
    """Đóng/mở thẻ thành viên ở đối tác hiện tại.

    Khi is_active=False, transaction_service từ chối tích điểm cho member này.
    """
    m = await db.scalar(
        select(Membership).where(
            Membership.id == membership_id,
            Membership.partner_id == partner_id,
        )
    )
    if m is None:
        raise HTTPException(status_code=404, detail="Member not found")
    m.is_active = body.is_active
    await db.commit()

    service = MemberService(db)
    refreshed = await service.get_member_by_id(
        partner_id=partner_id, membership_id=membership_id
    )
    if refreshed is None:
        raise HTTPException(status_code=404, detail="Member not found")
    return _to_response(refreshed)
