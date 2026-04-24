"""Admin campaign approval queue — Phase 8 plan voucher rebuild v2.2.

Endpoint ops:
- `GET /admin/campaigns/pending` — queue chờ duyệt.
- `GET /admin/campaigns/{id}` — chi tiết + metadata workflow.
- `GET /admin/campaigns/{id}/events` — audit log.
- `POST /admin/campaigns/{id}/mark-ops-started` — đánh dấu ops bắt đầu
  nộp Sở CT. Từ khoảnh khắc này, shop không được revoke uỷ quyền
  (guard C4 ở merchant API phase 7).
- `POST /admin/campaigns/{id}/regulatory-submissions` — upload bằng
  chứng nộp/xác nhận Sở CT. Gồm cả `bao_cao_ket_thuc` (báo cáo hậu
  chương trình) → auto set `post_report_submitted_at`.
- `POST /admin/campaigns/{id}/approve` — duyệt; guard 3 điều kiện
  (section 4.4 đồ án, bỏ fee check).
- `POST /admin/campaigns/{id}/reject` — từ chối + cascade cancel
  voucher `issued`. Voucher `used` không đụng. Nếu có `used` mà admin
  chưa `acknowledge_used_vouchers=True` → 409.
- `GET /admin/campaigns/overdue-reports` — quá hạn báo cáo kết thúc.

Yêu cầu `require_super_admin`.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import require_super_admin
from app.models.user import User
from app.schemas.campaign_approval import (
    AdminCampaignDetailResponse,
    ApprovalEventRow,
    OverdueReportRow,
    PendingCampaignRow,
    RegulatorySubmissionRequest,
    RegulatorySubmissionResponse,
    RejectCampaignRequest,
)
from app.services.campaign_approval_service import (
    ApprovalGuardFailed,
    CampaignApprovalService,
    CampaignNotFoundError,
    InvalidDocTypeError,
    InvalidStateError,
    UsedVouchersBlockRejectError,
)
from app.services.transaction_service import TransactionService


router = APIRouter(prefix="/admin", tags=["admin-campaigns"])


def _to_pending_row(campaign, tenant_name: str) -> PendingCampaignRow:
    return PendingCampaignRow(
        id=campaign.id,
        partner_id=campaign.partner_id,
        tenant_name=tenant_name,
        name=campaign.name,
        program_form=campaign.program_form,
        approval_status=campaign.approval_status,
        approval_tier=campaign.approval_tier,
        estimated_cost=campaign.estimated_cost,
        service_fee_total=campaign.service_fee_total,
        service_fee_status=campaign.service_fee_status,
        starts_at=campaign.starts_at,
        ends_at=campaign.ends_at,
        authorization_id=campaign.authorization_id,
        ops_filing_started_at=campaign.ops_filing_started_at,
        created_at=campaign.created_at,
    )


async def _build_detail_response(
    db: AsyncSession, campaign
) -> AdminCampaignDetailResponse:
    """Chuẩn hoá build response: model_validate + patch realized_cost từ view.

    Mọi endpoint trả `AdminCampaignDetailResponse` phải đi qua helper này —
    nếu không, field `realized_cost` sẽ lấy column cache stale (0) thay vì
    giá trị realtime từ `v_campaign_stats` (Phase 10 I2).
    """
    realized = await TransactionService(db).get_campaign_realized_cost_from_view(
        campaign.id
    )
    resp = AdminCampaignDetailResponse.model_validate(campaign)
    resp.realized_cost = realized
    return resp


@router.get(
    "/campaigns/pending",
    response_model=list[PendingCampaignRow],
)
async def list_pending_campaigns(
    limit: int = 50,
    offset: int = 0,
    _admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> list[PendingCampaignRow]:
    rows = await CampaignApprovalService(db).list_pending(
        limit=limit, offset=offset
    )
    return [_to_pending_row(c, tn) for c, tn in rows]


@router.get(
    "/campaigns/overdue-reports",
    response_model=list[OverdueReportRow],
)
async def list_overdue_reports(
    limit: int = 100,
    _admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> list[OverdueReportRow]:
    rows = await CampaignApprovalService(db).list_overdue_reports(limit=limit)
    return [
        OverdueReportRow(
            id=c.id,
            partner_id=c.partner_id,
            tenant_name=tn,
            name=c.name,
            approval_tier=c.approval_tier,
            ends_at=c.ends_at,
            post_report_due_at=c.post_report_due_at,
            days_overdue=days,
        )
        for c, tn, days in rows
    ]


@router.get(
    "/campaigns/{campaign_id}",
    response_model=AdminCampaignDetailResponse,
)
async def get_campaign_detail(
    campaign_id: int,
    _admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminCampaignDetailResponse:
    try:
        campaign = await CampaignApprovalService(db).get_detail(campaign_id)
    except CampaignNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    # Phase 10 I2 — đọc realized_cost realtime từ view `v_campaign_stats`
    # thay vì column cache (column sẽ drop ở phase sau).
    return await _build_detail_response(db, campaign)


@router.get(
    "/campaigns/{campaign_id}/events",
    response_model=list[ApprovalEventRow],
)
async def list_campaign_events(
    campaign_id: int,
    _admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> list[ApprovalEventRow]:
    rows = await CampaignApprovalService(db).list_events(campaign_id)
    return [ApprovalEventRow.model_validate(r) for r in rows]


@router.post(
    "/campaigns/{campaign_id}/mark-ops-started",
    response_model=AdminCampaignDetailResponse,
)
async def mark_ops_started(
    campaign_id: int,
    admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminCampaignDetailResponse:
    try:
        campaign = await CampaignApprovalService(db).mark_ops_started(
            campaign_id=campaign_id, user_id=admin.id
        )
    except CampaignNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidStateError as e:
        raise HTTPException(status_code=409, detail=str(e))

    await db.commit()
    return await _build_detail_response(db, campaign)


@router.post(
    "/campaigns/{campaign_id}/regulatory-submissions",
    response_model=RegulatorySubmissionResponse,
    status_code=201,
)
async def add_regulatory_submission(
    campaign_id: int,
    body: RegulatorySubmissionRequest,
    admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> RegulatorySubmissionResponse:
    try:
        row = await CampaignApprovalService(db).add_regulatory_submission(
            campaign_id=campaign_id,
            doc_type=body.doc_type,
            reference_no=body.reference_no,
            url=body.url,
            note=body.note,
            submitted_at=body.submitted_at,
            user_id=admin.id,
        )
    except CampaignNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidDocTypeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    await db.commit()
    return RegulatorySubmissionResponse.model_validate(row)


@router.post(
    "/campaigns/{campaign_id}/approve",
    response_model=AdminCampaignDetailResponse,
)
async def approve_campaign(
    campaign_id: int,
    admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminCampaignDetailResponse:
    try:
        campaign = await CampaignApprovalService(db).approve(
            campaign_id=campaign_id, user_id=admin.id
        )
    except CampaignNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ApprovalGuardFailed as e:
        raise HTTPException(status_code=400, detail=str(e))

    await db.commit()
    return await _build_detail_response(db, campaign)


@router.post(
    "/campaigns/{campaign_id}/reject",
    response_model=AdminCampaignDetailResponse,
)
async def reject_campaign(
    campaign_id: int,
    body: RejectCampaignRequest,
    admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminCampaignDetailResponse:
    try:
        campaign, cancelled, used = await CampaignApprovalService(db).reject(
            campaign_id=campaign_id,
            user_id=admin.id,
            reason=body.reason,
            acknowledge_used_vouchers=body.acknowledge_used_vouchers,
        )
    except CampaignNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidStateError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except UsedVouchersBlockRejectError as e:
        # Code riêng cho FE hiện modal warning + ô checkbox acknowledge.
        raise HTTPException(
            status_code=409,
            detail={
                "code": "USED_VOUCHERS_REQUIRE_ACK",
                "message": str(e),
                "used_count": e.used_count,
            },
        )

    await db.commit()
    return await _build_detail_response(db, campaign)
