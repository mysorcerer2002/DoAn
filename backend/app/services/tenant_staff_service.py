from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.tenant_staff import TenantStaff, TenantStaffRole
from app.models.user import User
from app.models.verification_code import VerificationCodePurpose
from app.schemas.tenant_staff import (
    StaffAddRequest,
    StaffAddResponse,
    StaffResponse,
    StaffUpdateRoleRequest,
)
from app.services.verification_code_service import VerificationCodeService


class StaffNotFoundError(Exception):
    pass


class StaffAlreadyInTenantError(Exception):
    pass


class TenantStaffService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_staff(
        self, *, tenant_id: int, request: StaffAddRequest
    ) -> StaffAddResponse:
        existing_user = await self.db.scalar(
            select(User).where(User.email == request.email)
        )

        verification_code: str | None = None

        if existing_user is None:
            # Tạo shadow user — chưa có password
            existing_user = User(
                email=request.email,
                full_name=request.full_name,
                password_hash=None,
                is_active=True,
                is_shadow=True,
                system_role="regular",
            )
            self.db.add(existing_user)
            await self.db.flush()

            # Sinh verification code qua HMAC service
            vcs = VerificationCodeService(self.db)
            verification_code = await vcs.create_code(
                user_id=existing_user.id,
                purpose=VerificationCodePurpose.CLAIM_SHADOW,
            )

        # Check đã có trong tenant_staff chưa
        existing_link = await self.db.scalar(
            select(TenantStaff).where(
                TenantStaff.tenant_id == tenant_id,
                TenantStaff.user_id == existing_user.id,
            )
        )
        if existing_link is not None:
            raise StaffAlreadyInTenantError(
                f"User {request.email} already in tenant {tenant_id}"
            )

        staff = TenantStaff(
            tenant_id=tenant_id,
            user_id=existing_user.id,
            role=request.role,
        )
        self.db.add(staff)
        await self.db.flush()
        await self.db.refresh(staff)

        return StaffAddResponse(
            staff=StaffResponse(
                id=staff.id,
                tenant_id=staff.tenant_id,
                user_id=staff.user_id,
                role=staff.role,
                user_email=existing_user.email,
                user_full_name=existing_user.full_name,
                created_at=staff.added_at,
            ),
            verification_code=verification_code,
        )

    async def remove_staff(self, *, tenant_id: int, staff_id: int) -> None:
        staff = await self.db.get(TenantStaff, staff_id)
        if staff is None or staff.tenant_id != tenant_id:
            raise StaffNotFoundError(f"Staff {staff_id} not in tenant {tenant_id}")
        await self.db.delete(staff)
        await self.db.flush()

    async def update_role(
        self, *, tenant_id: int, staff_id: int, request: StaffUpdateRoleRequest
    ) -> StaffResponse:
        staff = await self.db.scalar(
            select(TenantStaff)
            .options(joinedload(TenantStaff.user))
            .where(TenantStaff.id == staff_id, TenantStaff.tenant_id == tenant_id)
        )
        if staff is None:
            raise StaffNotFoundError(f"Staff {staff_id} not in tenant {tenant_id}")
        staff.role = request.role
        await self.db.flush()
        return StaffResponse(
            id=staff.id,
            tenant_id=staff.tenant_id,
            user_id=staff.user_id,
            role=staff.role,
            user_email=staff.user.email,
            user_full_name=staff.user.full_name,
            created_at=staff.added_at,
        )

    async def list_staff(self, *, tenant_id: int) -> list[StaffResponse]:
        rows = (
            await self.db.scalars(
                select(TenantStaff)
                .options(joinedload(TenantStaff.user))
                .where(TenantStaff.tenant_id == tenant_id)
                .order_by(TenantStaff.added_at)
            )
        ).all()
        return [
            StaffResponse(
                id=s.id,
                tenant_id=s.tenant_id,
                user_id=s.user_id,
                role=s.role,
                user_email=s.user.email,
                user_full_name=s.user.full_name,
                created_at=s.added_at,
            )
            for s in rows
        ]
