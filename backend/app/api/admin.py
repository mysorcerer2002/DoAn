import secrets
import string
from datetime import UTC, datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_db
from app.core.deps import require_super_admin
from app.core.security import hash_password
from app.models.campaign import Campaign
from app.models.membership import Membership
from app.models.redemption import Redemption
from app.models.reward import Reward
from app.models.tenant import Tenant, TenantStatus
from app.models.tenant_staff import TenantStaff
from app.models.tier import Tier
from app.models.transaction import Transaction
from app.models.user import User
from app.models.voucher import Voucher
from app.schemas.analytics import (
    AdminTenantListRow,
    AdminTenantMemberRow,
    AdminTenantStaffRow,
    PlatformStatsResponse,
    TenantDetailResponse,
)
from app.schemas.ledger import ReconcileResponse
from app.schemas.tenant import TenantApprovalRequest, TenantResponse
from app.services.ledger_service import LedgerService
from app.services.tenant_service import (
    InvalidStatusTransitionError,
    TenantNotFoundError,
    TenantService,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/tenants", response_model=list[AdminTenantListRow])
async def list_tenants(
    tenant_status: TenantStatus | None = Query(default=None, alias="status"),
    _admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> list[AdminTenantListRow]:
    """Super Admin xem danh sách tenant kèm metric tổng quan + thông tin owner."""
    member_count_sq = (
        select(
            Membership.tenant_id.label("tenant_id"),
            func.count().label("cnt"),
        )
        .where(Membership.archived_at.is_(None))
        .group_by(Membership.tenant_id)
        .subquery()
    )
    staff_count_sq = (
        select(
            TenantStaff.tenant_id.label("tenant_id"),
            func.count().label("cnt"),
        )
        .group_by(TenantStaff.tenant_id)
        .subquery()
    )
    # Khách hoạt động 30 ngày: số membership distinct có giao dịch trong 30 ngày gần nhất
    since_30d = datetime.now(UTC) - timedelta(days=30)
    active_30d_sq = (
        select(
            Transaction.tenant_id.label("tenant_id"),
            func.count(func.distinct(Transaction.membership_id)).label("cnt"),
        )
        .where(Transaction.created_at >= since_30d)
        .group_by(Transaction.tenant_id)
        .subquery()
    )

    stmt = (
        select(
            Tenant,
            User.full_name.label("owner_name"),
            User.email.label("owner_email"),
            func.coalesce(member_count_sq.c.cnt, 0).label("member_count"),
            func.coalesce(staff_count_sq.c.cnt, 0).label("staff_count"),
            func.coalesce(active_30d_sq.c.cnt, 0).label("active_30d_count"),
        )
        .join(User, User.id == Tenant.owner_user_id)
        .outerjoin(member_count_sq, member_count_sq.c.tenant_id == Tenant.id)
        .outerjoin(staff_count_sq, staff_count_sq.c.tenant_id == Tenant.id)
        .outerjoin(active_30d_sq, active_30d_sq.c.tenant_id == Tenant.id)
        .order_by(Tenant.created_at.desc())
    )
    if tenant_status is not None:
        stmt = stmt.where(Tenant.status == tenant_status)

    rows = (await db.execute(stmt)).all()
    return [
        AdminTenantListRow(
            id=t.id,
            name=t.name,
            slug=t.slug,
            status=str(t.status.value if hasattr(t.status, "value") else t.status),
            category=str(
                t.category.value if hasattr(t.category, "value") else t.category
            ),
            logo_url=t.logo_url,
            contact_phone=t.contact_phone,
            contact_email=t.contact_email,
            created_at=t.created_at,
            activated_at=t.activated_at,
            owner_id=t.owner_user_id,
            owner_name=owner_name,
            owner_email=owner_email,
            member_count=int(mc),
            active_member_count_30d=int(a30),
            staff_count=int(sc),
        )
        for t, owner_name, owner_email, mc, sc, a30 in rows
    ]


@router.post("/tenants/{tenant_id}/approve", response_model=TenantResponse)
async def approve_tenant(
    tenant_id: int,
    body: TenantApprovalRequest,
    _admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> TenantResponse:
    """Super Admin approve/reject tenant.

    `approve=true` → ACTIVE (chỉ từ PENDING/SUSPENDED).
    `approve=false` → SUSPENDED (chỉ từ PENDING/ACTIVE).
    Trả 409 nếu transition không hợp lệ.
    """
    service = TenantService(db)
    try:
        if body.approve:
            tenant = await service.approve_tenant(tenant_id=tenant_id)
        else:
            tenant = await service.suspend_tenant(tenant_id=tenant_id)
    except TenantNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except InvalidStatusTransitionError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    return TenantResponse.model_validate(tenant)


@router.post(
    "/reconcile/{membership_id}",
    response_model=ReconcileResponse,
    status_code=status.HTTP_200_OK,
)
async def reconcile_member_balance(
    membership_id: int,
    _admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> ReconcileResponse:
    """Super Admin kiểm tra tính nhất quán giữa points_balance và ledger."""
    membership = await db.get(Membership, membership_id)
    if membership is None:
        raise HTTPException(status_code=404, detail="Membership không tồn tại")
    service = LedgerService(db)
    return await service.reconcile(
        tenant_id=membership.tenant_id, membership_id=membership_id
    )


@router.get("/tenants/{tenant_id}/detail", response_model=TenantDetailResponse)
async def get_tenant_detail(
    tenant_id: int,
    _admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> TenantDetailResponse:
    """Super Admin xem chi tiết tenant kèm đầy đủ thống kê."""
    service = TenantService(db)
    try:
        tenant = await service.get_tenant_by_id(tenant_id)
    except TenantNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    owner = await db.get(User, tenant.owner_user_id)

    total_member_count = int(
        await db.scalar(
            select(func.count()).select_from(Membership).where(
                Membership.tenant_id == tenant_id
            )
        )
        or 0
    )
    active_member_count = int(
        await db.scalar(
            select(func.count())
            .select_from(Membership)
            .where(
                Membership.tenant_id == tenant_id,
                Membership.archived_at.is_(None),
            )
        )
        or 0
    )
    staff_count = int(
        await db.scalar(
            select(func.count()).select_from(TenantStaff).where(
                TenantStaff.tenant_id == tenant_id
            )
        )
        or 0
    )
    txn_row = (
        await db.execute(
            select(
                func.count(Transaction.id),
                func.coalesce(func.sum(Transaction.net_amount), 0),
            ).where(Transaction.tenant_id == tenant_id)
        )
    ).one()
    txn_count, total_revenue = txn_row

    campaign_count = int(
        await db.scalar(
            select(func.count()).select_from(Campaign).where(
                Campaign.tenant_id == tenant_id,
                Campaign.deleted_at.is_(None),
            )
        )
        or 0
    )
    active_campaign_count = int(
        await db.scalar(
            select(func.count()).select_from(Campaign).where(
                Campaign.tenant_id == tenant_id,
                Campaign.deleted_at.is_(None),
                Campaign.is_active.is_(True),
            )
        )
        or 0
    )
    voucher_count = int(
        await db.scalar(
            select(func.count()).select_from(Voucher).where(
                Voucher.tenant_id == tenant_id
            )
        )
        or 0
    )
    redemption_count = int(
        await db.scalar(
            select(func.count()).select_from(Redemption).where(
                Redemption.tenant_id == tenant_id
            )
        )
        or 0
    )
    reward_count = int(
        await db.scalar(
            select(func.count()).select_from(Reward).where(
                Reward.tenant_id == tenant_id,
                Reward.deleted_at.is_(None),
            )
        )
        or 0
    )

    status_val = (
        tenant.status.value if hasattr(tenant.status, "value") else tenant.status
    )
    category_val = (
        tenant.category.value
        if hasattr(tenant.category, "value")
        else tenant.category
    )

    return TenantDetailResponse(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        status=str(status_val),
        category=str(category_val),
        description=tenant.description,
        logo_url=tenant.logo_url,
        contact_phone=tenant.contact_phone,
        contact_email=tenant.contact_email,
        address=tenant.address,
        tax_code=tenant.tax_code,
        website=tenant.website,
        business_hours=tenant.business_hours,
        created_at=tenant.created_at,
        activated_at=tenant.activated_at,
        owner_id=tenant.owner_user_id,
        owner_name=owner.full_name if owner else None,
        owner_email=owner.email if owner else None,
        owner_phone=owner.phone if owner else None,
        member_count=total_member_count,
        active_member_count=active_member_count,
        staff_count=staff_count,
        transaction_count=int(txn_count),
        total_revenue=int(total_revenue),
        campaign_count=campaign_count,
        active_campaign_count=active_campaign_count,
        voucher_count=voucher_count,
        redemption_count=redemption_count,
        reward_count=reward_count,
    )


@router.get(
    "/tenants/{tenant_id}/staff", response_model=list[AdminTenantStaffRow]
)
async def list_tenant_staff(
    tenant_id: int,
    _admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> list[AdminTenantStaffRow]:
    """Super Admin xem danh sách nhân viên (gồm owner) của tenant."""
    tenant = await db.get(Tenant, tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant không tồn tại")

    rows = (
        await db.execute(
            select(TenantStaff, User)
            .join(User, User.id == TenantStaff.user_id)
            .where(TenantStaff.tenant_id == tenant_id)
            .order_by(TenantStaff.added_at)
        )
    ).all()
    return [
        AdminTenantStaffRow(
            user_id=u.id,
            full_name=u.full_name,
            email=u.email,
            phone=u.phone,
            role=str(ts.role.value if hasattr(ts.role, "value") else ts.role),
            added_at=ts.added_at,
            is_active=u.is_active,
        )
        for ts, u in rows
    ]


@router.get(
    "/tenants/{tenant_id}/members", response_model=list[AdminTenantMemberRow]
)
async def list_tenant_members(
    tenant_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> list[AdminTenantMemberRow]:
    """Super Admin xem danh sách khách hàng của tenant."""
    tenant = await db.get(Tenant, tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant không tồn tại")

    rows = (
        await db.execute(
            select(Membership, User, Tier.name)
            .join(User, User.id == Membership.user_id)
            .outerjoin(Tier, Tier.id == Membership.current_tier_id)
            .where(Membership.tenant_id == tenant_id)
            .order_by(Membership.joined_at.desc())
            .limit(limit)
            .offset(offset)
        )
    ).all()
    return [
        AdminTenantMemberRow(
            membership_id=m.id,
            user_id=u.id,
            full_name=u.full_name,
            email=u.email,
            phone=u.phone,
            points_balance=m.points_balance,
            total_points_earned=m.total_points_earned,
            current_tier_name=tier_name,
            joined_at=m.joined_at,
            archived=m.archived_at is not None,
        )
        for m, u, tier_name in rows
    ]


@router.post("/tenants/{tenant_id}/suspend", response_model=TenantResponse)
async def suspend_tenant(
    tenant_id: int,
    _admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> TenantResponse:
    """Super Admin suspend một tenant."""
    service = TenantService(db)
    try:
        tenant = await service.suspend_tenant(tenant_id=tenant_id)
    except TenantNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except InvalidStatusTransitionError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    return TenantResponse.model_validate(tenant)


class AdminUserRow(BaseModel):
    id: int
    email: str | None
    phone: str | None
    full_name: str | None
    system_role: str
    is_active: bool
    is_shadow: bool
    created_at: datetime
    last_login_at: datetime | None

    model_config = {"from_attributes": True}


class AdminUserListResponse(BaseModel):
    total: int
    items: list[AdminUserRow]


class AuditFeedItem(BaseModel):
    event_type: str  # tenant_approved | transaction | user_registered
    title: str
    description: str
    at: datetime
    tenant_name: str | None = None


class AdminSettingsResponse(BaseModel):
    environment: str
    debug: bool
    jwt_expire_minutes: int
    refresh_expire_days: int
    scheduler_enabled: bool
    allowed_origins: list[str]
    app_name: str


@router.get("/users", response_model=AdminUserListResponse)
async def list_platform_users(
    q: str | None = Query(default=None, max_length=100),
    role: str | None = Query(default=None, pattern="^(regular|admin|super_admin)$"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminUserListResponse:
    """Super Admin xem danh sách user toàn platform."""
    stmt = select(User).where(User.is_shadow.is_(False))
    count_stmt = select(func.count()).select_from(User).where(User.is_shadow.is_(False))

    if role:
        stmt = stmt.where(User.system_role == role)
        count_stmt = count_stmt.where(User.system_role == role)

    if q:
        like = f"%{q.strip().lower()}%"
        stmt = stmt.where(
            (func.lower(User.email).like(like))
            | (func.lower(User.full_name).like(like))
            | (User.phone.like(f"%{q.strip()}%"))
        )
        count_stmt = count_stmt.where(
            (func.lower(User.email).like(like))
            | (func.lower(User.full_name).like(like))
            | (User.phone.like(f"%{q.strip()}%"))
        )

    total = int(await db.scalar(count_stmt) or 0)
    stmt = stmt.order_by(User.created_at.desc()).limit(limit).offset(offset)
    users = (await db.scalars(stmt)).all()

    return AdminUserListResponse(
        total=total,
        items=[AdminUserRow.model_validate(u) for u in users],
    )


@router.get("/audit-feed", response_model=list[AuditFeedItem])
async def get_audit_feed(
    limit: int = Query(default=30, ge=1, le=100),
    _admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> list[AuditFeedItem]:
    """Feed hoạt động gần đây trên platform (tenant approval, giao dịch lớn, đăng ký)."""
    items: list[AuditFeedItem] = []

    # Tenants vừa approved/pending
    recent_tenants = (
        await db.execute(
            select(Tenant)
            .order_by(Tenant.created_at.desc())
            .limit(10)
        )
    ).scalars().all()
    for t in recent_tenants:
        event_type = "tenant_created"
        title = f"Tenant mới: {t.name}"
        if t.status == TenantStatus.ACTIVE:
            event_type = "tenant_approved"
            title = f"Tenant đã duyệt: {t.name}"
        elif t.status == TenantStatus.SUSPENDED:
            event_type = "tenant_suspended"
            title = f"Tenant bị đình chỉ: {t.name}"
        items.append(
            AuditFeedItem(
                event_type=event_type,
                title=title,
                description=(t.description or "")[:120],
                at=t.activated_at or t.created_at,
                tenant_name=t.name,
            )
        )

    # User đăng ký mới
    recent_users = (
        await db.execute(
            select(User)
            .where(User.is_shadow.is_(False))
            .order_by(User.created_at.desc())
            .limit(10)
        )
    ).scalars().all()
    for u in recent_users:
        items.append(
            AuditFeedItem(
                event_type="user_registered",
                title=f"Đăng ký: {u.full_name or u.email or u.phone or f'User #{u.id}'}",
                description=u.email or u.phone or "",
                at=u.created_at,
            )
        )

    # Giao dịch gần đây (join tenant để lấy tên)
    recent_txns = (
        await db.execute(
            select(Transaction, Tenant.name)
            .join(Tenant, Transaction.tenant_id == Tenant.id)
            .order_by(Transaction.created_at.desc())
            .limit(10)
        )
    ).all()
    for txn, tenant_name in recent_txns:
        items.append(
            AuditFeedItem(
                event_type="transaction",
                title=f"Giao dịch {txn.net_amount:,}₫ tại {tenant_name}",
                description=f"#{txn.id} — {txn.points_earned} điểm",
                at=txn.created_at,
                tenant_name=tenant_name,
            )
        )

    items.sort(key=lambda x: x.at, reverse=True)
    return items[:limit]


@router.get("/settings", response_model=AdminSettingsResponse)
async def get_admin_settings(
    _admin: User = Depends(require_super_admin),
) -> AdminSettingsResponse:
    """Super Admin xem config toàn platform (readonly)."""
    s = get_settings()
    return AdminSettingsResponse(
        environment=s.environment,
        debug=s.debug,
        jwt_expire_minutes=s.access_token_expire_minutes,
        refresh_expire_days=s.refresh_token_expire_days,
        scheduler_enabled=s.enable_scheduler,
        allowed_origins=s.cors_origins,
        app_name=s.app_name,
    )


class AdminMembershipInfo(BaseModel):
    tenant_id: int
    tenant_name: str
    tenant_slug: str
    points_balance: int
    total_points_earned: int
    current_tier_name: str | None
    joined_at: datetime
    archived: bool


class AdminUserDetailResponse(BaseModel):
    id: int
    email: str | None
    phone: str | None
    full_name: str | None
    system_role: str
    is_active: bool
    is_shadow: bool
    created_at: datetime
    last_login_at: datetime | None
    password_changed_at: datetime | None
    memberships: list[AdminMembershipInfo]


class AdminUserUpdateRequest(BaseModel):
    is_active: bool | None = None
    system_role: Literal["regular", "admin", "super_admin"] | None = None


class AdminResetPasswordResponse(BaseModel):
    user_id: int
    temporary_password: str


def _generate_temp_password(length: int = 12) -> str:
    """Sinh mật khẩu ngẫu nhiên dễ đọc (chữ + số, không ký tự đặc biệt)."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


async def _count_active_super_admins(db: AsyncSession) -> int:
    return int(
        await db.scalar(
            select(func.count())
            .select_from(User)
            .where(
                User.system_role == "super_admin",
                User.is_active.is_(True),
                User.is_shadow.is_(False),
            )
        )
        or 0
    )


@router.get("/users/{user_id}", response_model=AdminUserDetailResponse)
async def get_user_detail(
    user_id: int,
    _admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminUserDetailResponse:
    """Super Admin xem chi tiết user + danh sách membership."""
    target = await db.get(User, user_id)
    if target is None or target.is_shadow:
        raise HTTPException(status_code=404, detail="Người dùng không tồn tại")

    rows = (
        await db.execute(
            select(Membership, Tenant, Tier.name)
            .join(Tenant, Membership.tenant_id == Tenant.id)
            .outerjoin(Tier, Membership.current_tier_id == Tier.id)
            .where(Membership.user_id == user_id)
            .order_by(Membership.joined_at.desc())
        )
    ).all()

    memberships = [
        AdminMembershipInfo(
            tenant_id=t.id,
            tenant_name=t.name,
            tenant_slug=t.slug,
            points_balance=m.points_balance,
            total_points_earned=m.total_points_earned,
            current_tier_name=tier_name,
            joined_at=m.joined_at,
            archived=m.archived_at is not None,
        )
        for m, t, tier_name in rows
    ]

    return AdminUserDetailResponse(
        id=target.id,
        email=target.email,
        phone=target.phone,
        full_name=target.full_name,
        system_role=target.system_role,
        is_active=target.is_active,
        is_shadow=target.is_shadow,
        created_at=target.created_at,
        last_login_at=target.last_login_at,
        password_changed_at=target.password_changed_at,
        memberships=memberships,
    )


@router.patch("/users/{user_id}", response_model=AdminUserDetailResponse)
async def update_user(
    user_id: int,
    body: AdminUserUpdateRequest,
    admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminUserDetailResponse:
    """Super Admin cập nhật is_active hoặc system_role của user.

    - Không cho phép tự khoá/tự đổi role của chính mình.
    - Không cho phép demote hoặc deactivate super_admin cuối cùng của platform.
    """
    if body.is_active is None and body.system_role is None:
        raise HTTPException(status_code=400, detail="Không có trường nào để cập nhật")

    target = await db.get(User, user_id)
    if target is None or target.is_shadow:
        raise HTTPException(status_code=404, detail="Người dùng không tồn tại")

    if target.id == admin.id:
        raise HTTPException(
            status_code=409,
            detail="Không thể chỉnh sửa trạng thái hoặc vai trò của chính mình",
        )

    demoting_super = (
        body.system_role is not None
        and target.system_role == "super_admin"
        and body.system_role != "super_admin"
    )
    deactivating_super = (
        body.is_active is False
        and target.system_role == "super_admin"
        and target.is_active
    )
    if demoting_super or deactivating_super:
        active_supers = await _count_active_super_admins(db)
        if active_supers <= 1:
            raise HTTPException(
                status_code=409,
                detail="Không thể hạ cấp/khoá super admin cuối cùng của hệ thống",
            )

    if body.is_active is not None:
        target.is_active = body.is_active
    if body.system_role is not None:
        target.system_role = body.system_role

    await db.commit()
    await db.refresh(target)

    return await get_user_detail(user_id=target.id, _admin=admin, db=db)


@router.post(
    "/users/{user_id}/reset-password", response_model=AdminResetPasswordResponse
)
async def reset_user_password(
    user_id: int,
    admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminResetPasswordResponse:
    """Super Admin reset mật khẩu user, trả mật khẩu tạm thời để chuyển cho user."""
    target = await db.get(User, user_id)
    if target is None or target.is_shadow:
        raise HTTPException(status_code=404, detail="Người dùng không tồn tại")

    if target.id == admin.id:
        raise HTTPException(
            status_code=409,
            detail="Không thể reset mật khẩu của chính mình qua trang admin",
        )

    temp_password = _generate_temp_password()
    target.password_hash = hash_password(temp_password)
    target.password_changed_at = datetime.now(tz=UTC)
    await db.commit()

    return AdminResetPasswordResponse(
        user_id=target.id, temporary_password=temp_password
    )


@router.get("/stats", response_model=PlatformStatsResponse)
async def get_platform_stats(
    _admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> PlatformStatsResponse:
    """Thống kê toàn platform cho super admin."""
    tenants_count = await db.scalar(
        select(func.count()).select_from(Tenant)
    )
    users_count = await db.scalar(
        select(func.count()).select_from(User)
    )
    txn_count = await db.scalar(
        select(func.count()).select_from(Transaction)
    )
    return PlatformStatsResponse(
        total_tenants=int(tenants_count or 0),
        total_users=int(users_count or 0),
        total_transactions=int(txn_count or 0),
    )
