"""CampaignApprovalService — Phase 8 plan voucher rebuild v2.2.

Ops workflow admin:
1. `list_pending` — queue campaign `pending_approval`.
2. `mark_ops_started` — set `ops_filing_started_at=NOW` → chặn shop revoke
   uỷ quyền (C4 guard ở phase 7).
3. `add_regulatory_submission` — ops upload bằng chứng nộp Sở CT
   (`notify_so_ct`/`dang_ky_so_ct`/`xac_nhan_so_ct`/…).
4. `approve` — guard 3 điều kiện (section 4.4 đồ án, bỏ service_fee check):
   a. `approval_status == 'pending_approval'`.
   b. `authorization.revoked_at IS NULL AND valid_until > NOW()`.
   c. Có ít nhất 1 `campaign_regulatory_submissions` với
      `doc_type='xac_nhan_so_ct'` (bằng chứng Sở CT xác nhận hợp lệ).
   Set `approval_status='approved'`, `reviewed_at`, `reviewed_by_user_id`,
   `post_report_due_at = ends_at + 45 ngày` (NĐ 81 Điều 21). Ghi event.
5. `reject` — UPDATE `approval_status='rejected'` TRƯỚC (state machine
   không cho claim nữa), rồi cascade `UPDATE vouchers SET status='cancelled'`
   CHỈ cho `status='issued'` (không đụng `used`/`expired`/`cancelled`).
   Nếu có voucher `used` → trả warning trước, admin phải gửi
   `acknowledge_used_vouchers=True`. Ghi event.
6. `list_overdue_reports` — campaign `post_report_due_at < NOW` chưa
   `post_report_submitted_at` và `approval_tier != 'none'`.
7. `list_events` — audit log cho 1 campaign.

Mọi mutation dùng `SELECT ... FOR UPDATE` trên campaign để race-safe với
revoke bên merchant (phase 7).
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Campaign
from app.models.campaign_approval_event import (
    ApprovalEventType,
    CampaignApprovalEvent,
)
from app.models.campaign_regulatory_submission import (
    CampaignRegulatorySubmission,
    RegulatoryDocType,
)
from app.models.tenant import Tenant
from app.models.tenant_authorization import TenantAuthorization
from app.models.voucher import Voucher, VoucherStatus


POST_REPORT_DEADLINE_DAYS = 45


class CampaignNotFoundError(Exception):
    pass


class InvalidStateError(Exception):
    """Campaign state không cho phép action (vd đã approved)."""


class ApprovalGuardFailed(Exception):
    """Approve thiếu điều kiện; message chỉ rõ lý do."""


class UsedVouchersBlockRejectError(Exception):
    """Reject campaign có voucher `used` mà admin chưa acknowledge."""

    def __init__(self, used_count: int):
        self.used_count = used_count
        super().__init__(
            f"Campaign có {used_count} voucher đã được dùng (status='used'). "
            "Voucher used không bị cancel. Xác nhận lại để tiếp tục reject."
        )


class InvalidDocTypeError(Exception):
    pass


class CampaignApprovalService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _lock_campaign(self, campaign_id: int) -> Campaign:
        campaign = await self.db.scalar(
            select(Campaign)
            .where(Campaign.id == campaign_id, Campaign.deleted_at.is_(None))
            .with_for_update()
        )
        if campaign is None:
            raise CampaignNotFoundError(
                f"Không tìm thấy campaign #{campaign_id}"
            )
        return campaign

    async def list_pending(
        self, *, limit: int = 50, offset: int = 0
    ) -> list[tuple[Campaign, str]]:
        """Trả list `(campaign, tenant_name)` sắp theo created_at asc."""
        q = (
            select(Campaign, Tenant.name.label("tenant_name"))
            .join(Tenant, Tenant.id == Campaign.tenant_id)
            .where(
                Campaign.approval_status == "pending_approval",
                Campaign.deleted_at.is_(None),
            )
            .order_by(Campaign.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(q)
        return [(row[0], row[1]) for row in result.all()]

    async def get_detail(self, campaign_id: int) -> Campaign:
        campaign = await self.db.scalar(
            select(Campaign).where(
                Campaign.id == campaign_id, Campaign.deleted_at.is_(None)
            )
        )
        if campaign is None:
            raise CampaignNotFoundError(
                f"Không tìm thấy campaign #{campaign_id}"
            )
        return campaign

    async def mark_ops_started(
        self, *, campaign_id: int, user_id: int
    ) -> Campaign:
        now = datetime.now(timezone.utc)
        campaign = await self._lock_campaign(campaign_id)

        if campaign.approval_status != "pending_approval":
            raise InvalidStateError(
                "Chỉ đánh dấu nộp hồ sơ khi campaign đang chờ duyệt"
            )
        if campaign.ops_filing_started_at is not None:
            # Idempotent — đã đánh dấu rồi.
            return campaign

        campaign.ops_filing_started_at = now
        self.db.add(
            CampaignApprovalEvent(
                campaign_id=campaign.id,
                event_type=ApprovalEventType.OPS_STARTED.value,
                actor_user_id=user_id,
                reason=None,
                at=now,
            )
        )
        await self.db.flush()
        return campaign

    async def add_regulatory_submission(
        self,
        *,
        campaign_id: int,
        doc_type: str,
        reference_no: str | None,
        url: str | None,
        note: str | None,
        submitted_at: datetime | None,
        user_id: int,
    ) -> CampaignRegulatorySubmission:
        try:
            RegulatoryDocType(doc_type)
        except ValueError:
            raise InvalidDocTypeError(
                f"doc_type không hợp lệ: {doc_type}"
            )

        # Lock campaign để INSERT submission và cập nhật
        # `post_report_submitted_at` (nếu là bao_cao_ket_thuc) đi cùng
        # nhau trong một transaction serialized với approve/reject.
        campaign = await self._lock_campaign(campaign_id)

        now = datetime.now(timezone.utc)
        row = CampaignRegulatorySubmission(
            campaign_id=campaign_id,
            doc_type=doc_type,
            reference_no=reference_no,
            url=url,
            note=note,
            submitted_at=submitted_at or now,
            submitted_by_user_id=user_id,
        )
        self.db.add(row)

        # `bao_cao_ket_thuc` → cập nhật campaign.post_report_submitted_at
        # để job `check_post_report_overdue` không spam.
        if (
            doc_type == RegulatoryDocType.BAO_CAO_KET_THUC.value
            and campaign.post_report_submitted_at is None
        ):
            campaign.post_report_submitted_at = submitted_at or now

        await self.db.flush()
        return row

    async def approve(
        self, *, campaign_id: int, user_id: int
    ) -> Campaign:
        now = datetime.now(timezone.utc)
        campaign = await self._lock_campaign(campaign_id)

        # Guard a: state.
        if campaign.approval_status != "pending_approval":
            raise ApprovalGuardFailed(
                f"Campaign đang ở trạng thái '{campaign.approval_status}', "
                "không duyệt được"
            )

        # Guard b: authorization active (nếu có FK).
        # Lock auth row (.with_for_update()) để độc lập với chuỗi lock
        # campaign→auth ở TenantAuthorizationService.revoke. Race hiện đã
        # serialize qua campaign lock, nhưng giữ lock kép ở đây là defense
        # in depth cho các path tương lai có thể revoke auth không qua
        # campaign.
        if campaign.authorization_id is None:
            raise ApprovalGuardFailed(
                "Campaign chưa có uỷ quyền — không thể duyệt"
            )
        auth = await self.db.scalar(
            select(TenantAuthorization)
            .where(TenantAuthorization.id == campaign.authorization_id)
            .with_for_update()
        )
        if auth is None:
            raise ApprovalGuardFailed(
                "Uỷ quyền liên kết không tồn tại (dangling FK)"
            )
        if auth.revoked_at is not None:
            raise ApprovalGuardFailed("Uỷ quyền đã bị thu hồi")
        if auth.valid_until <= now:
            raise ApprovalGuardFailed(
                "Uỷ quyền đã hết hiệu lực (valid_until <= NOW)"
            )

        # Guard c: xác nhận Sở CT.
        has_xac_nhan = await self.db.scalar(
            select(func.count(CampaignRegulatorySubmission.id)).where(
                CampaignRegulatorySubmission.campaign_id == campaign.id,
                CampaignRegulatorySubmission.doc_type
                == RegulatoryDocType.XAC_NHAN_SO_CT.value,
            )
        )
        if not has_xac_nhan:
            raise ApprovalGuardFailed(
                "Chưa có 'xác nhận Sở CT' (doc_type='xac_nhan_so_ct')"
            )

        campaign.approval_status = "approved"
        campaign.reviewed_at = now
        campaign.reviewed_by_user_id = user_id
        campaign.post_report_due_at = campaign.ends_at + timedelta(
            days=POST_REPORT_DEADLINE_DAYS
        )

        self.db.add(
            CampaignApprovalEvent(
                campaign_id=campaign.id,
                event_type=ApprovalEventType.APPROVED.value,
                actor_user_id=user_id,
                reason=None,
                at=now,
            )
        )
        await self.db.flush()
        return campaign

    async def count_used_vouchers(self, campaign_id: int) -> int:
        return (
            await self.db.scalar(
                select(func.count(Voucher.id)).where(
                    Voucher.campaign_id == campaign_id,
                    Voucher.status == VoucherStatus.USED.value,
                )
            )
            or 0
        )

    async def reject(
        self,
        *,
        campaign_id: int,
        user_id: int,
        reason: str,
        acknowledge_used_vouchers: bool = False,
    ) -> tuple[Campaign, int, int]:
        """Reject + cascade cancel voucher issued-only.

        Trả `(campaign, cancelled_count, used_count)`.
        """
        now = datetime.now(timezone.utc)
        campaign = await self._lock_campaign(campaign_id)

        # Reject dùng cho cả pre-approval (ops chưa duyệt) lẫn
        # post-approval cancellation (đã approved, phát hiện vi phạm →
        # rút chiến dịch). Cascade `issued→cancelled` chỉ có tác dụng ở
        # đường sau (voucher chỉ phát được khi campaign đã approved),
        # vì vậy 'approved' nằm trong whitelist là chủ ý — xem section
        # 4.4 #10 kế hoạch v2.2.
        if campaign.approval_status not in (
            "pending_approval",
            "auto_approved",
            "approved",
            "revision_requested",
        ):
            raise InvalidStateError(
                f"Campaign '{campaign.approval_status}' không thể reject nữa"
            )

        used_count = await self.count_used_vouchers(campaign.id)
        if used_count > 0 and not acknowledge_used_vouchers:
            raise UsedVouchersBlockRejectError(used_count)

        # Ordering: UPDATE approval_status='rejected' trước, rồi cancel vouchers.
        campaign.approval_status = "rejected"
        campaign.reviewed_at = now
        campaign.reviewed_by_user_id = user_id
        campaign.rejection_reason = reason
        await self.db.flush()

        cancel_stmt = (
            update(Voucher)
            .where(
                Voucher.campaign_id == campaign.id,
                Voucher.status == VoucherStatus.ISSUED.value,
            )
            .values(
                status=VoucherStatus.CANCELLED.value,
                cancelled_at=now,
                cancelled_reason=f"Campaign bị từ chối: {reason}",
            )
        )
        result = await self.db.execute(cancel_stmt)
        cancelled_count = result.rowcount or 0

        self.db.add(
            CampaignApprovalEvent(
                campaign_id=campaign.id,
                event_type=ApprovalEventType.REJECTED.value,
                actor_user_id=user_id,
                reason=(
                    f"{reason} "
                    f"(cancel {cancelled_count} voucher issued, "
                    f"giữ {used_count} voucher used)"
                ),
                at=now,
            )
        )
        await self.db.flush()
        return campaign, cancelled_count, used_count

    async def list_overdue_reports(
        self, *, limit: int = 100
    ) -> list[tuple[Campaign, str, int]]:
        """Campaign kết thúc + 45 ngày chưa có báo cáo kết thúc."""
        now = datetime.now(timezone.utc)
        q = (
            select(Campaign, Tenant.name.label("tenant_name"))
            .join(Tenant, Tenant.id == Campaign.tenant_id)
            .where(
                Campaign.post_report_due_at.is_not(None),
                Campaign.post_report_due_at < now,
                Campaign.post_report_submitted_at.is_(None),
                Campaign.approval_tier.in_(
                    ["notify_so_ct", "dang_ky_so_ct", "full_dossier"]
                ),
                Campaign.deleted_at.is_(None),
            )
            .order_by(Campaign.post_report_due_at.asc())
            .limit(limit)
        )
        result = await self.db.execute(q)
        rows: list[tuple[Campaign, str, int]] = []
        for c, tenant_name in result.all():
            days = (now - c.post_report_due_at).days
            rows.append((c, tenant_name, days))
        return rows

    async def list_events(
        self, campaign_id: int
    ) -> list[CampaignApprovalEvent]:
        result = await self.db.scalars(
            select(CampaignApprovalEvent)
            .where(CampaignApprovalEvent.campaign_id == campaign_id)
            .order_by(CampaignApprovalEvent.at.asc())
        )
        return list(result)
