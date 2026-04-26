import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import JWTError
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user
from app.core.limiter import limiter
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)


class UpdateMeRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    phone: str | None = Field(default=None, pattern=r"^\+?[0-9\s\-()]{8,20}$")
    birthday: date | None = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8)


from app.core.exceptions import EmailDeliveryError
from app.services.auth_service import (
    AuthService,
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    _hash_email_for_log,
)
from app.services.email_service import EmailService

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def register(
    request: Request,
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    service = AuthService(db)
    try:
        user = await service.register(body)
    except EmailAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e

    return TokenResponse(
        access_token=create_access_token(user_id=user.id),
        refresh_token=create_refresh_token(user_id=user.id),
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("30/minute")
async def login(
    request: Request,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    service = AuthService(db)
    try:
        user = await service.authenticate(identifier=body.identifier, password=body.password)
    except InvalidCredentialsError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e

    return TokenResponse(
        access_token=create_access_token(user_id=user.id),
        refresh_token=create_refresh_token(user_id=user.id),
    )


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("60/minute")
async def refresh(
    request: Request,
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    try:
        payload = decode_token(body.refresh_token)
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        ) from e

    if payload.type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is not a refresh token"
        )

    try:
        user_id = int(payload.sub)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
        ) from e

    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive"
        )

    return TokenResponse(
        access_token=create_access_token(user_id=user_id),
        refresh_token=create_refresh_token(user_id=user_id),
    )


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_me(
    body: UpdateMeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """User tự cập nhật họ tên, SĐT, ngày sinh.

    Phone là unique partial index — nếu trùng raise 409 thay vì 500.
    """
    from sqlalchemy.exc import IntegrityError

    if body.full_name is not None:
        current_user.full_name = body.full_name.strip()
    if body.phone is not None:
        current_user.phone = body.phone.strip()
    if body.birthday is not None:
        current_user.birthday = body.birthday
    try:
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        msg = str(e.orig) if hasattr(e, "orig") else str(e)
        if "phone" in msg.lower():
            raise HTTPException(
                status_code=409,
                detail="Số điện thoại đã được sử dụng bởi tài khoản khác",
            ) from e
        if "email" in msg.lower():
            raise HTTPException(
                status_code=409,
                detail="Email đã được sử dụng",
            ) from e
        raise HTTPException(
            status_code=409, detail="Vi phạm ràng buộc dữ liệu"
        ) from e
    await db.refresh(current_user)
    return current_user


@router.post("/forgot-password", status_code=200)
@limiter.limit("5/minute")
async def forgot_password(
    request: Request,
    body: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Cấp mật khẩu tạm gửi qua email. Idempotent: dù user có hay không vẫn trả 200."""
    service = AuthService(db)
    result = await service.reset_password_send_temp(email=body.email)
    if result is not None:
        temp_password, target_email = result
        email_service = EmailService()
        try:
            await email_service.send_email(
                to=target_email,
                subject="[Loyalty] Mật khẩu mới của bạn",
                body=(
                    f"Chào bạn,\n\n"
                    f"Bạn vừa yêu cầu đặt lại mật khẩu.\n"
                    f"Mật khẩu tạm thời: {temp_password}\n\n"
                    f"Vui lòng đăng nhập và đổi mật khẩu ngay sau khi nhận được."
                ),
            )
        except EmailDeliveryError:
            logger.warning(
                "auth.forgot_password.SMTP_FAIL",
                extra={"email": target_email, "temp_password_dev": temp_password},
            )
    return {"message": "Nếu email hợp lệ, mật khẩu mới đã được gửi."}


@router.patch("/me/password", status_code=204)
async def change_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = AuthService(db)
    try:
        await service.change_password(
            user=current_user,
            current_password=body.current_password,
            new_password=body.new_password,
        )
    except InvalidCredentialsError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    await db.commit()
