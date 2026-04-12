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


def extract_tenant_id_from_header(x_tenant_id: str | None) -> int:
    """Đọc và validate header X-Tenant-Id thành int.

    Raises HTTPException(400) nếu thiếu hoặc không phải int dương.
    """
    if x_tenant_id is None or x_tenant_id.strip() == "":
        raise HTTPException(
            status_code=400,
            detail="Missing X-Tenant-Id header",
        )
    try:
        tenant_id = int(x_tenant_id)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail="X-Tenant-Id must be a positive integer",
        ) from e
    if tenant_id <= 0:
        raise HTTPException(
            status_code=400,
            detail="X-Tenant-Id must be a positive integer",
        )
    return tenant_id


async def get_tenant_id(
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
) -> int:
    """FastAPI dependency: đọc X-Tenant-Id header và return int.

    Dùng cho endpoints /merchant/* và /pos/* cần biết tenant context.
    """
    return extract_tenant_id_from_header(x_tenant_id)


async def get_verified_tenant_id(
    tenant_id: int = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> int:
    """Dependency: verify tenant tồn tại và đang active trong DB.

    Dùng thay get_tenant_id cho public/member endpoints không qua role check.
    """
    from app.models.tenant import Tenant

    tenant = await db.get(Tenant, tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    if not tenant.is_active:
        raise HTTPException(status_code=403, detail="Tenant is suspended")
    return tenant_id


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


async def get_current_tenant_role(
    user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> "TenantStaffRole":
    """Lấy role của current user trong current tenant.

    1. Lookup cache (TTL 60s)
    2. Cache miss → query DB tenant_staff
    3. Không có row → raise 403
    """
    from sqlalchemy import select as sa_select

    from app.core.tenant_cache import tenant_role_cache
    from app.models.tenant_staff import TenantStaff, TenantStaffRole

    cached = tenant_role_cache.get(user_id=user.id, tenant_id=tenant_id)
    if cached is not None:
        return TenantStaffRole(cached)

    staff = await db.scalar(
        sa_select(TenantStaff).where(
            TenantStaff.tenant_id == tenant_id,
            TenantStaff.user_id == user.id,
        )
    )
    if staff is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied for this tenant",
        )
    tenant_role_cache.set(user_id=user.id, tenant_id=tenant_id, role=staff.role)
    return staff.role


async def require_staff_in_tenant(
    role: "TenantStaffRole" = Depends(get_current_tenant_role),
) -> "TenantStaffRole":
    """Dependency: user phải là staff hoặc owner của tenant."""
    return role


async def require_owner_in_tenant(
    role: "TenantStaffRole" = Depends(get_current_tenant_role),
) -> "TenantStaffRole":
    """Dependency: user phải là owner của tenant."""
    from app.models.tenant_staff import TenantStaffRole

    if role != TenantStaffRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Owner access required",
        )
    return role


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
