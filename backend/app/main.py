from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api import auth as auth_router
from app.api.admin import router as admin_router
from app.api.analytics import router as analytics_router
from app.api.members import router as members_router
from app.api.point_rules import router as point_rules_router
from app.api.qr import router as qr_router
from app.api.redemptions import router as redemptions_router
from app.api.rewards import router as rewards_router
from app.api.settings import router as settings_router
from app.api.partners import partner_router, partners_router, users_router
from app.api.tiers import router as tiers_router
from app.api.transactions import router as transactions_router
from app.core.config import get_settings
from app.core.limiter import limiter
from app.jobs.scheduler import init_scheduler, shutdown_scheduler

settings = get_settings()


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Startup / shutdown events."""
    init_scheduler()
    yield
    shutdown_scheduler()


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={"detail": f"Rate limit exceeded: {exc.detail}"},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Partner-Id"],
)

app.include_router(auth_router.router)
app.include_router(partner_router)
app.include_router(partners_router)
app.include_router(users_router)
app.include_router(admin_router)
app.include_router(tiers_router)
app.include_router(point_rules_router)
app.include_router(settings_router)
app.include_router(transactions_router)
app.include_router(members_router)
app.include_router(qr_router)
app.include_router(rewards_router)
app.include_router(redemptions_router)
app.include_router(analytics_router)


@app.exception_handler(Exception)
async def _global_exception_handler(request, exc: Exception):
    """Catch-all: trả 409 cho IntegrityError, 500 cho lỗi khác."""
    import logging

    from sqlalchemy.exc import IntegrityError

    if isinstance(exc, IntegrityError):
        msg = str(exc.orig) if hasattr(exc, "orig") else str(exc)
        msg_low = msg.lower()
        # Map các unique constraint phổ biến → user-facing message
        if "phone" in msg_low and ("unique" in msg_low or "duplicate" in msg_low):
            detail = "Số điện thoại đã được sử dụng"
        elif "email" in msg_low and ("unique" in msg_low or "duplicate" in msg_low):
            detail = "Email đã được sử dụng"
        elif "slug" in msg_low and ("unique" in msg_low or "duplicate" in msg_low):
            detail = "Slug đã tồn tại"
        elif "receipt_code" in msg_low and ("unique" in msg_low or "duplicate" in msg_low):
            detail = "Mã hoá đơn đã tồn tại cho đối tác này"
        elif "duplicate key" in msg_low:
            detail = "Dữ liệu trùng lặp"
        else:
            detail = "Vi phạm ràng buộc dữ liệu"
        logging.getLogger("app").warning(
            "IntegrityError → 409 [%s] %s", detail, msg[:200]
        )
        return JSONResponse(status_code=409, content={"detail": detail})

    logging.getLogger("app").exception("Unhandled exception")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name}
