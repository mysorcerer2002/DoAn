import logging
import secrets
import string
from datetime import UTC, datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.core.config import get_settings
from app.core.db import get_db
from app.core.deps import require_super_admin
from app.core.security import hash_password
from app.models.login_log import LoginLog
from app.models.membership import Membership
from app.models.point_ledger import LedgerReason, PointLedger
from app.models.redemption import Redemption
from app.models.reward import Reward
from app.models.partner import Partner, PartnerStatus
from app.models.tier import Tier
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.admin import (
    PartnerEarnedItem,
    PointAdjustmentListResponse,
    PointAdjustmentResponse,
    PointsSummaryResponse,
)
from app.schemas.analytics import (
    AdminPartnerListRow,
    AdminPartnerMemberRow,
    AdminPartnerStaffRow,
    PlatformStatsResponse,
    PartnerDetailResponse,
)
from app.schemas.ledger import ReconcileResponse
from app.schemas.login_log import LoginLogListResponse, LoginLogResponse
from app.schemas.partner import PartnerApprovalRequest, PartnerResponse
from app.core.exceptions import EmailDeliveryError
from app.services.email_service import EmailService
from app.services.ledger_service import LedgerService
from app.services.partner_service import (
    InvalidStatusTransitionError,
    PartnerNotFoundError,
    PartnerService,
)

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)


