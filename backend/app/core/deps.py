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

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is not an access token",
        )

    try:
        user_id = int(payload["sub"])
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
