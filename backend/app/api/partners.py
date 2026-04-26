import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from fastapi import Query

from app.core.db import get_db
from app.core.deps import (
    get_current_user,
    get_partner_id,
    require_owner_in_partner,
)

logger = logging.getLogger(__name__)
from app.core.limiter import limiter
from app.models.membership import Membership
from app.models.redemption import Redemption
from app.models.point_ledger import PointLedger
from app.models.partner import Partner, PartnerStatus
from app.models.reward import Reward
from app.models.user import User
from app.schemas.ledger import LedgerEntryResponse
from app.schemas.member import MemberResponse
from app.schemas.redemption import (
    MyRedemptionDetailResponse,
    MyRedemptionListItem,
    MyRedemptionListResponse,
    RedeemRequest,
    RedemptionResponse,
)
from app.schemas.partner import (
    MyPartnerSummary,
    PartnerCreateRequest,
    PartnerDetailForMember,
    PartnerResponse,
    PartnerStaffSummary,
    PartnerUpdateRequest,
)
from app.schemas.partner_staff import StaffCreateRequest, StaffPatchRequest
from app.services.partner_service import PartnerNotFoundError, PartnerService
from app.services.redemption_service import (
    InsufficientPointsError,
    OutOfStockError,
    RedemptionService,
)

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
    """Lịch sử tích điểm của current user (ví toàn cục).

    Nếu partner_slug được truyền, chỉ lấy entry phát sinh tại partner đó.
    Ngược lại, lấy toàn bộ qua TẤT CẢ partner user từng giao dịch.
    """
    stmt = select(PointLedger).where(PointLedger.user_id == user.id)
    if partner_slug is not None:
        partner = await db.scalar(
            select(Partner).where(Partner.slug == partner_slug)
        )
        if partner is None:
            raise HTTPException(status_code=404, detail="Partner not found")
        stmt = stmt.where(PointLedger.partner_id == partner.id)

    rows = (
        await db.scalars(
            stmt.order_by(PointLedger.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
    ).all()
    return [LedgerEntryResponse.model_validate(r) for r in rows]


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
            .where(Membership.user_id == user.id)
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
            points_balance=m.user.points_balance,
            lifetime_earned=m.lifetime_earned,
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

    Với partner mà user đã là member, kèm `is_member=True`, `points_balance`
    (ví toàn cục), `current_tier_name` (theo shop). Dùng cho trang
    `/member/partners` để customer vừa khám phá shop vừa thấy hạng + điểm
    hiện tại trên card.
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
            .where(Membership.user_id == user.id)
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
                points_balance=user.points_balance,
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

    `points_balance` luôn = ví toàn cục của user (kể cả chưa join shop).
    `lifetime_earned` chỉ có khi user là member shop (per-shop tier metric).
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
        )
    )

    return PartnerDetailForMember(
        id=partner.id,
        name=partner.name,
        slug=partner.slug,
        category=str(partner.category.value if hasattr(partner.category, "value") else partner.category),
        description=partner.description,
        logo_url=partner.logo_url,
        banner_url=partner.banner_url,
        contact_phone=partner.contact_phone,
        contact_email=partner.contact_email,
        address=partner.address,
        website=partner.website,
        business_hours=partner.business_hours,
        is_member=membership is not None,
        points_balance=user.points_balance,
        lifetime_earned=membership.lifetime_earned if membership else None,
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
    """Rewards active của 1 partner. `user_points_balance` = ví toàn cục.

    Non-member: vẫn show balance global, nhưng can_redeem=False (phải join shop trước).
    """
    partner = await db.scalar(
        select(Partner).where(
            Partner.slug == slug, Partner.status == PartnerStatus.ACTIVE
        )
    )
    if partner is None:
        raise HTTPException(status_code=404, detail="Partner not found")

    is_member = await db.scalar(
        select(Membership.id).where(
            Membership.partner_id == partner.id,
            Membership.user_id == user.id,
        )
    ) is not None
    balance = user.points_balance

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


@users_router.get("/me/redemptions", response_model=MyRedemptionListResponse)
async def list_my_redemptions(
    status: str | None = Query(default=None, pattern="^(pending|used|expired)$"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> MyRedemptionListResponse:
    """List quà đã đổi của current user (toàn bộ shop)."""
    stmt = (
        select(Redemption, Partner.name.label("partner_name"), Reward.name.label("reward_name"), Reward.image_url.label("reward_image_url"))
        .join(Partner, Partner.id == Redemption.partner_id)
        .join(Reward, Reward.id == Redemption.reward_id)
        .where(Redemption.user_id == user.id)
    )
    if status:
        stmt = stmt.where(Redemption.status == status)

    total_stmt = select(func.count()).select_from(Redemption).where(Redemption.user_id == user.id)
    if status:
        total_stmt = total_stmt.where(Redemption.status == status)
    total = await db.scalar(total_stmt) or 0

    stmt = stmt.order_by(Redemption.redeemed_at.desc()).limit(limit).offset(offset)
    rows = (await db.execute(stmt)).all()
    items = [
        MyRedemptionListItem(
            id=r.Redemption.id,
            redemption_code=r.Redemption.redemption_code,
            points_spent=r.Redemption.points_spent,
            status=r.Redemption.status,
            redeemed_at=r.Redemption.redeemed_at,
            expires_at=r.Redemption.expires_at,
            used_at=r.Redemption.used_at,
            partner_id=r.Redemption.partner_id,
            partner_name=r.partner_name,
            reward_id=r.Redemption.reward_id,
            reward_name=r.reward_name,
            reward_image_url=r.reward_image_url,
        )
        for r in rows
    ]
    return MyRedemptionListResponse(items=items, total=total, limit=limit, offset=offset)


@users_router.get("/me/redemptions/{redemption_id}", response_model=MyRedemptionDetailResponse)
async def get_my_redemption(
    redemption_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> MyRedemptionDetailResponse:
    """Chi tiết 1 quà đã đổi (kèm QR code)."""
    stmt = (
        select(Redemption, Partner, Reward)
        .join(Partner, Partner.id == Redemption.partner_id)
        .join(Reward, Reward.id == Redemption.reward_id)
        .where(Redemption.id == redemption_id, Redemption.user_id == user.id)
    )
    row = (await db.execute(stmt)).one_or_none()
    if row is None:
        raise HTTPException(404, "Không tìm thấy quà đã đổi.")
    r, p, w = row
    return MyRedemptionDetailResponse(
        id=r.id,
        redemption_code=r.redemption_code,
        points_spent=r.points_spent,
        status=r.status,
        redeemed_at=r.redeemed_at,
        expires_at=r.expires_at,
        used_at=r.used_at,
        partner_id=p.id,
        partner_name=p.name,
        reward_id=w.id,
        reward_name=w.name,
        reward_image_url=w.image_url,
        snapshot_image_url=r.snapshot_image_url,
        reward_description=w.description,
        reward_terms=w.terms,
    )


@users_router.post(
    "/me/redemptions", response_model=RedemptionResponse, status_code=201
)
@limiter.limit("10/minute")
async def redeem_reward_self(
    request: Request,
    body: RedeemRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RedemptionResponse:
    """Customer tự đổi quà — derive partner từ reward, không cần X-Partner-Id.

    Yêu cầu user là member của partner sở hữu reward (membership tồn tại).
    """
    reward = await db.scalar(
        select(Reward).where(
            Reward.id == body.reward_id,
            Reward.deleted_at.is_(None),
            Reward.is_active.is_(True),
        )
    )
    if reward is None:
        raise HTTPException(status_code=404, detail="Reward not found")

    is_member = await db.scalar(
        select(Membership.id).where(
            Membership.partner_id == reward.partner_id,
            Membership.user_id == user.id,
        )
    )
    if is_member is None:
        raise HTTPException(
            status_code=403, detail="Bạn cần là thành viên của shop để đổi quà"
        )

    service = RedemptionService(db)
    try:
        redemption = await service.redeem(
            partner_id=reward.partner_id,
            user_id=user.id,
            reward_id=body.reward_id,
        )
    except InsufficientPointsError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except OutOfStockError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return RedemptionResponse.model_validate(redemption)


@users_router.get("/me/rewards")
async def list_my_rewards(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Rewards active của TẤT CẢ partner mà current user là member.

    `user_points_balance` = ví toàn cục (giống nhau ở mọi shop).
    """
    partner_rows = (
        await db.execute(
            select(Membership.partner_id, Partner.name, Partner.slug)
            .join(Partner, Membership.partner_id == Partner.id)
            .where(Membership.user_id == user.id)
        )
    ).all()
    if not partner_rows:
        return []

    partner_names = {pid: (name, slug) for pid, name, slug in partner_rows}
    partner_ids = list(partner_names.keys())
    balance = user.points_balance

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
            "user_points_balance": balance,
            "can_redeem": balance >= r.points_cost,
        }
        for r in rewards
    ]


@partners_router.get("/me", response_model=PartnerResponse)
async def get_my_partner(
    partner: Partner = Depends(require_owner_in_partner),
) -> PartnerResponse:
    """Lấy thông tin partner theo header X-Partner-Id. Yêu cầu là owner của partner."""
    if partner.status != PartnerStatus.ACTIVE:
        raise HTTPException(
            status_code=403,
            detail=f"Partner is {partner.status}, not active",
        )
    return PartnerResponse.model_validate(partner)


@partners_router.patch("/me", response_model=PartnerResponse)
async def update_my_partner(
    body: PartnerUpdateRequest,
    partner: Partner = Depends(require_owner_in_partner),
    db: AsyncSession = Depends(get_db),
) -> PartnerResponse:
    """Owner update thông tin shop (tên, mô tả, logo)."""
    service = PartnerService(db)
    try:
        updated = await service.update_partner(partner_id=partner.id, request=body)
    except PartnerNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return PartnerResponse.model_validate(updated)


# ==================== Staff management ====================

@partner_router.get("/staff")
async def list_partner_staff(
    is_active: str = Query(default="all", pattern="^(true|false|all)$"),
    partner: Partner = Depends(require_owner_in_partner),
    db: AsyncSession = Depends(get_db),
):
    """Owner xem danh sách nhân viên của shop."""
    from app.services.staff_service import StaffService

    svc = StaffService(db)
    result = await svc.list_staff(partner_id=partner.id, is_active=is_active)
    return result


@partner_router.post("/staff", status_code=201)
async def add_partner_staff(
    body: StaffCreateRequest,
    partner: Partner = Depends(require_owner_in_partner),
    db: AsyncSession = Depends(get_db),
):
    """Owner thêm nhân viên mới (tạo tài khoản + link vào shop)."""
    from app.services.staff_service import InvalidStaffError, StaffService

    svc = StaffService(db)
    try:
        return await svc.add_staff(partner_id=partner.id, req=body)
    except InvalidStaffError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e


@partner_router.patch("/staff/{user_id}")
async def toggle_partner_staff_active(
    user_id: int,
    body: StaffPatchRequest,
    partner: Partner = Depends(require_owner_in_partner),
    db: AsyncSession = Depends(get_db),
):
    """Owner bật/tắt is_active cho nhân viên."""
    from app.services.staff_service import InvalidStaffError, StaffService

    svc = StaffService(db)
    try:
        return await svc.toggle_active(partner_id=partner.id, user_id=user_id, req=body)
    except InvalidStaffError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@partner_router.post("/staff/{user_id}/reset-password")
async def reset_partner_staff_password(
    user_id: int,
    partner: Partner = Depends(require_owner_in_partner),
    db: AsyncSession = Depends(get_db),
):
    """Owner reset mật khẩu nhân viên. Trả về mật khẩu tạm + gửi email nếu có."""
    from app.services.email_service import EmailDeliveryError, EmailService
    from app.services.staff_service import InvalidStaffError, StaffService

    svc = StaffService(db)
    try:
        temp_password, user = await svc.reset_staff_password(
            partner_id=partner.id, user_id=user_id
        )
    except InvalidStaffError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    email_sent = False
    if user.email:
        try:
            email_svc = EmailService()
            await email_svc.send_email(
                to=user.email,
                subject="[Loyalty] Mật khẩu mới của bạn",
                body=(
                    f"Xin chào {user.full_name or 'bạn'},\n\n"
                    f"Mật khẩu tạm thời của bạn là: {temp_password}\n\n"
                    "Vui lòng đăng nhập và đổi mật khẩu ngay."
                ),
            )
            email_sent = True
        except EmailDeliveryError:
            logger.warning("Gửi email reset mật khẩu thất bại cho user %d", user_id)

    return {
        "email_sent": email_sent,
        "temp_password": temp_password,
        "message": "Đặt lại mật khẩu thành công." + (" Email đã được gửi." if email_sent else ""),
    }
