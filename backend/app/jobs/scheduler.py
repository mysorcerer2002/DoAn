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
    from app.jobs.cleanup_codes import cleanup_expired_verification_codes

    sched.add_job(
        cleanup_expired_verification_codes,
        trigger=CronTrigger(minute=5),
        id="cleanup_expired_verification_codes",
        replace_existing=True,
    )
    sched.add_job(
        birthday_voucher_job,
        trigger=CronTrigger(hour=0, minute=5),
        id="birthday_voucher_job",
        replace_existing=True,
    )
