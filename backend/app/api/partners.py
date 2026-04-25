from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from fastapi import Query

from app.core.db import get_db
from app.core.deps import (
    get_current_user,
    get_partner_id,
    require_owner_in_partner,
    require_staff_in_partner,
)
from app.core.limiter import limiter
from app.models.membership import Membership
from app.models.point_ledger import PointLedger
from app.models.partner import Partner, PartnerStatus
from app.models.partner_staff import PartnerStaffRole
from app.models.reward import Reward
from app.models.user import User
from app.models.voucher import Voucher, VoucherStatus
from app.schemas.ledger import LedgerEntryResponse
from app.schemas.member import MemberResponse
from app.schemas.partner import (
    MyPartnerSummary,
    PartnerCreateRequest,
    PartnerDetailForMember,
    PartnerResponse,
    PartnerStaffSummary,
    PartnerUpdateRequest,
)
from app.schemas.voucher import VoucherResponse
from app.services.partner_service import PartnerNotFoundError, PartnerService

partner_router = APIRouter(prefix="/partner", tags=["partner"])
partners_router = APIRouter(prefix="/partners", tags=["partners"])
users_router = APIRouter(prefix="/users", tags=["users"])


@partner_router.post(
    "/register",
    response_model=PartnerResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("10/minute")
async def register_partner(
    request: Request,
    body: PartnerCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PartnerResponse:
    """Owner đăng ký đối tác mới (status=pending, chờ Super Admin duyệt)."""
    service = PartnerService(db)
    partner = await service.create_partner(owner=current_user, request=body)
    return PartnerResponse.model_validate(partner)


@users_router.get("/me/partners-as-staff", response_model=list[PartnerStaffSummary])
async def list_my_partners_as_staff(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[PartnerStaffSummary]:
    """List partner mà user là staff/owner. Frontend dùng để chọn partner sau login."""
    service = PartnerService(db)
    rows = await service.list_partners_for_user(user_id=user.id)
    return [PartnerStaffSummary.model_validate(row) for row in rows]


@users_router.get("/me/ledger", response_model=list[LedgerEntryResponse])
async def list_my_ledger(
    user: User = Depends(get_current_user),
    partner_slug: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[LedgerEntryResponse]:
    """Lịch sử tích điểm của current user.

    Nếu partner_slug được truyền, chỉ lấy ledger của partner đó.
    Ngược lại, lấy toàn bộ qua TẤT CẢ partner user tham gia.
    """
    membership_query = select(Membership).where(
        Membership.user_id == user.id,
        Membership.archived_at.is_(None),
    )
    if partner_slug is not None:
        partner = await db.scalar(
            select(Partner).where(Partner.slug == partner_slug)
        )
        if partner is None:
            raise HTTPException(status_code=404, detail="Partner not found")
        membership_query = membership_query.where(
            Membership.partner_id == partner.id
        )

    membership_ids = [
        row.id
        for row in (await db.scalars(membership_query)).all()
    ]
    if not membership_ids:
        return []
    rows = (
        await db.scalars(
            select(PointLedger)
            .where(PointLedger.membership_id.in_(membership_ids))
            .order_by(PointLedger.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
    ).all()
    return [LedgerEntryResponse.model_validate(r) for r in rows]


def _voucher_to_response(v: Voucher) -> VoucherResponse:
    """Helper map Voucher (với joinedload campaign) → VoucherResponse đầy đủ field."""
    campaign = v.campaign
    discount_type_str: str | None = None
    if campaign is not None:
        dt = campaign.discount_type
        discount_type_str = dt.value if hasattr(dt, "value") else str(dt)
    return VoucherResponse(
        id=v.id,
        partner_id=v.partner_id,
        campaign_id=v.campaign_id,
        membership_id=v.membership_id,
        code=v.code,
        status=v.status,
        issued_at=v.issued_at,
        used_at=v.used_at,
        expires_at=v.expires_at,
        campaign_name=campaign.name if campaign else None,
        campaign_description=campaign.description if campaign else None,
        campaign_terms=campaign.terms if campaign else None,
        campaign_usage_guide=campaign.usage_guide if campaign else None,
        campaign_support_contact=campaign.support_contact if campaign else None,
        discount_type=discount_type_str,
        discount_value=campaign.discount_value if campaign else None,
        min_order=campaign.min_order if campaign else None,
        max_discount=campaign.max_discount if campaign else None,
    )


@users_router.get("/me/vouchers", response_model=list[VoucherResponse])
async def list_my_vouchers_all_partners(
    user: User = Depends(get_current_user),
    status: VoucherStatus | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[VoucherResponse]:
    """Voucher của current user qua TẤT CẢ partner họ là member."""
    membership_ids = [
        row.id
        for row in (
            await db.scalars(
                select(Membership).where(
                    Membership.user_id == user.id,
                    Membership.archived_at.is_(None),
                )
            )
        ).all()
    ]
    if not membership_ids:
        return []
    stmt = (
        select(Voucher)
        .options(joinedload(Voucher.campaign))
        .where(Voucher.membership_id.in_(membership_ids))
    )
    if status is not None:
        stmt = stmt.where(Voucher.status == status)
    stmt = stmt.order_by(Voucher.issued_at.desc())
    rows = (await db.scalars(stmt)).all()
    return [_voucher_to_response(v) for v in rows]


@users_router.get("/me/memberships", response_model=list[MemberResponse])
async def list_my_memberships(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MemberResponse]:
    """List tất cả membership của current user (các shop user đã tham gia)."""
    rows = (
        await db.scalars(
            select(Membership)
            .options(
                joinedload(Membership.user),
                joinedload(Membership.current_tier),
                joinedload(Membership.partner),
            )
            .where(
                Membership.user_id == user.id,
                Membership.archived_at.is_(None),
            )
            .order_by(Membership.last_activity_at.desc().nullslast())
        )
    ).unique().all()
    return [
        MemberResponse(
            membership_id=m.id,
            partner_id=m.partner_id,
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
        for m in rows
    ]


@users_router.get("/me/partners", response_model=list[MyPartnerSummary])
async def list_my_partners(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MyPartnerSummary]:
    """Tất cả partner ACTIVE trên platform.

    Với partner mà user đã là member, kèm `is_member=True`, `points_balance`,
    `current_tier_name`. Dùng cho trang `/member/partners` để customer
    vừa khám phá shop vừa thấy hạng + điểm hiện tại trên card.
    """
    partners = (
        await db.scalars(
            select(Partner)
            .where(Partner.status == PartnerStatus.ACTIVE)
            .order_by(Partner.name.asc())
        )
    ).all()

    memberships = (
        await db.scalars(
            select(Membership)
            .options(joinedload(Membership.current_tier))
            .where(
                Membership.user_id == user.id,
                Membership.archived_at.is_(None),
            )
        )
    ).all()
    membership_by_partner = {m.partner_id: m for m in memberships}

    result: list[MyPartnerSummary] = []
    for p in partners:
        m = membership_by_partner.get(p.id)
        result.append(
            MyPartnerSummary(
                id=p.id,
                name=p.name,
                slug=p.slug,
                category=str(p.category.value if hasattr(p.category, "value") else p.category),
                description=p.description,
                logo_url=p.logo_url,
                is_member=m is not None,
                points_balance=m.points_balance if m else None,
                current_tier_name=m.current_tier.name if m and m.current_tier else None,
            )
        )
    return result


@users_router.get("/me/partners/{slug}", response_model=PartnerDetailForMember)
async def get_partner_detail_for_member(
    slug: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PartnerDetailForMember:
    """Chi tiết partner cho khách hàng.

    Nếu user là member của partner, trả thêm points_balance, tier, v.v.
    """
    partner = await db.scalar(
        select(Partner).where(Partner.slug == slug, Partner.status == PartnerStatus.ACTIVE)
    )
    if partner is None:
        raise HTTPException(status_code=404, detail="Partner not found")

    membership = await db.scalar(
        select(Membership).options(joinedload(Membership.current_tier)).where(
            Membership.partner_id == partner.id,
            Membership.user_id == user.id,
            Membership.archived_at.is_(None),
        )
    )

    return PartnerDetailForMember(
        id=partner.id,
        name=partner.name,
        slug=partner.slug,
        category=str(partner.category.value if hasattr(partner.category, "value") else partner.category),
        description=partner.description,
        logo_url=partner.logo_url,
        contact_phone=partner.contact_phone,
        contact_email=partner.contact_email,
        address=partner.address,
        website=partner.website,
        business_hours=partner.business_hours,
        is_member=membership is not None,
        points_balance=membership.points_balance if membership else None,
        total_points_earned=membership.total_points_earned if membership else None,
        current_tier_name=membership.current_tier.name if membership and membership.current_tier else None,
        joined_at=membership.joined_at if membership else None,
        last_activity_at=membership.last_activity_at if membership else None,
    )


@users_router.get("/me/partners/{slug}/rewards")
async def list_partner_rewards_for_member(
    slug: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Rewards active của 1 partner. user_points_balance/can_redeem dựa trên membership.

    Non-member: balance=0, can_redeem=False (không đổi được kể cả đủ điểm).
    """
    partner = await db.scalar(
        select(Partner).where(
            Partner.slug == slug, Partner.status == PartnerStatus.ACTIVE
        )
    )
    if partner is None:
        raise HTTPException(status_code=404, detail="Partner not found")

    membership = await db.scalar(
        select(Membership).where(
            Membership.partner_id == partner.id,
            Membership.user_id == user.id,
            Membership.archived_at.is_(None),
        )
    )
    is_member = membership is not None
    balance = membership.points_balance if membership else 0

    rewards = (
        await db.scalars(
            select(Reward)
            .where(
                Reward.partner_id == partner.id,
                Reward.deleted_at.is_(None),
                Reward.is_active.is_(True),
            )
            .order_by(Reward.points_cost.asc())
        )
    ).all()

    return [
        {
            "id": r.id,
            "name": r.name,
            "description": r.description,
            "points_cost": r.points_cost,
            "stock": r.stock,
            "image_url": r.image_url,
            "user_points_balance": balance,
            "can_redeem": is_member and balance >= r.points_cost,
        }
        for r in rewards
    ]


@users_router.get("/me/rewards")
async def list_my_rewards(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Rewards active của TẤT CẢ partner mà current user là member."""
    memberships_rows = (
        await db.execute(
            select(Membership, Partner.name, Partner.slug)
            .join(Partner, Membership.partner_id == Partner.id)
            .where(
                Membership.user_id == user.id,
                Membership.archived_at.is_(None),
            )
        )
    ).all()
    if not memberships_rows:
        return []

    partner_points = {m.partner_id: m.points_balance for m, _, _ in memberships_rows}
    partner_names = {m.partner_id: (name, slug) for m, name, slug in memberships_rows}
    partner_ids = list(partner_points.keys())

    rewards = (
        await db.scalars(
            select(Reward)
            .where(
                Reward.partner_id.in_(partner_ids),
                Reward.deleted_at.is_(None),
                Reward.is_active.is_(True),
            )
            .order_by(Reward.points_cost.asc())
        )
    ).all()

    return [
        {
            "id": r.id,
            "partner_id": r.partner_id,
            "partner_name": partner_names[r.partner_id][0],
            "partner_slug": partner_names[r.partner_id][1],
            "name": r.name,
            "description": r.description,
            "points_cost": r.points_cost,
            "stock": r.stock,
            "image_url": r.image_url,
            "user_points_balance": partner_points[r.partner_id],
            "can_redeem": partner_points[r.partner_id] >= r.points_cost,
        }
        for r in rewards
    ]


@partners_router.get("/me", response_model=PartnerResponse)
async def get_my_partner(
    partner_id: int = Depends(get_partner_id),
    _role: PartnerStaffRole = Depends(require_staff_in_partner),
    db: AsyncSession = Depends(get_db),
) -> PartnerResponse:
    """Lấy thông tin partner theo header X-Partner-Id. Yêu cầu là staff của partner."""
    service = PartnerService(db)
    try:
        partner = await service.get_partner_by_id(partner_id)
    except PartnerNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    if partner.status != PartnerStatus.ACTIVE:
        raise HTTPException(
            status_code=403,
            detail=f"Partner is {partner.status}, not active",
        )

    return PartnerResponse.model_validate(partner)


@partners_router.patch("/me", response_model=PartnerResponse)
async def update_my_partner(
    body: PartnerUpdateRequest,
    partner_id: int = Depends(get_partner_id),
    _role: PartnerStaffRole = Depends(require_owner_in_partner),
    db: AsyncSession = Depends(get_db),
) -> PartnerResponse:
    """Owner update thông tin shop (tên, mô tả, logo)."""
    service = PartnerService(db)
    try:
        partner = await service.update_partner(partner_id=partner_id, request=body)
    except PartnerNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return PartnerResponse.model_validate(partner)


@partner_router.get("/vouchers/check/{code}")
async def check_voucher_by_code(
    code: str,
    gross_amount: int = Query(default=0, ge=0),
    partner_id: int = Depends(get_partner_id),
    _role: PartnerStaffRole = Depends(require_staff_in_partner),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Staff/owner check voucher code: trả info + tính discount preview cho gross_amount."""
    from app.services.voucher_service import (
        VoucherExpiredError,
        VoucherInvalidStatusError,
        VoucherNotFoundError,
        VoucherService,
    )

    service = VoucherService(db)
    try:
        return await service.check_voucher_for_use(
            partner_id=partner_id,
            code=code,
            gross_amount=gross_amount,
        )
    except VoucherNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except (VoucherInvalidStatusError, VoucherExpiredError) as e:
        raise HTTPException(status_code=409, detail=str(e)) from e


@partner_router.get("/vouchers", response_model=list[VoucherResponse])
async def list_partner_vouchers(
    vstatus: VoucherStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    partner_id: int = Depends(get_partner_id),
    _role: PartnerStaffRole = Depends(require_owner_in_partner),
    db: AsyncSession = Depends(get_db),
) -> list[VoucherResponse]:
    """Merchant xem tất cả voucher đã phát cho partner này."""
    stmt = (
        select(Voucher)
        .options(joinedload(Voucher.campaign))
        .where(Voucher.partner_id == partner_id)
        .order_by(Voucher.issued_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if vstatus is not None:
        stmt = stmt.where(Voucher.status == vstatus)
    rows = (await db.scalars(stmt)).all()
    return [_voucher_to_response(v) for v in rows]
