"""API router cho merchant analytics dashboard."""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_tenant_id, require_owner_in_tenant
from app.models.tenant_staff import TenantStaffRole
from app.schemas.analytics import DashboardResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/merchant/analytics", tags=["merchant-analytics"])


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_owner_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> DashboardResponse:
    """Dashboard analytics — 6 chỉ số chính cho merchant."""
    if to_date is None:
        to_date = date.today()
    if from_date is None:
        from_date = to_date - timedelta(days=30)
    if from_date > to_date:
        raise HTTPException(
            status_code=422,
            detail="from_date must be before or equal to to_date",
        )

    service = AnalyticsService(db)
    return await service.get_dashboard(
        tenant_id=tenant_id, from_date=from_date, to_date=to_date
    )
