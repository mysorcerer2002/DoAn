from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import decode_token
from app.models.user import User

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(credentials.credentials)
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    if payload.type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is not an access token",
        )

    try:
        user_id = int(payload.sub)
    except (ValueError, KeyError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        ) from e
    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user


def extract_partner_id_from_header(x_partner_id: str | None) -> int:
    """Đọc và validate header X-Partner-Id thành int.

    Raises HTTPException(400) nếu thiếu hoặc không phải int dương.
    """
    if x_partner_id is None or x_partner_id.strip() == "":
        raise HTTPException(
            status_code=400,
            detail="Missing X-Partner-Id header",
        )
    try:
        partner_id = int(x_partner_id)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail="X-Partner-Id must be a positive integer",
        ) from e
    if partner_id <= 0:
        raise HTTPException(
            status_code=400,
            detail="X-Partner-Id must be a positive integer",
        )
    return partner_id


async def get_partner_id(
    x_partner_id: str | None = Header(default=None, alias="X-Partner-Id"),
) -> int:
    """FastAPI dependency: đọc X-Partner-Id header và return int.

    Dùng cho endpoints /partner/* và /pos/* cần biết partner context.
    """
    return extract_partner_id_from_header(x_partner_id)


async def get_verified_partner_id(
    partner_id: int = Depends(get_partner_id),
    db: AsyncSession = Depends(get_db),
) -> int:
    """Dependency: verify partner tồn tại và đang active trong DB.

    Dùng thay get_partner_id cho public/member endpoints không qua role check.
    """
    from app.models.partner import Partner, PartnerStatus

    partner = await db.get(Partner, partner_id)
    if partner is None:
        raise HTTPException(status_code=404, detail="Partner not found")
    if partner.status != PartnerStatus.ACTIVE:
        raise HTTPException(
            status_code=403,
            detail=f"Partner is {partner.status}, not active",
        )
    return partner_id


async def require_super_admin(
    user: User = Depends(get_current_user),
) -> User:
    """Yêu cầu quyền super_admin để truy cập."""
    if user.system_role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required",
        )
    return user


async def require_owner_in_partner(
    user: User = Depends(get_current_user),
    partner_id: int = Depends(get_partner_id),
    db: AsyncSession = Depends(get_db),
):
    """MVP final 1 owner / shop: chỉ owner mới truy cập được route /partner/*.

    Check partners.owner_user_id == current_user.id. Trả về Partner để route reuse.
    """
    from app.models.partner import Partner

    partner = await db.get(Partner, partner_id)
    if partner is None or partner.owner_user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không phải chủ cửa hàng này.",
        )
    return partner


async def require_staff_in_partner(
    user: User = Depends(get_current_user),
    partner_id: int = Depends(get_partner_id),
    db: AsyncSession = Depends(get_db),
):
    """Dependency: user phải là owner HOẶC active staff của partner.

    Dùng cho POS actions (tích điểm, đổi quà) — staff được phép thực hiện,
    không cần là owner. Trả về Partner để route reuse nếu cần.
    """
    from sqlalchemy import select as sa_select

    from app.models.partner import Partner
    from app.models.partner_staff import PartnerStaff

    partner = await db.get(Partner, partner_id)
    if partner is None:
        raise HTTPException(status_code=404, detail="Partner not found")
    if partner.owner_user_id == user.id:
        return partner
    staff_row = await db.scalar(
        sa_select(PartnerStaff).where(
            PartnerStaff.partner_id == partner_id,
            PartnerStaff.user_id == user.id,
            PartnerStaff.is_active.is_(True),
        )
    )
    if staff_row is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền truy cập shop này.",
        )
    return partner


async def require_customer_in_partner(
    user: User = Depends(get_current_user),
    partner_id: int = Depends(get_partner_id),
    db: AsyncSession = Depends(get_db),
):
    """Dependency: user phải là member của đối tác (có row trong memberships).

    Dùng cho các endpoint customer-facing như /member/redemptions, /member/qr.
    Trả về Membership row để endpoint dùng tiếp (tránh query lại).
    """
    from sqlalchemy import select as sa_select

    from app.models.membership import Membership

    membership = await db.scalar(
        sa_select(Membership).where(
            Membership.partner_id == partner_id,
            Membership.user_id == user.id,
        )
    )
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this partner",
        )
    return membership


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Trả về User nếu có Bearer token hợp lệ, None nếu không."""
    if credentials is None:
        return None
    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        return None
    if payload.type != "access":
        return None
    try:
        user_id = int(payload.sub)
    except (ValueError, KeyError):
        return None
    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        return None
    return user
