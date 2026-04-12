"""Integration tests: Notification service — push, list, count_unread, mark_read."""

import pytest

from app.models.tenant import Tenant, TenantStatus
from app.models.user import User
from app.services.notification_service import NotificationService


async def _make_user(db_session) -> User:
    user = User(phone="0900000055", password_hash="x", is_active=True)
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.mark.asyncio
async def test_push_notification(db_session):
    user = await _make_user(db_session)
    svc = NotificationService(db_session)

    notif = await svc.push(
        user_id=user.id,
        type="test",
        title="Hello",
        body="World",
    )
    assert notif.id is not None
    assert notif.user_id == user.id
    assert notif.type == "test"
    assert notif.title == "Hello"
    assert notif.is_read is False


@pytest.mark.asyncio
async def test_push_with_tenant_id(db_session):
    user = await _make_user(db_session)
    owner = User(email="notifowner@example.com", password_hash="x", is_active=True)
    db_session.add(owner)
    await db_session.flush()

    tenant = Tenant(
        name="NotifShop", slug="notif-shop",
        owner_user_id=owner.id, status=TenantStatus.ACTIVE, settings={},
    )
    db_session.add(tenant)
    await db_session.flush()

    svc = NotificationService(db_session)
    notif = await svc.push(
        user_id=user.id,
        type="promo",
        title="Khuyến mãi",
        tenant_id=tenant.id,
    )
    assert notif.tenant_id == tenant.id


@pytest.mark.asyncio
async def test_list_user_notifications(db_session):
    user = await _make_user(db_session)
    svc = NotificationService(db_session)

    await svc.push(user_id=user.id, type="a", title="First")
    await svc.push(user_id=user.id, type="b", title="Second")
    await svc.push(user_id=user.id, type="c", title="Third")
    await db_session.flush()

    notifs = await svc.list_user(user_id=user.id)
    assert len(notifs) == 3


@pytest.mark.asyncio
async def test_count_unread(db_session):
    user = await _make_user(db_session)
    svc = NotificationService(db_session)

    await svc.push(user_id=user.id, type="a", title="One")
    await svc.push(user_id=user.id, type="b", title="Two")
    await db_session.flush()

    count = await svc.count_unread(user_id=user.id)
    assert count == 2


@pytest.mark.asyncio
async def test_mark_read(db_session):
    user = await _make_user(db_session)
    svc = NotificationService(db_session)

    n1 = await svc.push(user_id=user.id, type="a", title="One")
    n2 = await svc.push(user_id=user.id, type="b", title="Two")
    await db_session.flush()

    updated = await svc.mark_read(user_id=user.id, notification_ids=[n1.id, n2.id])
    assert updated == 2

    count = await svc.count_unread(user_id=user.id)
    assert count == 0


@pytest.mark.asyncio
async def test_mark_read_idempotent(db_session):
    """Mark read lần 2 → updated = 0."""
    user = await _make_user(db_session)
    svc = NotificationService(db_session)

    n1 = await svc.push(user_id=user.id, type="a", title="One")
    await db_session.flush()

    await svc.mark_read(user_id=user.id, notification_ids=[n1.id])
    updated = await svc.mark_read(user_id=user.id, notification_ids=[n1.id])
    assert updated == 0


@pytest.mark.asyncio
async def test_list_unread_only(db_session):
    user = await _make_user(db_session)
    svc = NotificationService(db_session)

    n1 = await svc.push(user_id=user.id, type="a", title="Read")
    await svc.push(user_id=user.id, type="b", title="Unread")
    await db_session.flush()

    await svc.mark_read(user_id=user.id, notification_ids=[n1.id])
    await db_session.flush()

    notifs = await svc.list_user(user_id=user.id, unread_only=True)
    assert len(notifs) == 1
    assert notifs[0].title == "Unread"
