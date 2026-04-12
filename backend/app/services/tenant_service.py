from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.slug import generate_unique_slug
from app.models.tenant import Tenant, TenantStatus
from app.models.user import User
from app.schemas.tenant import TenantCreateRequest, TenantUpdateRequest


class TenantNotFoundError(Exception):
    pass


class SlugConflictError(Exception):
    pass


class TenantService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_tenant(self, *, owner: User, request: TenantCreateRequest) -> Tenant:
        """Tạo tenant mới (status=pending) + tự thêm owner vào tenant_staff."""
        existing_slugs = set(
            (await self.db.scalars(select(Tenant.slug))).all()
        )
        slug = generate_unique_slug(request.name, existing_slugs)

        tenant = Tenant(
            name=request.name,
            slug=slug,
            owner_user_id=owner.id,
            status=TenantStatus.PENDING,
            description=request.description,
            logo_url=request.logo_url,
            settings={},
        )
        self.db.add(tenant)
        await self.db.flush()

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
        tenant = await self.get_tenant_by_id(tenant_id)
        tenant.status = TenantStatus.ACTIVE
        tenant.activated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return tenant

    async def suspend_tenant(self, *, tenant_id: int) -> Tenant:
        tenant = await self.get_tenant_by_id(tenant_id)
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
        """List tenant mà user là staff/owner."""
        from app.models.tenant_staff import TenantStaff
        from sqlalchemy.orm import joinedload

        rows = (
            await self.db.scalars(
                select(TenantStaff)
                .options(joinedload(TenantStaff.tenant))
                .where(TenantStaff.user_id == user_id)
            )
        ).all()
        return [
            {
                "id": row.tenant.id,
                "name": row.tenant.name,
                "slug": row.tenant.slug,
                "status": row.tenant.status,
                "role": row.role.value,
                "logo_url": row.tenant.logo_url,
            }
            for row in rows
        ]
