"""API endpoints — /merchant/campaigns CRUD + ROI."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_tenant_id, require_owner_in_tenant
from app.models.tenant_staff import TenantStaffRole
from app.schemas.campaign import (
    CampaignCreateRequest,
    CampaignResponse,
    CampaignRoiResponse,
    CampaignUpdateRequest,
)
from app.services.campaign_service import CampaignNotFoundError, CampaignService

router = APIRouter(prefix="/merchant/campaigns", tags=["merchant-campaigns"])


@router.get("", response_model=list[CampaignResponse])
async def list_campaigns(
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_owner_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> list[CampaignResponse]:
    rows = await CampaignService(db).list_campaigns_with_stats(
        tenant_id=tenant_id
    )
    result: list[CampaignResponse] = []
    for c, used, discount, revenue in rows:
        resp = CampaignResponse.model_validate(c)
        resp.used_count = used
        resp.total_discount_amount = discount
        resp.total_revenue_from_voucher_txns = revenue
        result.append(resp)
    return result


@router.post("", response_model=CampaignResponse, status_code=201)
async def create_campaign(
    body: CampaignCreateRequest,
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_owner_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> CampaignResponse:
    campaign = await CampaignService(db).create_campaign(
        tenant_id=tenant_id, request=body
    )
    return CampaignResponse.model_validate(campaign)


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: int,
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_owner_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> CampaignResponse:
    try:
        campaign, used, discount, revenue = await CampaignService(
            db
        ).get_campaign_with_stats(
            tenant_id=tenant_id, campaign_id=campaign_id
        )
    except CampaignNotFoundError as e:
        raise HTTPException(status_code=404, detail="Campaign not found") from e
    resp = CampaignResponse.model_validate(campaign)
    resp.used_count = used
    resp.total_discount_amount = discount
    resp.total_revenue_from_voucher_txns = revenue
    return resp


@router.patch("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: int,
    body: CampaignUpdateRequest,
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_owner_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> CampaignResponse:
    try:
        campaign = await CampaignService(db).update_campaign(
            tenant_id=tenant_id, campaign_id=campaign_id, request=body
        )
    except CampaignNotFoundError as e:
        raise HTTPException(status_code=404, detail="Campaign not found") from e
    return CampaignResponse.model_validate(campaign)


@router.delete("/{campaign_id}", status_code=204)
async def delete_campaign(
    campaign_id: int,
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_owner_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> None:
    try:
        await CampaignService(db).soft_delete_campaign(
            tenant_id=tenant_id, campaign_id=campaign_id
        )
    except CampaignNotFoundError as e:
        raise HTTPException(status_code=404, detail="Campaign not found") from e


@router.get("/{campaign_id}/roi", response_model=CampaignRoiResponse)
async def get_campaign_roi(
    campaign_id: int,
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_owner_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> CampaignRoiResponse:
    try:
        return await CampaignService(db).get_campaign_roi(
            tenant_id=tenant_id, campaign_id=campaign_id
        )
    except CampaignNotFoundError as e:
        raise HTTPException(status_code=404, detail="Campaign not found") from e
