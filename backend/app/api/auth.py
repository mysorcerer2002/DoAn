import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import JWTError
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
from app.schemas.claim_shadow import ClaimShadowRequest, RequestClaimRequest
from app.services.auth_service import AuthService, EmailAlreadyExistsError, InvalidCredentialsError

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
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
@limiter.limit("5/minute")
async def login(
    request: Request,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    service = AuthService(db)
    try:
        user = await service.authenticate(email=body.email, password=body.password)
    except InvalidCredentialsError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e

    return TokenResponse(
        access_token=create_access_token(user_id=user.id),
        refresh_token=create_refresh_token(user_id=user.id),
    )


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("10/minute")
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

    # Reject token nếu issued trước khi user đổi password (ngăn dùng refresh token cũ).
    # Compare integer timestamps (JWT iat lưu giây nguyên — datetime DB có microseconds).
    if user.password_changed_at is not None and payload.iat:
        pwd_changed_ts = int(user.password_changed_at.timestamp())
        if payload.iat < pwd_changed_ts:
            logger.warning(
                "auth.refresh.stale_token",
                extra={"user_id": user.id, "token_iat": payload.iat},
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is stale (password changed)",
            )

    return TokenResponse(
        access_token=create_access_token(user_id=user_id),
        refresh_token=create_refresh_token(user_id=user_id),
    )


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.post("/request-claim", status_code=202)
@limiter.limit("3/minute")
async def request_claim(
    request: Request,
    body: RequestClaimRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = AuthService(db)
    await service.request_claim(email=body.email)
    return {"message": "If account exists and is shadow, code has been sent"}


@router.post("/claim-shadow", response_model=TokenResponse)
@limiter.limit("5/minute")
async def claim_shadow(
    request: Request,
    body: ClaimShadowRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    service = AuthService(db)
    try:
        user = await service.claim_shadow(
            email=body.email,
            code=body.code,
            password=body.password,
            full_name=body.full_name,
            birthday=body.birthday,
        )
    except InvalidCredentialsError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e
    return TokenResponse(
        access_token=create_access_token(user_id=user.id),
        refresh_token=create_refresh_token(user_id=user.id),
    )
