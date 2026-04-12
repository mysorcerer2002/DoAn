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
from app.services.auth_service import AuthService, EmailAlreadyExistsError, InvalidCredentialsError

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    service = AuthService(db)
    try:
        user = await service.register(request)
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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)
        ) from e

    return TokenResponse(
        access_token=create_access_token(user_id=user.id),
        refresh_token=create_refresh_token(user_id=user.id),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    try:
        payload = decode_token(request.refresh_token)
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        ) from e

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is not a refresh token"
        )

    user_id = int(payload["sub"])
    return TokenResponse(
        access_token=create_access_token(user_id=user_id),
        refresh_token=request.refresh_token,
    )


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
