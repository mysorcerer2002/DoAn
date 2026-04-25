"""API router cho merchant analytics dashboard."""

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_partner_id, require_owner_in_partner
from app.core.limiter import limiter
from app.schemas.analytics import DashboardResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/partner/analytics", tags=["partner-analytics"])

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
MAX_RANGE_DAYS = 366  # >1 năm để cover năm nhuận, chống OOM/heavy queries


@router.get("/dashboard", response_model=DashboardResponse)
@limiter.limit("30/minute")
async def get_dashboard(
    request: Request,
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    partner_id: int = Depends(get_partner_id),
    _=Depends(require_owner_in_partner),
    db: AsyncSession = Depends(get_db),
) -> DashboardResponse:
    """Dashboard analytics — 6 chỉ số chính cho merchant.

    Default range: 30 ngày gần nhất theo timezone VN.
    Max range: 366 ngày (chống OOM/heavy queries).
    Rate limit: 30/min để chống F5 spam.
    """
    if to_date is None:
        to_date = datetime.now(VN_TZ).date()
    if from_date is None:
        from_date = to_date - timedelta(days=30)
    if from_date > to_date:
        raise HTTPException(
            status_code=422,
            detail="from_date must be before or equal to to_date",
        )
    if (to_date - from_date).days > MAX_RANGE_DAYS:
        raise HTTPException(
            status_code=422,
            detail=f"Date range too large (max {MAX_RANGE_DAYS} days)",
        )

    service = AnalyticsService(db)
    return await service.get_dashboard(
        partner_id=partner_id, from_date=from_date, to_date=to_date
    )
