from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import gen_temp_password, hash_password
from app.models.partner import Partner
from app.models.partner_staff import PartnerStaff
from app.models.user import User
from app.schemas.partner_staff import (
    StaffCreateRequest,
    StaffListResponse,
    StaffPatchRequest,
    StaffResetResponse,
    StaffResponse,
)


class InvalidStaffError(Exception):
    """Raised khi nghiệp vụ staff không hợp lệ."""


class StaffService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_staff(
        self, partner_id: int, is_active: str = "all"
    ) -> StaffListResponse:
        """Lấy danh sách staff của partner, có thể lọc theo is_active."""
        q = (
            select(
                PartnerStaff.id,
                PartnerStaff.user_id,
                PartnerStaff.is_active,
                PartnerStaff.created_at,
                User.email,
                User.phone,
                User.full_name,
            )
            .join(User, User.id == PartnerStaff.user_id)
            .where(PartnerStaff.partner_id == partner_id)
        )
        if is_active == "true":
            q = q.where(PartnerStaff.is_active.is_(True))
        elif is_active == "false":
            q = q.where(PartnerStaff.is_active.is_(False))

        rows = (await self._db.execute(q.order_by(PartnerStaff.created_at))).all()
        items = [
            StaffResponse(
                id=r.id,
                user_id=r.user_id,
                email=r.email,
                phone=r.phone,
                full_name=r.full_name,
                is_active=r.is_active,
                created_at=r.created_at,
            )
            for r in rows
        ]
        return StaffListResponse(items=items, total=len(items))

    async def add_staff(
        self, partner_id: int, req: StaffCreateRequest
    ) -> StaffResponse:
        """Tạo user mới (hoặc tìm user hiện có theo email/phone) và thêm vào staff list."""
        db = self._db

        # Tìm user hiện có theo email hoặc phone
        existing_user: User | None = None
        if req.email:
            existing_user = await db.scalar(
                select(User).where(User.email == req.email)
            )
        if existing_user is None and req.phone:
            existing_user = await db.scalar(
                select(User).where(User.phone == req.phone)
            )

        if existing_user is not None:
            # Guard system_role: super_admin / admin không được làm staff
            if existing_user.system_role != "regular":
                raise InvalidStaffError(
                    "Tài khoản này không thể trở thành nhân viên (vai trò hệ thống đặc biệt)."
                )
            # Guard owner: user đang là chủ shop (bất kỳ partner nào) → reject
            owns_partner = await db.scalar(
                select(Partner.id).where(Partner.owner_user_id == existing_user.id)
            )
            if owns_partner is not None:
                raise InvalidStaffError(
                    "Tài khoản này đang là chủ cửa hàng, không thể làm nhân viên."
                )
            user = existing_user
        else:
            user = User(
                email=req.email,
                phone=req.phone,
                full_name=req.full_name,
                password_hash=hash_password(req.password),
                is_active=True,
                system_role="regular",
            )
            db.add(user)
            try:
                await db.flush()
            except IntegrityError as e:
                await db.rollback()
                raise InvalidStaffError(
                    "Email hoặc số điện thoại đã tồn tại trong hệ thống."
                ) from e

        # Kiểm tra user đã là staff của partner nào chưa
        existing_staff = await db.scalar(
            select(PartnerStaff).where(PartnerStaff.user_id == user.id)
        )
        if existing_staff is not None:
            if existing_staff.partner_id == partner_id:
                raise InvalidStaffError("Nhân viên đã thuộc cửa hàng này.")
            raise InvalidStaffError(
                "Tài khoản này đã là nhân viên của cửa hàng khác."
            )

        staff = PartnerStaff(
            partner_id=partner_id,
            user_id=user.id,
            is_active=True,
        )
        db.add(staff)
        try:
            await db.flush()
        except IntegrityError as e:
            await db.rollback()
            raise InvalidStaffError(
                "Vi phạm ràng buộc dữ liệu khi thêm nhân viên."
            ) from e

        return StaffResponse(
            id=staff.id,
            user_id=user.id,
            email=user.email,
            phone=user.phone,
            full_name=user.full_name,
            is_active=staff.is_active,
            created_at=staff.created_at,
        )

    async def toggle_active(
        self, partner_id: int, user_id: int, req: StaffPatchRequest
    ) -> StaffResponse:
        """Bật/tắt is_active của staff row."""
        db = self._db
        staff = await db.scalar(
            select(PartnerStaff).where(
                PartnerStaff.partner_id == partner_id,
                PartnerStaff.user_id == user_id,
            )
        )
        if staff is None:
            raise InvalidStaffError("Nhân viên không thuộc cửa hàng này.")

        staff.is_active = req.is_active
        await db.flush()

        user = await db.get(User, user_id)
        return StaffResponse(
            id=staff.id,
            user_id=user_id,
            email=user.email if user else None,
            phone=user.phone if user else None,
            full_name=user.full_name if user else None,
            is_active=staff.is_active,
            created_at=staff.created_at,
        )

    async def reset_staff_password(
        self, partner_id: int, user_id: int
    ) -> tuple[str, User]:
        """Reset mật khẩu nhân viên → trả về (temp_password, user)."""
        db = self._db
        staff = await db.scalar(
            select(PartnerStaff).where(
                PartnerStaff.partner_id == partner_id,
                PartnerStaff.user_id == user_id,
            )
        )
        if staff is None:
            raise InvalidStaffError("Nhân viên không thuộc cửa hàng này.")

        user = await db.get(User, user_id)
        if user is None:
            raise InvalidStaffError("Tài khoản nhân viên không tồn tại.")

        temp_password = gen_temp_password()
        user.password_hash = hash_password(temp_password)
        await db.flush()

        return temp_password, user
