import time

from app.core.partner_cache import PartnerRoleCache


def test_cache_set_and_get():
    cache = PartnerRoleCache(maxsize=10, ttl=60)
    cache.set(user_id=1, partner_id=10, role="owner")
    assert cache.get(user_id=1, partner_id=10) == "owner"


def test_cache_miss_returns_none():
    cache = PartnerRoleCache(maxsize=10, ttl=60)
    assert cache.get(user_id=999, partner_id=999) is None


def test_cache_invalidate_specific():
    cache = PartnerRoleCache(maxsize=10, ttl=60)
    cache.set(user_id=1, partner_id=10, role="owner")
    cache.set(user_id=2, partner_id=10, role="staff")

    cache.invalidate(user_id=1, partner_id=10)
    assert cache.get(user_id=1, partner_id=10) is None
    assert cache.get(user_id=2, partner_id=10) == "staff"


def test_cache_invalidate_user_all_partners():
    cache = PartnerRoleCache(maxsize=10, ttl=60)
    cache.set(user_id=1, partner_id=10, role="owner")
    cache.set(user_id=1, partner_id=20, role="staff")
    cache.set(user_id=2, partner_id=10, role="staff")

    cache.invalidate_user(user_id=1)
    assert cache.get(user_id=1, partner_id=10) is None
    assert cache.get(user_id=1, partner_id=20) is None
    assert cache.get(user_id=2, partner_id=10) == "staff"


def test_cache_clear_all():
    cache = PartnerRoleCache(maxsize=10, ttl=60)
    cache.set(user_id=1, partner_id=10, role="owner")
    cache.set(user_id=2, partner_id=20, role="staff")

    cache.clear()
    assert cache.get(user_id=1, partner_id=10) is None
    assert cache.get(user_id=2, partner_id=20) is None


def test_cache_ttl_expiration():
    cache = PartnerRoleCache(maxsize=10, ttl=1)
    cache.set(user_id=1, partner_id=10, role="owner")
    assert cache.get(user_id=1, partner_id=10) == "owner"

    time.sleep(1.1)
    assert cache.get(user_id=1, partner_id=10) is None
