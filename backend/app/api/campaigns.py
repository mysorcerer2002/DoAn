"""API endpoints — /partner/campaigns CRUD + ROI."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_partner_id, require_owner_in_partner
from app.models.partner_staff import PartnerStaffRole
from app.schemas.campaign import (
    CampaignCreateRequest,
    CampaignResponse,
    CampaignRoiResponse,
    CampaignUpdateRequest,
)
from app.services.campaign_service import CampaignNotFoundError, CampaignService

router = APIRouter(prefix="/partner/campaigns", tags=["partner-campaigns"])


@router.get("", response_model=list[CampaignResponse])
async def list_campaigns(
    partner_id: int = Depends(get_partner_id),
    _role: PartnerStaffRole = Depends(require_owner_in_partner),
    db: AsyncSession = Depends(get_db),
) -> list[CampaignResponse]:
    rows = await CampaignService(db).list_campaigns_with_stats(
        partner_id=partner_id
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
    partner_id: int = Depends(get_partner_id),
    _role: PartnerStaffRole = Depends(require_owner_in_partner),
    db: AsyncSession = Depends(get_db),
) -> CampaignResponse:
    campaign = await CampaignService(db).create_campaign(
        partner_id=partner_id, request=body
    )
    return CampaignResponse.model_validate(campaign)


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: int,
    partner_id: int = Depends(get_partner_id),
    _role: PartnerStaffRole = Depends(require_owner_in_partner),
    db: AsyncSession = Depends(get_db),
) -> CampaignResponse:
    try:
        campaign, used, discount, revenue = await CampaignService(
            db
        ).get_campaign_with_stats(
            partner_id=partner_id, campaign_id=campaign_id
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
    partner_id: int = Depends(get_partner_id),
    _role: PartnerStaffRole = Depends(require_owner_in_partner),
    db: AsyncSession = Depends(get_db),
) -> CampaignResponse:
    try:
        campaign = await CampaignService(db).update_campaign(
            partner_id=partner_id, campaign_id=campaign_id, request=body
        )
    except CampaignNotFoundError as e:
        raise HTTPException(status_code=404, detail="Campaign not found") from e
    return CampaignResponse.model_validate(campaign)


@router.delete("/{campaign_id}", status_code=204)
async def delete_campaign(
    campaign_id: int,
    partner_id: int = Depends(get_partner_id),
    _role: PartnerStaffRole = Depends(require_owner_in_partner),
    db: AsyncSession = Depends(get_db),
) -> None:
    try:
        await CampaignService(db).soft_delete_campaign(
            partner_id=partner_id, campaign_id=campaign_id
        )
    except CampaignNotFoundError as e:
        raise HTTPException(status_code=404, detail="Campaign not found") from e


@router.get("/{campaign_id}/roi", response_model=CampaignRoiResponse)
async def get_campaign_roi(
    campaign_id: int,
    partner_id: int = Depends(get_partner_id),
    _role: PartnerStaffRole = Depends(require_owner_in_partner),
    db: AsyncSession = Depends(get_db),
) -> CampaignRoiResponse:
    try:
        return await CampaignService(db).get_campaign_roi(
            partner_id=partner_id, campaign_id=campaign_id
        )
    except CampaignNotFoundError as e:
        raise HTTPException(status_code=404, detail="Campaign not found") from e
