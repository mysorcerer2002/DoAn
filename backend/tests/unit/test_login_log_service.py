import pytest
from datetime import datetime, timedelta, timezone

from app.models.login_log import LoginLog
from app.services.login_log_service import LoginLogService


@pytest.mark.integration
@pytest.mark.asyncio
async def test_count_recent_failures_excludes_old(db_session):
    now = datetime.now(timezone.utc)
    db_session.add_all([
        LoginLog(identifier="x@y.com", ip="1.1.1.1", success=False,
                 failure_reason="wrong_password", created_at=now - timedelta(minutes=20)),
        LoginLog(identifier="x@y.com", ip="1.1.1.1", success=False,
                 failure_reason="wrong_password", created_at=now - timedelta(minutes=5)),
    ])
    await db_session.commit()

    svc = LoginLogService(db_session)
    count = await svc.count_recent_failures("x@y.com", minutes=15)
    assert count == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_count_recent_failures_excludes_success(db_session):
    now = datetime.now(timezone.utc)
    db_session.add_all([
        LoginLog(identifier="x@y.com", ip="1.1.1.1", success=True, created_at=now),
        LoginLog(identifier="x@y.com", ip="1.1.1.1", success=False,
                 failure_reason="wrong_password", created_at=now),
    ])
    await db_session.commit()
    svc = LoginLogService(db_session)
    assert await svc.count_recent_failures("x@y.com", minutes=15) == 1
