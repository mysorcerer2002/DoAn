"""CampaignService — CRUD + soft delete cho campaigns."""

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Campaign
from app.models.transaction import Transaction
from app.models.voucher import Voucher, VoucherStatus
from app.schemas.campaign import (
    CampaignCreateRequest,
    CampaignRoiResponse,
    CampaignUpdateRequest,
)


class CampaignNotFoundError(Exception):
    pass


class CampaignService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_campaign(
        self, *, tenant_id: int, request: CampaignCreateRequest
    ) -> Campaign:
        campaign = Campaign(
            tenant_id=tenant_id,
            name=request.name,
            description=request.description,
            discount_type=request.discount_type,
            discount_value=request.discount_value,
            min_order=request.min_order,
            max_discount=request.max_discount,
            target_tier_id=request.target_tier_id,
            max_issuances=request.max_issuances,
            starts_at=request.starts_at,
            ends_at=request.ends_at,
            is_active=True,
            source=request.source,
        )
        self.db.add(campaign)
        await self.db.flush()
        return campaign

    async def get_campaign(self, *, tenant_id: int, campaign_id: int) -> Campaign:
        campaign = await self.db.scalar(
            select(Campaign).where(
                Campaign.id == campaign_id,
                Campaign.tenant_id == tenant_id,
                Campaign.deleted_at.is_(None),
            )
        )
        if campaign is None:
            raise CampaignNotFoundError(f"Campaign {campaign_id} not found")
        return campaign

    async def list_campaigns(
        self,
        *,
        tenant_id: int,
        active_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Campaign]:
        stmt = (
            select(Campaign)
            .where(Campaign.tenant_id == tenant_id, Campaign.deleted_at.is_(None))
            .order_by(Campaign.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if active_only:
            stmt = stmt.where(Campaign.is_active.is_(True))
        rows = await self.db.scalars(stmt)
        return list(rows.all())

    async def _compute_stats_for_campaigns(
        self, campaign_ids: list[int]
    ) -> dict[int, tuple[int, int, int]]:
        """Trả map campaign_id -> (used_count, total_discount, total_revenue)."""
        if not campaign_ids:
            return {}

        used_rows = await self.db.execute(
            select(Voucher.campaign_id, func.count())
            .where(
                Voucher.campaign_id.in_(campaign_ids),
                Voucher.status == VoucherStatus.USED,
            )
            .group_by(Voucher.campaign_id)
        )
        used_map = {cid: int(cnt) for cid, cnt in used_rows.all()}

        txn_rows = await self.db.execute(
            select(
                Voucher.campaign_id,
                func.coalesce(func.sum(Transaction.voucher_discount_amount), 0),
                func.coalesce(func.sum(Transaction.net_amount), 0),
            )
            .join(Transaction, Transaction.voucher_id == Voucher.id)
            .where(Voucher.campaign_id.in_(campaign_ids))
            .group_by(Voucher.campaign_id)
        )
        txn_map = {
            cid: (int(d), int(r)) for cid, d, r in txn_rows.all()
        }

        return {
            cid: (
                used_map.get(cid, 0),
                txn_map.get(cid, (0, 0))[0],
                txn_map.get(cid, (0, 0))[1],
            )
            for cid in campaign_ids
        }

    async def list_campaigns_with_stats(
        self,
        *,
        tenant_id: int,
        active_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[tuple[Campaign, int, int, int]]:
        campaigns = await self.list_campaigns(
            tenant_id=tenant_id,
            active_only=active_only,
            limit=limit,
            offset=offset,
        )
        stats_map = await self._compute_stats_for_campaigns(
            [c.id for c in campaigns]
        )
        return [
            (c, *stats_map.get(c.id, (0, 0, 0))) for c in campaigns
        ]

    async def get_campaign_with_stats(
        self, *, tenant_id: int, campaign_id: int
    ) -> tuple[Campaign, int, int, int]:
        campaign = await self.get_campaign(
            tenant_id=tenant_id, campaign_id=campaign_id
        )
        stats_map = await self._compute_stats_for_campaigns([campaign.id])
        used, discount, revenue = stats_map.get(campaign.id, (0, 0, 0))
        return campaign, used, discount, revenue

    async def update_campaign(
        self, *, tenant_id: int, campaign_id: int, request: CampaignUpdateRequest
    ) -> Campaign:
        campaign = await self.get_campaign(
            tenant_id=tenant_id, campaign_id=campaign_id
        )
        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(campaign, field, value)
        await self.db.flush()
        return campaign

    async def soft_delete_campaign(
        self, *, tenant_id: int, campaign_id: int
    ) -> Campaign:
        campaign = await self.get_campaign(
            tenant_id=tenant_id, campaign_id=campaign_id
        )
        campaign.deleted_at = datetime.now(timezone.utc)
        campaign.is_active = False
        await self.db.flush()
        return campaign

    async def get_campaign_roi(
        self, *, tenant_id: int, campaign_id: int
    ) -> CampaignRoiResponse:
        """Tính ROI của campaign: vouchers issued/used, tổng discount, tổng revenue."""
        campaign = await self.get_campaign(
            tenant_id=tenant_id, campaign_id=campaign_id
        )

        vouchers_issued = await self.db.scalar(
            select(func.count())
            .select_from(Voucher)
            .where(Voucher.campaign_id == campaign_id)
        )
        vouchers_used = await self.db.scalar(
            select(func.count())
            .select_from(Voucher)
            .where(
                Voucher.campaign_id == campaign_id,
                Voucher.status == VoucherStatus.USED,
            )
        )

        voucher_ids_subq = select(Voucher.id).where(
            Voucher.campaign_id == campaign_id
        )
        txn_stats = await self.db.execute(
            select(
                func.coalesce(func.sum(Transaction.voucher_discount_amount), 0),
                func.coalesce(func.sum(Transaction.net_amount), 0),
            ).where(Transaction.voucher_id.in_(voucher_ids_subq))
        )
        total_discount, total_revenue = txn_stats.one()

        return CampaignRoiResponse(
            campaign_id=campaign.id,
            name=campaign.name,
            vouchers_issued=int(vouchers_issued or 0),
            vouchers_used=int(vouchers_used or 0),
            total_discount_amount=int(total_discount),
            total_revenue_from_voucher_txns=int(total_revenue),
        )
