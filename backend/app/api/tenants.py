from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from fastapi import Query

from app.core.db import get_db
from app.core.deps import (
    get_current_user,
    get_tenant_id,
    require_owner_in_tenant,
    require_staff_in_tenant,
)
from app.core.limiter import limiter
from app.models.membership import Membership
from app.models.point_ledger import PointLedger
from app.models.reward import Reward
from app.models.tenant import Tenant, TenantStatus
from app.models.tenant_staff import TenantStaffRole
from app.models.user import User
from app.models.voucher import Voucher, VoucherStatus
from app.schemas.ledger import LedgerEntryResponse
from app.schemas.member import MemberResponse
from app.schemas.tenant import (
    TenantCreateRequest,
    TenantResponse,
    TenantStaffSummary,
    TenantUpdateRequest,
)
from app.schemas.voucher import VoucherResponse
from app.services.tenant_service import TenantNotFoundError, TenantService

merchant_router = APIRouter(prefix="/merchant", tags=["merchant"])
tenants_router = APIRouter(prefix="/tenants", tags=["tenants"])
users_router = APIRouter(prefix="/users", tags=["users"])


@merchant_router.post(
    "/register",
    response_model=TenantResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("3/minute")
async def register_tenant(
    request: Request,
    body: TenantCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TenantResponse:
    """Owner đăng ký doanh nghiệp mới (status=pending, chờ Super Admin duyệt)."""
    service = TenantService(db)
    tenant = await service.create_tenant(owner=current_user, request=body)
    return TenantResponse.model_validate(tenant)


@users_router.get("/me/tenants", response_model=list[TenantStaffSummary])
async def list_my_tenants(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[TenantStaffSummary]:
    """List tenant mà user là staff/owner. Frontend dùng để chọn tenant sau login."""
    service = TenantService(db)
    rows = await service.list_tenants_for_user(user_id=user.id)
    return [TenantStaffSummary.model_validate(row) for row in rows]


@users_router.get("/me/ledger", response_model=list[LedgerEntryResponse])
async def list_my_ledger(
    user: User = Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[LedgerEntryResponse]:
    """Lịch sử tích điểm của current user qua TẤT CẢ tenant họ tham gia.

    Dùng cho trang `/member/history` hiển thị timeline toàn bộ hoạt động
    tích điểm / đổi quà / điều chỉnh điểm.
    """
    # Lấy membership_ids của user
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


@users_router.get("/me/vouchers", response_model=list[VoucherResponse])
async def list_my_vouchers_all_tenants(
    user: User = Depends(get_current_user),
    status: VoucherStatus | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[VoucherResponse]:
    """Voucher của current user qua TẤT CẢ tenant họ là member.

    Dùng cho trang `/member/vouchers` hiển thị toàn bộ voucher (không chỉ 1 shop).
    """
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
    stmt = select(Voucher).where(Voucher.membership_id.in_(membership_ids))
    if status is not None:
        stmt = stmt.where(Voucher.status == status)
    stmt = stmt.order_by(Voucher.issued_at.desc())
    rows = (await db.scalars(stmt)).all()
    return [VoucherResponse.model_validate(v) for v in rows]


@users_router.get("/me/memberships", response_model=list[MemberResponse])
async def list_my_memberships(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MemberResponse]:
    """List tất cả membership của current user (các shop user đã tham gia).

    Customer-facing endpoint: dùng cho trang `/member` để hiển thị
    danh sách shop mình là thành viên + points balance per shop.
    """
    rows = (
        await db.scalars(
            select(Membership)
            .options(
                joinedload(Membership.user),
                joinedload(Membership.current_tier),
                joinedload(Membership.tenant),
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
        for m in rows
    ]


@users_router.get("/me/shops")
async def list_shops_for_discovery(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Tất cả shop ACTIVE trên platform + flag is_member/current_tier nếu user đã tham gia.

    Dùng cho trang `/member/shops` để customer khám phá và thấy shop nào đã là thành viên.
    """
    # Lấy membership của user map theo tenant_id
    from app.models.tier import Tier

    user_memberships = (
        await db.execute(
            select(Membership, Tier.name.label("tier_name"))
            .join(Tier, Membership.current_tier_id == Tier.id, isouter=True)
            .where(
                Membership.user_id == user.id,
                Membership.archived_at.is_(None),
            )
        )
    ).all()
    member_map = {
        m.tenant_id: {
            "points_balance": m.points_balance,
            "tier_name": tier_name,
        }
        for m, tier_name in user_memberships
    }

    # Tất cả tenant active
    tenants = (
        await db.scalars(
            select(Tenant)
            .where(Tenant.status == TenantStatus.ACTIVE)
            .order_by(Tenant.name.asc())
        )
    ).all()

    return [
        {
            "id": t.id,
            "name": t.name,
            "slug": t.slug,
            "category": t.category,
            "description": t.description,
            "logo_url": t.logo_url,
            "is_member": t.id in member_map,
            "points_balance": member_map.get(t.id, {}).get("points_balance"),
            "tier_name": member_map.get(t.id, {}).get("tier_name"),
        }
        for t in tenants
    ]


@users_router.get("/me/rewards")
async def list_my_rewards(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Rewards active của TẤT CẢ tenant mà current user là member.

    Dùng cho trang `/member/rewards` để customer thấy quà available cross-shop.
    Trả kèm points_balance của membership để frontend biết đủ điểm hay chưa.
    """
    memberships_rows = (
        await db.execute(
            select(Membership, Tenant.name, Tenant.slug)
            .join(Tenant, Membership.tenant_id == Tenant.id)
            .where(
                Membership.user_id == user.id,
                Membership.archived_at.is_(None),
            )
        )
    ).all()
    if not memberships_rows:
        return []

    tenant_points = {m.tenant_id: m.points_balance for m, _, _ in memberships_rows}
    tenant_names = {m.tenant_id: (name, slug) for m, name, slug in memberships_rows}
    tenant_ids = list(tenant_points.keys())

    rewards = (
        await db.scalars(
            select(Reward)
            .where(
                Reward.tenant_id.in_(tenant_ids),
                Reward.deleted_at.is_(None),
                Reward.is_active.is_(True),
            )
            .order_by(Reward.points_cost.asc())
        )
    ).all()

    return [
        {
            "id": r.id,
            "tenant_id": r.tenant_id,
            "tenant_name": tenant_names[r.tenant_id][0],
            "tenant_slug": tenant_names[r.tenant_id][1],
            "name": r.name,
            "description": r.description,
            "points_cost": r.points_cost,
            "stock": r.stock,
            "image_url": r.image_url,
            "user_points_balance": tenant_points[r.tenant_id],
            "can_redeem": tenant_points[r.tenant_id] >= r.points_cost,
        }
        for r in rewards
    ]


@tenants_router.get("/me", response_model=TenantResponse)
async def get_my_tenant(
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_staff_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> TenantResponse:
    """Lấy thông tin tenant theo header X-Tenant-Id. Yêu cầu là staff của tenant."""
    service = TenantService(db)
    try:
        tenant = await service.get_tenant_by_id(tenant_id)
    except TenantNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    if tenant.status != TenantStatus.ACTIVE:
        raise HTTPException(
            status_code=403,
            detail=f"Tenant is {tenant.status}, not active",
        )

    return TenantResponse.model_validate(tenant)


@tenants_router.patch("/me", response_model=TenantResponse)
async def update_my_tenant(
    body: TenantUpdateRequest,
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_owner_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> TenantResponse:
    """Owner update thông tin shop (tên, mô tả, logo)."""
    service = TenantService(db)
    try:
        tenant = await service.update_tenant(tenant_id=tenant_id, request=body)
    except TenantNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return TenantResponse.model_validate(tenant)


@merchant_router.get("/vouchers/check/{code}")
async def check_voucher_by_code(
    code: str,
    gross_amount: int = Query(default=0, ge=0),
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_staff_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Staff/owner check voucher code: trả info + tính discount preview cho gross_amount.

    Dùng ở POS form khi nhập mã voucher → hiển thị tên + giảm giá ngay.
    Không sử dụng (mark used) — chỉ preview.

    Toàn bộ logic ở `VoucherService.check_voucher_for_use` để reuse + dễ test.
    """
    from app.services.voucher_service import (
        VoucherExpiredError,
        VoucherInvalidStatusError,
        VoucherNotFoundError,
        VoucherService,
    )

    service = VoucherService(db)
    try:
        return await service.check_voucher_for_use(
            tenant_id=tenant_id,
            code=code,
            gross_amount=gross_amount,
        )
    except VoucherNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except (VoucherInvalidStatusError, VoucherExpiredError) as e:
        raise HTTPException(status_code=409, detail=str(e)) from e


@merchant_router.get("/vouchers", response_model=list[VoucherResponse])
async def list_tenant_vouchers(
    vstatus: VoucherStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_owner_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> list[VoucherResponse]:
    """Merchant xem tất cả voucher đã phát cho tenant này."""
    stmt = (
        select(Voucher)
        .options(joinedload(Voucher.campaign))
        .where(Voucher.tenant_id == tenant_id)
        .order_by(Voucher.issued_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if vstatus is not None:
        stmt = stmt.where(Voucher.status == vstatus)
    rows = (await db.scalars(stmt)).all()
    return [
        VoucherResponse(
            id=v.id,
            tenant_id=v.tenant_id,
            campaign_id=v.campaign_id,
            membership_id=v.membership_id,
            code=v.code,
            status=v.status,
            issued_at=v.issued_at,
            used_at=v.used_at,
            expires_at=v.expires_at,
            campaign_name=v.campaign.name if v.campaign else None,
            discount_type=(
                v.campaign.discount_type.value
                if v.campaign and hasattr(v.campaign.discount_type, "value")
                else None
            ),
            discount_value=v.campaign.discount_value if v.campaign else None,
        )
        for v in rows
    ]
