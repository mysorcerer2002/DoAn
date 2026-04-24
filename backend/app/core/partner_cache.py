from cachetools import TTLCache


class PartnerRoleCache:
    """In-memory cache cho (user_id, partner_id) → role.

    Mục đích: tránh query DB partner_staff mỗi request.
    TTL 60s — chấp nhận staff vừa bị revoke vẫn có quyền tối đa 60s.

    LƯU Ý: cache per-process. Nếu chạy nhiều worker, mỗi worker có cache riêng.
    Production cần Redis (xem 6.3 trong spec).
    """

    def __init__(self, maxsize: int = 1024, ttl: int = 60):
        self._cache: TTLCache = TTLCache(maxsize=maxsize, ttl=ttl)

    @staticmethod
    def _key(user_id: int, partner_id: int) -> tuple[int, int]:
        return (user_id, partner_id)

    def get(self, user_id: int, partner_id: int) -> str | None:
        return self._cache.get(self._key(user_id, partner_id))

    def set(self, user_id: int, partner_id: int, role: str) -> None:
        self._cache[self._key(user_id, partner_id)] = role

    def invalidate(self, user_id: int, partner_id: int) -> None:
        self._cache.pop(self._key(user_id, partner_id), None)

    def invalidate_user(self, user_id: int) -> None:
        """Xoá toàn bộ cache entries của 1 user (mọi đối tác).

        Dùng khi: user logout, đổi mật khẩu, bị remove khỏi đối tác.
        """
        keys_to_remove = [k for k in self._cache if k[0] == user_id]
        for k in keys_to_remove:
            self._cache.pop(k, None)

    def clear(self) -> None:
        self._cache.clear()


partner_role_cache = PartnerRoleCache(maxsize=1024, ttl=60)
