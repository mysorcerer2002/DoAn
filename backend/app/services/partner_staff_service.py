from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.partner_staff import PartnerStaff, PartnerStaffRole
from app.models.user import User
from app.models.verification_code import VerificationCodePurpose
from app.schemas.partner_staff import (
    StaffAddRequest,
    StaffAddResponse,
    StaffResponse,
    StaffUpdateRoleRequest,
)
from app.services.verification_code_service import VerificationCodeService


class StaffNotFoundError(Exception):
    pass


class StaffAlreadyInPartnerError(Exception):
    pass


class LastOwnerError(Exception):
    """Raised khi action sẽ làm đối tác không còn owner nào."""

    pass


class PartnerStaffService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _count_owners(self, partner_id: int) -> int:
        return await self.db.scalar(
            select(func.count())
            .select_from(PartnerStaff)
            .where(
                PartnerStaff.partner_id == partner_id,
                PartnerStaff.role == PartnerStaffRole.OWNER,
            )
        )

    async def add_staff(
        self, *, partner_id: int, request: StaffAddRequest
    ) -> StaffAddResponse:
        """Thêm staff vào đối tác. Tạo shadow user nếu email chưa tồn tại.

        Check link existence TRƯỚC khi tạo shadow để tránh orphan rows
        khi user đã tồn tại + đã link.
        """
        existing_user = await self.db.scalar(
            select(User).where(User.email == request.email)
        )

        # Nếu user đã tồn tại, check link trước khi tạo shadow / verification code
        if existing_user is not None:
            existing_link = await self.db.scalar(
                select(PartnerStaff).where(
                    PartnerStaff.partner_id == partner_id,
                    PartnerStaff.user_id == existing_user.id,
                )
            )
            if existing_link is not None:
                raise StaffAlreadyInPartnerError(
                    f"User {request.email} already in partner {partner_id}"
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

        staff = PartnerStaff(
            partner_id=partner_id,
            user_id=existing_user.id,
            role=request.role,
        )
        self.db.add(staff)
        try:
            await self.db.flush()
        except IntegrityError as e:
            raise StaffAlreadyInPartnerError(
                f"User {request.email} already in partner {partner_id}"
            ) from e
        await self.db.refresh(staff)

        return StaffAddResponse(
            staff=StaffResponse(
                id=staff.id,
                partner_id=staff.partner_id,
                user_id=staff.user_id,
                role=staff.role,
                user_email=existing_user.email,
                user_full_name=existing_user.full_name,
                created_at=staff.added_at,
            ),
            verification_code=verification_code,
        )

    async def remove_staff(self, *, partner_id: int, staff_id: int) -> int:
        """Xóa staff khỏi đối tác. Trả về user_id (để invalidate cache).

        Raises LastOwnerError nếu staff là owner cuối cùng.
        """
        staff = await self.db.get(PartnerStaff, staff_id)
        if staff is None or staff.partner_id != partner_id:
            raise StaffNotFoundError(f"Staff {staff_id} not in partner {partner_id}")
        if staff.role == PartnerStaffRole.OWNER:
            owner_count = await self._count_owners(partner_id)
            if owner_count <= 1:
                raise LastOwnerError("Cannot remove the last owner of a partner")
        user_id = staff.user_id
        await self.db.delete(staff)
        await self.db.flush()
        return user_id

    async def update_role(
        self, *, partner_id: int, staff_id: int, request: StaffUpdateRoleRequest
    ) -> StaffResponse:
        """Cập nhật role staff. Raises LastOwnerError nếu demote owner cuối cùng."""
        staff = await self.db.scalar(
            select(PartnerStaff)
            .options(joinedload(PartnerStaff.user))
            .where(PartnerStaff.id == staff_id, PartnerStaff.partner_id == partner_id)
        )
        if staff is None:
            raise StaffNotFoundError(f"Staff {staff_id} not in partner {partner_id}")
        # Block demote owner cuối cùng
        if staff.role == PartnerStaffRole.OWNER and request.role != PartnerStaffRole.OWNER:
            owner_count = await self._count_owners(partner_id)
            if owner_count <= 1:
                raise LastOwnerError(
                    "Cannot demote the last owner of a partner"
                )
        staff.role = request.role
        await self.db.flush()
        return StaffResponse(
            id=staff.id,
            partner_id=staff.partner_id,
            user_id=staff.user_id,
            role=staff.role,
            user_email=staff.user.email,
            user_full_name=staff.user.full_name,
            created_at=staff.added_at,
        )

    async def list_staff(
        self, *, partner_id: int, limit: int = 50, offset: int = 0
    ) -> list[StaffResponse]:
        rows = (
            await self.db.scalars(
                select(PartnerStaff)
                .options(joinedload(PartnerStaff.user))
                .where(PartnerStaff.partner_id == partner_id)
                .order_by(PartnerStaff.added_at)
                .limit(limit)
                .offset(offset)
            )
        ).all()
        return [
            StaffResponse(
                id=s.id,
                partner_id=s.partner_id,
                user_id=s.user_id,
                role=s.role,
                user_email=s.user.email,
                user_full_name=s.user.full_name,
                created_at=s.added_at,
            )
            for s in rows
        ]
