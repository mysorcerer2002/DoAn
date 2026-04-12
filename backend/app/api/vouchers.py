"""API endpoints — /member/vouchers (available, claim, mine)."""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user
from app.core.limiter import limiter
from app.models.membership import Membership
from app.models.tenant import Tenant
from app.models.user import User
from app.models.voucher import VoucherStatus
from app.schemas.voucher import (
    CampaignEligibleResponse,
    VoucherClaimRequest,
    VoucherResponse,
)
from app.services.voucher_service import (
    AlreadyClaimedError,
    CampaignFullError,
    CampaignNotEligibleError,
    VoucherService,
)

router = APIRouter(prefix="/member/vouchers", tags=["member-vouchers"])


async def _resolve_tenant_and_membership(
    tenant_slug: str, user: User, db: AsyncSession
) -> tuple[Tenant, Membership]:
    """Helper — resolve tenant + membership hoặc raise 404/403."""
    tenant = await db.scalar(select(Tenant).where(Tenant.slug == tenant_slug))
    if tenant is None:
        raise HTTPException(status_code=404, detail="Shop not found")
    membership = await db.scalar(
        select(Membership).where(
            Membership.tenant_id == tenant.id, Membership.user_id == user.id
        )
    )
    if membership is None:
        raise HTTPException(status_code=403, detail="Not a member of this shop")
    return tenant, membership


@router.get("/available/{tenant_slug}", response_model=list[CampaignEligibleResponse])
async def list_available_campaigns(
    tenant_slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[CampaignEligibleResponse]:
    """List campaigns đủ điều kiện cho khách claim trong tenant này."""
    tenant, membership = await _resolve_tenant_and_membership(
        tenant_slug, current_user, db
    )
    campaigns = await VoucherService(db).list_eligible_campaigns(
        tenant_id=tenant.id,
        membership_id=membership.id,
        current_tier_id=membership.current_tier_id,
    )
    return [
        CampaignEligibleResponse(
            campaign_id=c.id,
            name=c.name,
            description=c.description,
            discount_type=c.discount_type,
            discount_value=c.discount_value,
            min_order=c.min_order,
            max_discount=c.max_discount,
            ends_at=c.ends_at,
            issued_count=c.issued_count,
            max_issuances=c.max_issuances,
        )
        for c in campaigns
    ]


@router.post("/claim/{tenant_slug}", response_model=VoucherResponse, status_code=201)
@limiter.limit("10/minute")
async def claim_voucher(
    request: Request,
    tenant_slug: str,
    body: VoucherClaimRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VoucherResponse:
    """Claim voucher từ campaign — atomic chống TOCTOU."""
    tenant, membership = await _resolve_tenant_and_membership(
        tenant_slug, current_user, db
    )
    service = VoucherService(db)
    try:
        voucher = await service.claim(
            tenant_id=tenant.id,
            membership_id=membership.id,
            campaign_id=body.campaign_id,
        )
    except AlreadyClaimedError as e:
        raise HTTPException(status_code=409, detail="ALREADY_CLAIMED") from e
    except CampaignFullError as e:
        raise HTTPException(status_code=409, detail="CAMPAIGN_FULL") from e
    except CampaignNotEligibleError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return VoucherResponse.model_validate(voucher)


@router.get("/mine/{tenant_slug}", response_model=list[VoucherResponse])
async def list_my_vouchers(
    tenant_slug: str,
    status: VoucherStatus | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[VoucherResponse]:
    """List vouchers của khách trong tenant này."""
    tenant, membership = await _resolve_tenant_and_membership(
        tenant_slug, current_user, db
    )
    vouchers = await VoucherService(db).list_my_vouchers(
        tenant_id=tenant.id,
        membership_id=membership.id,
        status=status,
    )
    return [VoucherResponse.model_validate(v) for v in vouchers]
