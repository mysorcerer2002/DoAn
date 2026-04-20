from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.slug import generate_slug, generate_unique_slug
from app.models.tenant import Tenant, TenantStatus
from app.models.user import User
from app.schemas.tenant import TenantCreateRequest, TenantUpdateRequest


class TenantNotFoundError(Exception):
    pass


class SlugConflictError(Exception):
    pass


class InvalidStatusTransitionError(Exception):
    """Raised khi cố thay đổi trạng thái tenant theo hướng không hợp lệ."""

    pass


class TenantService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_tenant(self, *, owner: User, request: TenantCreateRequest) -> Tenant:
        """Tạo tenant mới (status=pending) + tự thêm owner vào tenant_staff.

        Slug query bound theo prefix (LIKE) thay vì load tất cả slugs trong DB.
        """
        base = generate_slug(request.name) or "shop"
        existing_slugs = set(
            (
                await self.db.scalars(
                    select(Tenant.slug).where(Tenant.slug.like(f"{base}%"))
                )
            ).all()
        )
        slug = generate_unique_slug(request.name, existing_slugs)

        tenant = Tenant(
            name=request.name,
            slug=slug,
            owner_user_id=owner.id,
            status=TenantStatus.PENDING,
            category=request.category,
            description=request.description,
            logo_url=request.logo_url,
            contact_phone=request.contact_phone,
            contact_email=request.contact_email,
            address=request.address,
            tax_code=request.tax_code,
            website=request.website,
            business_hours=request.business_hours,
            settings={},
        )
        self.db.add(tenant)
        try:
            await self.db.flush()
        except IntegrityError as e:
            raise SlugConflictError(
                f"Slug '{slug}' already exists, please retry"
            ) from e

        # Auto-insert owner vào tenant_staff (import tại đây tránh circular)
        from app.models.tenant_staff import TenantStaff, TenantStaffRole

        staff = TenantStaff(
            tenant_id=tenant.id,
            user_id=owner.id,
            role=TenantStaffRole.OWNER,
        )
        self.db.add(staff)
        await self.db.flush()
        await self.db.refresh(tenant)
        return tenant

    async def get_tenant_by_id(self, tenant_id: int) -> Tenant:
        tenant = await self.db.get(Tenant, tenant_id)
        if tenant is None:
            raise TenantNotFoundError(f"Tenant {tenant_id} not found")
        return tenant

    async def get_tenant_by_slug(self, slug: str) -> Tenant | None:
        return await self.db.scalar(select(Tenant).where(Tenant.slug == slug))

    async def list_tenants(self, *, status: TenantStatus | None = None) -> list[Tenant]:
        stmt = select(Tenant).order_by(Tenant.created_at.desc())
        if status is not None:
            stmt = stmt.where(Tenant.status == status)
        return list((await self.db.scalars(stmt)).all())

    async def approve_tenant(self, *, tenant_id: int) -> Tenant:
        """Approve tenant: chỉ chấp nhận chuyển PENDING/SUSPENDED → ACTIVE."""
        tenant = await self.get_tenant_by_id(tenant_id)
        if tenant.status not in (TenantStatus.PENDING, TenantStatus.SUSPENDED):
            raise InvalidStatusTransitionError(
                f"Cannot approve tenant in status {tenant.status.value}"
            )
        tenant.status = TenantStatus.ACTIVE
        if tenant.activated_at is None:
            tenant.activated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return tenant

    async def suspend_tenant(self, *, tenant_id: int) -> Tenant:
        """Suspend tenant: chỉ chấp nhận chuyển PENDING/ACTIVE → SUSPENDED."""
        tenant = await self.get_tenant_by_id(tenant_id)
        if tenant.status not in (TenantStatus.PENDING, TenantStatus.ACTIVE):
            raise InvalidStatusTransitionError(
                f"Cannot suspend tenant in status {tenant.status.value}"
            )
        tenant.status = TenantStatus.SUSPENDED
        await self.db.flush()
        return tenant

    async def update_tenant(
        self, *, tenant_id: int, request: TenantUpdateRequest
    ) -> Tenant:
        tenant = await self.get_tenant_by_id(tenant_id)
        for field, value in request.model_dump(exclude_unset=True).items():
            setattr(tenant, field, value)
        await self.db.flush()
        return tenant

    async def list_tenants_for_user(self, *, user_id: int) -> list[dict]:
        """List tenant mà user là staff/owner. Output match TenantStaffSummary schema."""
        from sqlalchemy.orm import joinedload

        from app.models.tenant_staff import TenantStaff

        rows = (
            await self.db.scalars(
                select(TenantStaff)
                .options(joinedload(TenantStaff.tenant))
                .where(TenantStaff.user_id == user_id)
                .order_by(TenantStaff.added_at)
            )
        ).all()
        return [
            {
                "id": row.tenant.id,
                "name": row.tenant.name,
                "slug": row.tenant.slug,
                "logo_url": row.tenant.logo_url,
                "status": row.tenant.status,
                "role": str(row.role),
            }
            for row in rows
        ]
