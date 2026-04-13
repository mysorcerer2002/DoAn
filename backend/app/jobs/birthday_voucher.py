"""Birthday voucher job — tự động tạo voucher sinh nhật mỗi ngày."""

import logging
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import extract, select, update
from sqlalchemy.orm import joinedload

from app.core.db import AsyncSessionLocal
from app.models.campaign import Campaign, CampaignSource
from app.models.membership import Membership
from app.models.notification import Notification
from app.models.user import User
from app.models.voucher import Voucher, VoucherStatus
from app.services.voucher_service import VoucherService, generate_code

logger = logging.getLogger(__name__)

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


async def birthday_voucher_job() -> dict:
    """Tìm membership có sinh nhật hôm nay, tạo voucher và gửi notification.

    Chạy lúc 00:05 mỗi ngày (CronTrigger). Idempotent: nếu đã có voucher
    từ campaign sinh nhật trong ngày → bỏ qua.
    """
    try:
        return await _birthday_voucher_logic()
    except Exception:
        logger.exception("birthday_voucher_job failed")
        return {"issued": 0, "skipped": 0, "error": True}


async def _birthday_voucher_logic() -> dict:
    """Tính 'today' theo múi giờ VN (Asia/Ho_Chi_Minh).

    Sai timezone → off-by-one day cho user sinh ngay 00:00 ICT (= 17:00 UTC
    ngày trước). Idempotency window cũng tính theo VN day boundary.
    """
    today_vn = datetime.now(VN_TZ).date()
    today = today_vn  # giữ tên cũ trong query extract month/day
    # Idempotency window: ngày VN → UTC range
    today_start_vn = datetime.combine(today_vn, datetime.min.time(), tzinfo=VN_TZ)
    today_start_utc = today_start_vn.astimezone(timezone.utc)
    today_end_utc = (today_start_vn + timedelta(days=1)).astimezone(timezone.utc)
    issued = 0
    skipped = 0

    async with AsyncSessionLocal() as session:
        # Tìm tất cả campaign sinh nhật đang active
        campaigns = (
            await session.scalars(
                select(Campaign).where(
                    Campaign.source == CampaignSource.BIRTHDAY,
                    Campaign.is_active.is_(True),
                    Campaign.deleted_at.is_(None),
                )
            )
        ).all()

        if not campaigns:
            logger.info("No active birthday campaigns found")
            return {"issued": 0, "skipped": 0}

        for campaign in campaigns:
            # Tìm memberships có sinh nhật hôm nay trong tenant này
            memberships = (
                await session.scalars(
                    select(Membership)
                    .join(User, Membership.user_id == User.id)
                    .options(joinedload(Membership.user))
                    .where(
                        Membership.tenant_id == campaign.tenant_id,
                        extract("month", User.birthday) == today.month,
                        extract("day", User.birthday) == today.day,
                    )
                )
            ).unique().all()

            for membership in memberships:
                # Idempotent: kiểm tra đã có voucher sinh nhật trong "ngày VN" hôm nay chưa
                existing = await session.scalar(
                    select(Voucher).where(
                        Voucher.campaign_id == campaign.id,
                        Voucher.membership_id == membership.id,
                        Voucher.issued_at >= today_start_utc,
                        Voucher.issued_at < today_end_utc,
                    )
                )
                if existing:
                    skipped += 1
                    continue

                # Kiểm tra max_issuances
                if campaign.max_issuances and campaign.issued_count >= campaign.max_issuances:
                    logger.warning(
                        "Campaign %d reached max issuances (%d)",
                        campaign.id, campaign.max_issuances,
                    )
                    continue

                # Tạo voucher
                voucher_code = generate_code()
                svc = VoucherService(session)
                ttl_days = await svc.get_voucher_ttl(campaign.tenant_id)
                now = datetime.now(timezone.utc)

                voucher = Voucher(
                    tenant_id=campaign.tenant_id,
                    campaign_id=campaign.id,
                    membership_id=membership.id,
                    code=voucher_code,
                    status=VoucherStatus.ISSUED,
                    issued_at=now,
                    expires_at=now + timedelta(days=ttl_days),
                )
                session.add(voucher)
                await session.execute(
                    update(Campaign)
                    .where(Campaign.id == campaign.id)
                    .values(issued_count=Campaign.issued_count + 1)
                )

                # Push notification
                notification = Notification(
                    tenant_id=campaign.tenant_id,
                    user_id=membership.user_id,
                    type="birthday_voucher",
                    title="Chúc mừng sinh nhật! 🎂",
                    body=f"Bạn nhận được voucher giảm giá {campaign.name}. Mã: {voucher_code}",
                    data={"voucher_code": voucher_code, "campaign_id": campaign.id},
                )
                session.add(notification)
                issued += 1

        await session.commit()

    logger.info("Birthday voucher job: issued=%d, skipped=%d", issued, skipped)
    return {"issued": issued, "skipped": skipped}
