"""APScheduler entrypoint — khởi động khi ENABLE_SCHEDULER=true."""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import get_settings

logger = logging.getLogger(__name__)

scheduler: AsyncIOScheduler | None = None


def init_scheduler() -> AsyncIOScheduler | None:
    """Khởi tạo scheduler. Chỉ chạy khi ENABLE_SCHEDULER=true."""
    global scheduler
    settings = get_settings()
    if not settings.enable_scheduler:
        logger.info("Scheduler disabled (ENABLE_SCHEDULER=false)")
        return None

    scheduler = AsyncIOScheduler(
        timezone="Asia/Ho_Chi_Minh",
        job_defaults={"misfire_grace_time": 3600},
    )
    _register_jobs(scheduler)
    scheduler.start()
    logger.info("APScheduler started with %d jobs", len(scheduler.get_jobs()))
    return scheduler


def shutdown_scheduler() -> None:
    """Dừng scheduler."""
    global scheduler
    if scheduler is not None:
        scheduler.shutdown()
        scheduler = None


def _register_jobs(sched: AsyncIOScheduler) -> None:
    """Đăng ký tất cả background jobs."""
    from app.jobs.birthday_voucher import birthday_voucher_job
    from app.jobs.check_post_report_overdue import check_post_report_overdue_job
    from app.jobs.expire_vouchers import expire_vouchers_job
    from app.jobs.purge_retention import purge_retention_job

    sched.add_job(
        birthday_voucher_job,
        trigger=CronTrigger(hour=0, minute=5),
        id="birthday_voucher_job",
        replace_existing=True,
    )
    # Phase 11 — expire voucher mỗi giờ (:00).
    sched.add_job(
        expire_vouchers_job,
        trigger=CronTrigger(hour="*", minute=0),
        id="expire_vouchers_job",
        replace_existing=True,
    )
    # Phase 11 — quét campaign quá hạn báo cáo kết thúc mỗi ngày 01:00.
    sched.add_job(
        check_post_report_overdue_job,
        trigger=CronTrigger(hour=1, minute=0),
        id="check_post_report_overdue_job",
        replace_existing=True,
    )
    # Phase 11 — purge retention (Luật Kế toán 10 năm) mỗi Chủ nhật 02:00.
    sched.add_job(
        purge_retention_job,
        trigger=CronTrigger(day_of_week="sun", hour=2, minute=0),
        id="purge_retention_job",
        replace_existing=True,
    )
