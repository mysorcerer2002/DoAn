"""TenantAuthorizationService — Phase 7 plan voucher rebuild v2.2.

Scope:
- List authorizations của 1 tenant (merchant xem lịch sử uỷ quyền).
- Get detail 1 authorization (kèm campaign liên kết).
- Revoke authorization với C4 guard: chỉ cho phép khi
  `campaigns.ops_filing_started_at IS NULL AND approval_status != 'approved'`.
  Sau ops_start → 409 `REVOKE_BLOCKED_OPS_STARTED` (company ops đã bắt đầu
  nộp hồ sơ, shop không được rút lại uỷ quyền).

Revoke path dùng `SELECT ... FOR UPDATE` trên authorization + campaign
để chặn race với mark-ops-started bên admin (phase 8).
"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Campaign
from app.models.campaign_approval_event import (
    ApprovalEventType,
    CampaignApprovalEvent,
)
from app.models.tenant_authorization import TenantAuthorization


class AuthorizationNotFoundError(Exception):
    pass


class AuthorizationAlreadyRevokedError(Exception):
    pass


class RevokeBlockedOpsStartedError(Exception):
    """Company ops đã bắt đầu nộp hồ sơ → không cho revoke."""


class TenantAuthorizationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_tenant(
        self, tenant_id: int
    ) -> list[TenantAuthorization]:
        rows = await self.db.scalars(
            select(TenantAuthorization)
            .where(TenantAuthorization.tenant_id == tenant_id)
            .order_by(TenantAuthorization.signed_at.desc())
        )
        return list(rows)

    async def get_for_tenant(
        self, *, tenant_id: int, auth_id: int
    ) -> TenantAuthorization:
        record = await self.db.scalar(
            select(TenantAuthorization).where(
                TenantAuthorization.id == auth_id,
                TenantAuthorization.tenant_id == tenant_id,
            )
        )
        if record is None:
            raise AuthorizationNotFoundError(
                f"Không tìm thấy uỷ quyền #{auth_id}"
            )
        return record

    async def revoke(
        self,
        *,
        tenant_id: int,
        auth_id: int,
        user_id: int,
        reason: str | None = None,
    ) -> TenantAuthorization:
        """Revoke authorization nếu chưa bị khoá bởi ops_filing_started_at.

        Luồng:
        1. SELECT authorization FOR UPDATE (chặn revoke song song).
        2. Nếu đã revoked → raise AlreadyRevoked (idempotent soft-fail).
        3. SELECT campaign FOR UPDATE → check guard.
        4. Nếu guard pass: set revoked_at/reason + ghi CampaignApprovalEvent
           type=cancelled_by_shop.
        5. Commit ngoài — caller (API route) gọi db.commit().
        """
        now = datetime.now(timezone.utc)

        auth = await self.db.scalar(
            select(TenantAuthorization)
            .where(
                TenantAuthorization.id == auth_id,
                TenantAuthorization.tenant_id == tenant_id,
            )
            .with_for_update()
        )
        if auth is None:
            raise AuthorizationNotFoundError(
                f"Không tìm thấy uỷ quyền #{auth_id}"
            )
        if auth.revoked_at is not None:
            raise AuthorizationAlreadyRevokedError(
                "Uỷ quyền đã được thu hồi trước đó"
            )

        campaign_id = auth.campaign_id
        campaign: Campaign | None = None
        if campaign_id is not None:
            campaign = await self.db.scalar(
                select(Campaign)
                .where(
                    Campaign.id == campaign_id,
                    Campaign.tenant_id == tenant_id,
                )
                .with_for_update()
            )
            if campaign is None:
                raise AuthorizationNotFoundError(
                    "Campaign liên kết với uỷ quyền không tồn tại"
                )

            if campaign.ops_filing_started_at is not None:
                raise RevokeBlockedOpsStartedError(
                    "Công ty ops đã bắt đầu nộp hồ sơ Sở CT — "
                    "không thể thu hồi uỷ quyền. Liên hệ admin nếu cần."
                )
            if campaign.approval_status == "approved":
                raise RevokeBlockedOpsStartedError(
                    "Campaign đã được duyệt — uỷ quyền không thể thu hồi."
                )

        auth.revoked_at = now
        auth.revoked_reason = reason

        if campaign is not None:
            self.db.add(
                CampaignApprovalEvent(
                    campaign_id=campaign.id,
                    event_type=ApprovalEventType.CANCELLED_BY_SHOP.value,
                    actor_user_id=user_id,
                    reason=(
                        f"Thu hồi uỷ quyền #{auth.id}"
                        + (f": {reason}" if reason else "")
                    ),
                    at=now,
                )
            )

        await self.db.flush()
        return auth