@router.get("/partners", response_model=list[AdminPartnerListRow])
async def list_all_partners(
    partner_status: PartnerStatus | None = Query(default=None, alias="status"),
    _admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> list[AdminPartnerListRow]:
    """Super Admin xem danh sách partner kèm metric tổng quan + thông tin owner."""
    active_member_count_sq = (
        select(
            Membership.partner_id.label("partner_id"),
            func.count().label("cnt"),
        )
        .group_by(Membership.partner_id)
        .subquery()
    )
    # Khách hoạt động 30 ngày: số membership distinct có giao dịch trong 30 ngày gần nhất
    since_30d = datetime.now(UTC) - timedelta(days=30)
    active_30d_sq = (
        select(
            Transaction.partner_id.label("partner_id"),
            func.count(func.distinct(Transaction.membership_id)).label("cnt"),
        )
        .where(Transaction.created_at >= since_30d)
        .group_by(Transaction.partner_id)
        .subquery()
    )

    stmt = (
        select(
            Partner,
            User.full_name.label("owner_name"),
            User.email.label("owner_email"),
            func.coalesce(active_member_count_sq.c.cnt, 0).label("active_member_count"),
            func.coalesce(active_30d_sq.c.cnt, 0).label("active_30d_count"),
        )
        .join(User, User.id == Partner.owner_user_id)
        .outerjoin(active_member_count_sq, active_member_count_sq.c.partner_id == Partner.id)
        .outerjoin(active_30d_sq, active_30d_sq.c.partner_id == Partner.id)
        .order_by(Partner.created_at.desc())
    )
    if partner_status is not None:
        stmt = stmt.where(Partner.status == partner_status)

    rows = (await db.execute(stmt)).all()
    return [
        AdminPartnerListRow(
            id=p.id,
            name=p.name,
            slug=p.slug,
            status=str(p.status.value if hasattr(p.status, "value") else p.status),
            category=str(
                p.category.value if hasattr(p.category, "value") else p.category
            ),
            logo_url=p.logo_url,
            contact_phone=p.contact_phone,
            contact_email=p.contact_email,
            created_at=p.created_at,
            activated_at=p.activated_at,
            owner_id=p.owner_user_id,
            owner_name=owner_name,
            owner_email=owner_email,
            active_member_count=int(mc),
            active_member_count_30d=int(a30),
        )
        for p, owner_name, owner_email, mc, a30 in rows
    ]


@router.post("/partners/{partner_id}/approve", response_model=PartnerResponse)
async def approve_partner(
    partner_id: int,
    body: PartnerApprovalRequest,
    _admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> PartnerResponse:
    """Super Admin approve/reject partner.

    `approve=true` → ACTIVE (chỉ từ PENDING/SUSPENDED).
    `approve=false` → SUSPENDED (chỉ từ PENDING/ACTIVE).
    Trả 409 nếu transition không hợp lệ.
    """
    service = PartnerService(db)
    try:
        if body.approve:
            partner = await service.approve_partner(partner_id=partner_id)
        else:
            partner = await service.suspend_partner(partner_id=partner_id)
    except PartnerNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except InvalidStatusTransitionError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    return PartnerResponse.model_validate(partner)


@router.post(
    "/reconcile/{user_id}",
    response_model=ReconcileResponse,
    status_code=status.HTTP_200_OK,
)
async def reconcile_user_balance(
    user_id: int,
    _admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> ReconcileResponse:
    """Super Admin so khớp users.points_balance vs SUM(point_ledger.delta) global."""
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User không tồn tại")
    service = LedgerService(db)
    return await service.reconcile(user_id=user_id)


@router.get("/partners/{partner_id}/detail", response_model=PartnerDetailResponse)
async def get_partner_detail(
    partner_id: int,
    _admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> PartnerDetailResponse:
    """Super Admin xem chi tiết partner kèm đầy đủ thống kê."""
    service = PartnerService(db)
    try:
        partner = await service.get_partner_by_id(partner_id)
    except PartnerNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    owner = await db.get(User, partner.owner_user_id)

    total_member_count = int(
        await db.scalar(
            select(func.count()).select_from(Membership).where(
                Membership.partner_id == partner_id
            )
        )
        or 0
    )
    active_member_count = int(
        await db.scalar(
            select(func.count())
            .select_from(Membership)
            .where(Membership.partner_id == partner_id)
        )
        or 0
    )
    txn_row = (
        await db.execute(
            select(
                func.count(Transaction.id),
                func.coalesce(func.sum(Transaction.net_amount), 0),
            ).where(Transaction.partner_id == partner_id)
        )
    ).one()
    txn_count, total_revenue = txn_row

    redemption_count = int(
        await db.scalar(
            select(func.count()).select_from(Redemption).where(
                Redemption.partner_id == partner_id
            )
        )
        or 0
    )
    reward_count = int(
        await db.scalar(
            select(func.count()).select_from(Reward).where(
                Reward.partner_id == partner_id,
                Reward.deleted_at.is_(None),
            )
        )
        or 0
    )

    status_val = (
        partner.status.value if hasattr(partner.status, "value") else partner.status
    )
    category_val = (
        partner.category.value
        if hasattr(partner.category, "value")
        else partner.category
    )

    return PartnerDetailResponse(
        id=partner.id,
        name=partner.name,
        slug=partner.slug,
        status=str(status_val),
        category=str(category_val),
        description=partner.description,
        logo_url=partner.logo_url,
        contact_phone=partner.contact_phone,
        contact_email=partner.contact_email,
        address=partner.address,
        tax_code=partner.tax_code,
        website=partner.website,
        business_hours=partner.business_hours,
        created_at=partner.created_at,
        activated_at=partner.activated_at,
        owner_id=partner.owner_user_id,
        owner_name=owner.full_name if owner else None,
        owner_email=owner.email if owner else None,
        owner_phone=owner.phone if owner else None,
        member_count=total_member_count,
        active_member_count=active_member_count,
        transaction_count=int(txn_count),
        total_revenue=int(total_revenue),
        redemption_count=redemption_count,
        reward_count=reward_count,
    )


@router.get(
    "/partners/{partner_id}/staff", response_model=list[AdminPartnerStaffRow]
)
async def list_partner_staff(
    partner_id: int,
    _admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> list[AdminPartnerStaffRow]:
    """Super Admin xem owner của partner. MVP final: 1 owner / shop, không có staff."""
    partner = await db.get(Partner, partner_id)
    if partner is None:
        raise HTTPException(status_code=404, detail="Partner không tồn tại")

    owner = await db.get(User, partner.owner_user_id)
    if owner is None:
        return []
    return [
        AdminPartnerStaffRow(
            user_id=owner.id,
            full_name=owner.full_name,
            email=owner.email,
            phone=owner.phone,
            role="owner",
            added_at=partner.created_at,
            is_active=owner.is_active,
        )
    ]


@router.get(
    "/partners/{partner_id}/members", response_model=list[AdminPartnerMemberRow]
)
async def list_partner_members(
    partner_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> list[AdminPartnerMemberRow]:
    """Super Admin xem danh sách khách hàng của partner."""
    partner = await db.get(Partner, partner_id)
    if partner is None:
        raise HTTPException(status_code=404, detail="Partner không tồn tại")

    rows = (
        await db.execute(
            select(Membership, User, Tier.name)
            .join(User, User.id == Membership.user_id)
            .outerjoin(Tier, Tier.id == Membership.current_tier_id)
            .where(Membership.partner_id == partner_id)
            .order_by(Membership.joined_at.desc())
            .limit(limit)
            .offset(offset)
        )
    ).all()
    return [
        AdminPartnerMemberRow(
            membership_id=m.id,
            user_id=u.id,
            full_name=u.full_name,
            email=u.email,
            phone=u.phone,
            points_balance=u.points_balance,
            lifetime_earned=m.lifetime_earned,
            current_tier_name=tier_name,
            joined_at=m.joined_at,
        )
        for m, u, tier_name in rows
    ]


@router.post("/partners/{partner_id}/suspend", response_model=PartnerResponse)
async def suspend_partner(
    partner_id: int,
    _admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> PartnerResponse:
    """Super Admin suspend một partner."""
    service = PartnerService(db)
    try:
        partner = await service.suspend_partner(partner_id=partner_id)
    except PartnerNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except InvalidStatusTransitionError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    return PartnerResponse.model_validate(partner)


class AdminUserRow(BaseModel):
    id: int
    email: str | None
    phone: str | None
    full_name: str | None
    system_role: str
    is_active: bool
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
    stmt = select(User)
    count_stmt = select(func.count()).select_from(User)

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

    # Partners vừa approved/pending
    recent_partners = (
        await db.execute(
            select(Partner)
            .order_by(Partner.created_at.desc())
            .limit(10)
        )
    ).scalars().all()
    for p in recent_partners:
        event_type = "partner_created"
        title = f"Partner mới: {p.name}"
        if p.status == PartnerStatus.ACTIVE:
            event_type = "partner_approved"
            title = f"Partner đã duyệt: {p.name}"
        elif p.status == PartnerStatus.SUSPENDED:
            event_type = "partner_suspended"
            title = f"Partner bị đình chỉ: {p.name}"
        items.append(
            AuditFeedItem(
                event_type=event_type,
                title=title,
                description=(p.description or "")[:120],
                at=p.activated_at or p.created_at,
                tenant_name=p.name,
            )
        )

    # User đăng ký mới
    recent_users = (
        await db.execute(
            select(User)
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

    # Giao dịch gần đây (join partner để lấy tên)
    recent_txns = (
        await db.execute(
            select(Transaction, Partner.name)
            .join(Partner, Transaction.partner_id == Partner.id)
            .order_by(Transaction.created_at.desc())
            .limit(10)
        )
    ).all()
    for txn, partner_name in recent_txns:
        items.append(
            AuditFeedItem(
                event_type="transaction",
                title=f"Giao dịch {txn.net_amount:,}₫ tại {partner_name}",
                description=f"#{txn.id} — {txn.points_earned} điểm",
                at=txn.created_at,
                tenant_name=partner_name,
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
    partner_id: int
    partner_name: str
    partner_slug: str
    lifetime_earned: int  # Per-shop tier metric. Ví toàn cục = user.points_balance.
    current_tier_name: str | None
    joined_at: datetime


class AdminUserDetailResponse(BaseModel):
    id: int
    email: str | None
    phone: str | None
    full_name: str | None
    system_role: str
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None
    memberships: list[AdminMembershipInfo]


class AdminUserUpdateRequest(BaseModel):
    is_active: bool | None = None
    system_role: Literal["regular", "admin", "super_admin"] | None = None


class AdminResetPasswordResponse(BaseModel):
    user_id: int
    temporary_password: str
    email_sent: bool = False
    user_email: str | None = None


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
    if target is None:
        raise HTTPException(status_code=404, detail="Người dùng không tồn tại")

    rows = (
        await db.execute(
            select(Membership, Partner, Tier.name)
            .join(Partner, Membership.partner_id == Partner.id)
            .outerjoin(Tier, Membership.current_tier_id == Tier.id)
            .where(Membership.user_id == user_id)
            .order_by(Membership.joined_at.desc())
        )
    ).all()

    memberships = [
        AdminMembershipInfo(
            partner_id=p.id,
            partner_name=p.name,
            partner_slug=p.slug,
            lifetime_earned=m.lifetime_earned,
            current_tier_name=tier_name,
            joined_at=m.joined_at,
        )
        for m, p, tier_name in rows
    ]

    return AdminUserDetailResponse(
        id=target.id,
        email=target.email,
        phone=target.phone,
        full_name=target.full_name,
        system_role=target.system_role,
        is_active=target.is_active,
        created_at=target.created_at,
        last_login_at=target.last_login_at,
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
    if target is None:
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
    if target is None:
        raise HTTPException(status_code=404, detail="Người dùng không tồn tại")

    if target.id == admin.id:
        raise HTTPException(
            status_code=409,
            detail="Không thể reset mật khẩu của chính mình qua trang admin",
        )

    temp_password = _generate_temp_password()
    target.password_hash = hash_password(temp_password)
    await db.commit()

    email_sent = False
    if target.email:
        try:
            await EmailService().send_email(
                to=target.email,
                subject="[Loyalty] Admin đã reset mật khẩu của bạn",
                body=(
                    f"Chào bạn,\n\n"
                    f"Quản trị viên vừa reset mật khẩu của bạn.\n"
                    f"Mật khẩu tạm thời: {temp_password}\n\n"
                    f"Đăng nhập và đổi mật khẩu ngay."
                ),
            )
            email_sent = True
        except EmailDeliveryError:
            logger.warning(
                "admin.reset_password.SMTP_FAIL",
                extra={"user_id": user_id, "temp_password_dev": temp_password},
            )

    return AdminResetPasswordResponse(
        user_id=target.id,
        temporary_password=temp_password,
        email_sent=email_sent,
        user_email=target.email,
    )


@router.get("/stats", response_model=PlatformStatsResponse)
async def get_platform_stats(
    _admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> PlatformStatsResponse:
    """Thống kê toàn platform cho super admin."""
    tenants_count = await db.scalar(
        select(func.count()).select_from(Partner)
    )
    users_count = await db.scalar(
        select(func.count()).select_from(User)
    )
    txn_count = await db.scalar(
        select(func.count()).select_from(Transaction)
    )
    total_points = await db.scalar(
        select(func.coalesce(func.sum(User.points_balance), 0)).where(
            User.is_active.is_(True)
        )
    )
    return PlatformStatsResponse(
        total_tenants=int(tenants_count or 0),
        total_users=int(users_count or 0),
        total_transactions=int(txn_count or 0),
        total_points_circulating=int(total_points or 0),
    )


@router.get("/login-logs", response_model=LoginLogListResponse)
async def list_login_logs(
    identifier: str | None = None,
    success: bool | None = None,
    from_date: datetime | None = Query(default=None, alias="from"),
    to_date: datetime | None = Query(default=None, alias="to"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_super_admin),
) -> LoginLogListResponse:
    """Super Admin xem nhật ký đăng nhập toàn platform."""
    base = select(LoginLog)
    if identifier:
        base = base.where(LoginLog.identifier.ilike(f"%{identifier}%"))
    if success is not None:
        base = base.where(LoginLog.success == success)
    if from_date:
        base = base.where(LoginLog.created_at >= from_date)
    if to_date:
        base = base.where(LoginLog.created_at <= to_date)

    total = int(
        await db.scalar(select(func.count()).select_from(base.subquery())) or 0
    )
    stmt = base.order_by(LoginLog.created_at.desc()).limit(limit).offset(offset)
    logs = (await db.scalars(stmt)).all()

    # Batch-load user emails để tránh N+1
    user_ids = {log.user_id for log in logs if log.user_id is not None}
    email_map: dict[int, str | None] = {}
    if user_ids:
        rows = (
            await db.execute(
                select(User.id, User.email).where(User.id.in_(user_ids))
            )
        ).all()
        email_map = {r.id: r.email for r in rows}

    items = []
    for log in logs:
        item = LoginLogResponse.model_validate(log)
        item.user_email = email_map.get(log.user_id) if log.user_id else None
        items.append(item)

    return LoginLogListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/point-adjustments", response_model=PointAdjustmentListResponse)
async def list_point_adjustments(
    user_id: int | None = None,
    partner_id: int | None = None,
    actor_user_id: int | None = None,
    from_date: datetime | None = Query(default=None, alias="from"),
    to_date: datetime | None = Query(default=None, alias="to"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_super_admin),
) -> PointAdjustmentListResponse:
    """Super Admin xem danh sách điều chỉnh điểm thủ công (reason=adjust)."""
    SubjectUser = aliased(User, name="subject_user")
    ActorUser = aliased(User, name="actor_user")

    base = (
        select(PointLedger, SubjectUser.email, ActorUser.email, Partner.name)
        .join(SubjectUser, SubjectUser.id == PointLedger.user_id)
        .join(Partner, Partner.id == PointLedger.partner_id)
        .outerjoin(ActorUser, ActorUser.id == PointLedger.actor_user_id)
        .where(PointLedger.reason == LedgerReason.ADJUST)
    )
    if user_id is not None:
        base = base.where(PointLedger.user_id == user_id)
    if partner_id is not None:
        base = base.where(PointLedger.partner_id == partner_id)
    if actor_user_id is not None:
        base = base.where(PointLedger.actor_user_id == actor_user_id)
    if from_date:
        base = base.where(PointLedger.created_at >= from_date)
    if to_date:
        base = base.where(PointLedger.created_at <= to_date)

    total = int(
        await db.scalar(select(func.count()).select_from(base.subquery())) or 0
    )
    stmt = (
        base.order_by(PointLedger.created_at.desc()).limit(limit).offset(offset)
    )
    rows = (await db.execute(stmt)).all()

    items = [
        PointAdjustmentResponse(
            id=ledger.id,
            user_id=ledger.user_id,
            user_email=subject_email,
            partner_id=ledger.partner_id,
            partner_name=partner_name,
            actor_user_id=ledger.actor_user_id,
            actor_email=actor_email,
            delta=ledger.delta,
            balance_after=ledger.balance_after,
            description=ledger.description,
            created_at=ledger.created_at,
        )
        for ledger, subject_email, actor_email, partner_name in rows
    ]
    return PointAdjustmentListResponse(
        items=items, total=total, limit=limit, offset=offset
    )


@router.get("/points-summary", response_model=PointsSummaryResponse)
async def get_points_summary(
    _admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> PointsSummaryResponse:
    """Super Admin xem tổng quan điểm toàn hệ thống."""
    # Tổng điểm đang lưu hành (ví active users)
    total_circulating = int(
        await db.scalar(
            select(func.coalesce(func.sum(User.points_balance), 0)).where(
                User.is_active.is_(True)
            )
        )
        or 0
    )

    # Tổng earn / redeem / adjust từ ledger
    ledger_stats = (
        await db.execute(
            select(
                PointLedger.reason,
                func.coalesce(func.sum(PointLedger.delta), 0).label("total"),
            ).group_by(PointLedger.reason)
        )
    ).all()

    reason_totals: dict[str, int] = {}
    for reason, total in ledger_stats:
        reason_str = reason.value if hasattr(reason, "value") else str(reason)
        reason_totals[reason_str] = int(total)

    total_earned = reason_totals.get("earn", 0)
    # redeem deltas are negative — report as positive
    total_redeemed = abs(reason_totals.get("redeem", 0))
    total_adjusted = reason_totals.get("adjust", 0)

    # By partner: tổng điểm earn từng partner (LEFT JOIN so partner không có earn cũng xuất hiện)
    by_partner_rows = (
        await db.execute(
            select(
                Partner.id,
                Partner.name,
                func.coalesce(func.sum(PointLedger.delta), 0).label("total_earned"),
            )
            .outerjoin(
                PointLedger,
                and_(
                    PointLedger.partner_id == Partner.id,
                    PointLedger.reason == LedgerReason.EARN,
                ),
            )
            .group_by(Partner.id, Partner.name)
            .order_by(func.coalesce(func.sum(PointLedger.delta), 0).desc())
        )
    ).all()

    by_partner = [
        PartnerEarnedItem(
            partner_id=pid,
            name=name,
            total_earned=int(total_e),
        )
        for pid, name, total_e in by_partner_rows
    ]

    return PointsSummaryResponse(
        total_circulating=total_circulating,
        total_earned=total_earned,
        total_redeemed=total_redeemed,
        total_adjusted=total_adjusted,
        by_partner=by_partner,
    )
