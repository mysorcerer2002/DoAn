# Tuần 2 — Multi-tenant Foundation, Tenants, Staff, Tiers, Point Rules, Settings & Claim Shadow

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Xây dựng toàn bộ multi-tenant infrastructure (header `X-Tenant-Id` + cache TTL + dependencies) + 6 backend modules (`tenants`, `tenant_staff`, `tiers`, `point_rules`, `settings`, `verification_codes`) + claim shadow flow đầy đủ + 5 frontend pages (`/admin` minimal, `/merchant/register`, `/merchant/{settings,tiers,point-rules,staff}`) + seed script v1 + cross-tenant isolation tests.

**Architecture:**
- **Multi-tenant strategy:** Shared DB + cột `tenant_id` trong mọi bảng nghiệp vụ. Tenant context lấy qua header `X-Tenant-Id` từ `/merchant` và `/pos`. Middleware cache `(user_id, tenant_id) → role` bằng `cachetools.TTLCache(maxsize=1024, ttl=60)`
- **JWT vẫn đơn giản** (chỉ `user_id` + `system_role`) — không chứa tenant list, từ tuần 1
- **Claim shadow flow:** Verification code 6 số, hash HMAC-SHA256, log ra console (MVP), TTL 10 phút, dùng 1 lần
- **Backend modules:** Mỗi module có model/service/API theo pattern tuần 1 (`AuthService` → router catch domain exception)
- **Frontend:** Mở rộng axios client với header `X-Tenant-Id`, thêm Zustand `tenantStore` cho tenant context state

**Tech Stack additions:**
- `cachetools>=5.5.0` — đã có trong `pyproject.toml` từ tuần 1
- `python-slugify>=8.0.4` — sinh slug tự động từ tên doanh nghiệp

**Cuối tuần phải có:**
- Owner đăng ký tenant (status=pending) → Super Admin duyệt → tenant active
- Owner cấu hình tier (Bronze/Silver/Gold), point_rule (1 điểm/1000 VND), settings
- Owner thêm/xóa/đổi role nhân viên — nhân viên mới claim shadow account qua verification code
- Cross-tenant isolation: API gọi từ tenant A bị reject nếu thao tác data tenant B
- Seed script v1: `python -m scripts.seed` tạo 2 tenant + 5 tier mỗi tenant + 3 point_rule + 5 staff
- ~35 new tests pass (unit + integration + cross-tenant)
- Demo end-to-end Owner workflow chuẩn bị cho Milestone Review #1 với giảng viên

**Acceptance criteria:**
- Super Admin login → `/admin/tenants?status=pending` → bấm Approve → tenant chuyển `active`
- Owner đăng ký `/merchant/register` → nhận token → tenant pending → sau khi duyệt vào `/merchant` cấu hình
- Owner CRUD tier (vd Bronze min=0, Silver min=500, Gold min=2000)
- Owner CRUD point_rule (1 điểm/1000 VND, min_amount=10000)
- Owner thêm staff bằng email → backend log verification code → staff vào `/claim` nhập code → set password → login
- Owner toggle `points_on_gross` setting → audit log entry được ghi
- Test cross-tenant isolation: user tenant A gọi `GET /merchant/tiers` với header `X-Tenant-Id` của tenant B → 403
- `cd backend && pytest -v` → all green (target ~60 tests = 25 từ tuần 1 + 35 mới)
- CI xanh
- Demo scenario chuẩn bị xong cho buổi review giảng viên cuối tuần 2

---

## Tổng quan các phase

| Phase | Tasks | Mô tả | LOC backend | LOC frontend |
|---|---|---|---|---|
| 1 | 1-3 | Multi-tenant context middleware (X-Tenant-Id + cache TTL + dependencies) | ~150 | — |
| 2 | 4-9 | Tenants model + service + API (CRUD + approve flow) | ~400 | — |
| 3 | 10-13 | Tenant_staff model + service + API (Luồng H quản lý nhân viên) | ~350 | — |
| 4 | 14-17 | Tiers model + service + API | ~300 | — |
| 5 | 18-21 | Point_rules module | ~250 | — |
| 6 | 22-25 | Settings module + audit log | ~300 | — |
| 7 | 26-30 | Verification codes + claim shadow flow đầy đủ | ~400 | — |
| 8 | 31-33 | Cross-tenant isolation tests | ~300 | — |
| 9 | 34-35 | Seed script v1 + Makefile target | ~250 | — |
| 10 | 36-38 | Frontend state extension (tenant store, API client với X-Tenant-Id) | — | ~250 |
| 11 | 39-41 | `/admin` minimal (tenant approval) | — | ~300 |
| 12 | 42-45 | `/merchant/register` + dashboard root + auth guard | — | ~400 |
| 13 | 46-48 | `/merchant/tiers` + `/merchant/point-rules` | — | ~400 |
| 14 | 49-50 | `/merchant/settings` (form + audit history) | — | ~250 |
| 15 | 51-54 | `/merchant/staff` (Luồng H — list, add, update role, remove) | — | ~400 |
| 16 | 55-56 | `/claim` page (request code + verify) | — | ~250 |
| 17 | 57-58 | Smoke test E2E + Milestone Review #1 demo prep | — | — |

**Total:** 58 tasks · ~2700 LOC backend · ~2250 LOC frontend · ~35 new tests

---

## File Structure (sẽ tạo / sửa trong tuần 2)

```
D:/DoAn/
├── backend/
│   ├── alembic/versions/
│   │   ├── 002_create_tenants_and_tenant_staff.py        # NEW
│   │   ├── 003_create_tiers_and_point_rules.py           # NEW
│   │   ├── 004_create_verification_codes.py              # NEW
│   │   └── 005_create_tenant_settings_audit.py           # NEW
│   ├── app/
│   │   ├── core/
│   │   │   ├── tenant_cache.py                           # NEW
│   │   │   ├── deps.py                                   # MODIFY (add tenant deps)
│   │   │   └── slug.py                                   # NEW
│   │   ├── models/
│   │   │   ├── tenant.py                                 # NEW
│   │   │   ├── tenant_staff.py                           # NEW
│   │   │   ├── tier.py                                   # NEW
│   │   │   ├── point_rule.py                             # NEW
│   │   │   ├── verification_code.py                      # NEW
│   │   │   └── tenant_settings_audit.py                  # NEW
│   │   ├── schemas/
│   │   │   ├── tenant.py                                 # NEW
│   │   │   ├── tenant_staff.py                           # NEW
│   │   │   ├── tier.py                                   # NEW
│   │   │   ├── point_rule.py                             # NEW
│   │   │   ├── settings.py                               # NEW
│   │   │   └── verification_code.py                      # NEW
│   │   ├── services/
│   │   │   ├── tenant_service.py                         # NEW
│   │   │   ├── tenant_staff_service.py                   # NEW
│   │   │   ├── tier_service.py                           # NEW
│   │   │   ├── point_rule_service.py                     # NEW
│   │   │   ├── settings_service.py                       # NEW
│   │   │   ├── verification_code_service.py              # NEW
│   │   │   └── auth_service.py                           # MODIFY (claim shadow)
│   │   └── api/
│   │       ├── tenants.py                                # NEW
│   │       ├── admin.py                                  # NEW
│   │       ├── tenant_staff.py                           # NEW
│   │       ├── tiers.py                                  # NEW
│   │       ├── point_rules.py                            # NEW
│   │       ├── settings.py                               # NEW
│   │       └── auth.py                                   # MODIFY (claim shadow endpoints)
│   ├── scripts/
│   │   └── seed.py                                       # NEW
│   ├── tests/
│   │   ├── conftest.py                                   # MODIFY (add tenant fixtures)
│   │   └── integration/
│   │       ├── test_tenants_api.py                       # NEW
│   │       ├── test_tenant_staff_api.py                  # NEW
│   │       ├── test_tiers_api.py                         # NEW
│   │       ├── test_point_rules_api.py                   # NEW
│   │       ├── test_settings_api.py                      # NEW
│   │       ├── test_claim_shadow.py                      # NEW
│   │       └── test_tenant_isolation.py                  # NEW
│   └── pyproject.toml                                    # MODIFY (add python-slugify)
├── frontend/
│   ├── src/
│   │   ├── lib/
│   │   │   ├── api.ts                                    # MODIFY (X-Tenant-Id, new endpoints)
│   │   │   ├── auth-store.ts                             # MODIFY (rehydrate user)
│   │   │   └── tenant-store.ts                           # NEW
│   │   ├── types/
│   │   │   ├── tenant.ts                                 # NEW
│   │   │   ├── tier.ts                                   # NEW
│   │   │   ├── point-rule.ts                             # NEW
│   │   │   └── staff.ts                                  # NEW
│   │   ├── components/
│   │   │   ├── auth-guard.tsx                            # NEW
│   │   │   └── tenant-context-provider.tsx               # NEW
│   │   └── app/
│   │       ├── (auth)/claim/page.tsx                     # NEW
│   │       ├── admin/
│   │       │   ├── layout.tsx                            # NEW
│   │       │   ├── page.tsx                              # NEW (dashboard)
│   │       │   └── tenants/page.tsx                      # NEW
│   │       └── merchant/
│   │           ├── layout.tsx                            # NEW (auth guard + tenant context)
│   │           ├── page.tsx                              # NEW (dashboard root)
│   │           ├── register/page.tsx                     # NEW
│   │           ├── settings/page.tsx                     # NEW
│   │           ├── tiers/page.tsx                        # NEW
│   │           ├── point-rules/page.tsx                  # NEW
│   │           └── staff/page.tsx                        # NEW
│   └── package.json                                      # MODIFY (add date-fns nếu cần)
└── Makefile                                              # MODIFY (add make seed)
```

---

## PHASE 1 — Multi-tenant Context Middleware

### Task 1: Cài `python-slugify` + tạo `app/core/slug.py`

**Files:**
- Modify: `D:/DoAn/backend/pyproject.toml`
- Create: `D:/DoAn/backend/app/core/slug.py`
- Create: `D:/DoAn/backend/tests/unit/test_slug.py`

- [ ] **Step 1: Thêm `python-slugify` vào `pyproject.toml`**

Trong section `dependencies`, thêm:

```toml
"python-slugify>=8.0.4",
```

Sau đó install:

```bash
cd D:/DoAn/backend
pip install -e ".[dev]"
```

- [ ] **Step 2: Viết failing test cho slug utility**

Tạo `tests/unit/test_slug.py`:

```python
import pytest

from app.core.slug import generate_slug, generate_unique_slug


def test_generate_slug_basic():
    assert generate_slug("The Coffee House") == "the-coffee-house"


def test_generate_slug_vietnamese():
    assert generate_slug("Cà Phê Trung Nguyên") == "ca-phe-trung-nguyen"


def test_generate_slug_special_chars():
    assert generate_slug("Shop A&B! @123") == "shop-a-and-b-123"


def test_generate_unique_slug_no_conflict():
    existing = set()
    slug = generate_unique_slug("My Shop", existing)
    assert slug == "my-shop"


def test_generate_unique_slug_with_conflict():
    existing = {"my-shop"}
    slug = generate_unique_slug("My Shop", existing)
    assert slug.startswith("my-shop-")
    assert len(slug) == len("my-shop-") + 4
    assert slug not in existing


def test_generate_unique_slug_empty_name_raises():
    with pytest.raises(ValueError):
        generate_unique_slug("", set())
```

- [ ] **Step 3: Run test → FAIL**

```bash
cd D:/DoAn/backend
pytest tests/unit/test_slug.py -v
```

Expected: ImportError `cannot import name 'generate_slug'`

- [ ] **Step 4: Implement `app/core/slug.py`**

```python
import secrets
import string

from slugify import slugify


def generate_slug(name: str) -> str:
    """Sinh slug từ tên (lowercase, dashes, ASCII)."""
    return slugify(name, lowercase=True, separator="-")


def generate_unique_slug(name: str, existing_slugs: set[str]) -> str:
    """Sinh slug duy nhất, thêm random suffix nếu trùng.

    Args:
        name: Tên gốc
        existing_slugs: Set các slug đã tồn tại trong DB

    Returns:
        Slug duy nhất, không trùng với existing_slugs

    Raises:
        ValueError: Nếu name rỗng
    """
    if not name or not name.strip():
        raise ValueError("Name cannot be empty")

    base = generate_slug(name)
    if not base:
        raise ValueError("Name produces empty slug")

    if base not in existing_slugs:
        return base

    alphabet = string.ascii_lowercase + string.digits
    while True:
        suffix = "".join(secrets.choice(alphabet) for _ in range(4))
        candidate = f"{base}-{suffix}"
        if candidate not in existing_slugs:
            return candidate
```

- [ ] **Step 5: Run test → PASS**

```bash
pytest tests/unit/test_slug.py -v
```

Expected: 6 passed

- [ ] **Step 6: Commit**

```bash
cd D:/DoAn
git add backend/pyproject.toml backend/app/core/slug.py backend/tests/unit/test_slug.py
git commit -m "feat(backend): add slug generation utility with TDD"
```

---

### Task 2: Tạo `app/core/tenant_cache.py` với TTLCache

**Files:**
- Create: `D:/DoAn/backend/app/core/tenant_cache.py`
- Create: `D:/DoAn/backend/tests/unit/test_tenant_cache.py`

- [ ] **Step 1: Viết failing test**

Tạo `tests/unit/test_tenant_cache.py`:

```python
import time

import pytest

from app.core.tenant_cache import TenantRoleCache


def test_cache_set_and_get():
    cache = TenantRoleCache(maxsize=10, ttl=60)
    cache.set(user_id=1, tenant_id=10, role="owner")
    assert cache.get(user_id=1, tenant_id=10) == "owner"


def test_cache_miss_returns_none():
    cache = TenantRoleCache(maxsize=10, ttl=60)
    assert cache.get(user_id=999, tenant_id=999) is None


def test_cache_invalidate_specific():
    cache = TenantRoleCache(maxsize=10, ttl=60)
    cache.set(user_id=1, tenant_id=10, role="owner")
    cache.set(user_id=2, tenant_id=10, role="staff")

    cache.invalidate(user_id=1, tenant_id=10)
    assert cache.get(user_id=1, tenant_id=10) is None
    assert cache.get(user_id=2, tenant_id=10) == "staff"


def test_cache_invalidate_user_all_tenants():
    cache = TenantRoleCache(maxsize=10, ttl=60)
    cache.set(user_id=1, tenant_id=10, role="owner")
    cache.set(user_id=1, tenant_id=20, role="staff")
    cache.set(user_id=2, tenant_id=10, role="staff")

    cache.invalidate_user(user_id=1)
    assert cache.get(user_id=1, tenant_id=10) is None
    assert cache.get(user_id=1, tenant_id=20) is None
    assert cache.get(user_id=2, tenant_id=10) == "staff"


def test_cache_clear_all():
    cache = TenantRoleCache(maxsize=10, ttl=60)
    cache.set(user_id=1, tenant_id=10, role="owner")
    cache.set(user_id=2, tenant_id=20, role="staff")

    cache.clear()
    assert cache.get(user_id=1, tenant_id=10) is None
    assert cache.get(user_id=2, tenant_id=20) is None


def test_cache_ttl_expiration():
    cache = TenantRoleCache(maxsize=10, ttl=1)  # 1 giây
    cache.set(user_id=1, tenant_id=10, role="owner")
    assert cache.get(user_id=1, tenant_id=10) == "owner"

    time.sleep(1.1)
    assert cache.get(user_id=1, tenant_id=10) is None
```

- [ ] **Step 2: Run test → FAIL**

```bash
pytest tests/unit/test_tenant_cache.py -v
```

Expected: ImportError

- [ ] **Step 3: Implement `app/core/tenant_cache.py`**

```python
from cachetools import TTLCache


class TenantRoleCache:
    """In-memory cache cho (user_id, tenant_id) → role.

    Mục đích: tránh query DB tenant_staff mỗi request.
    TTL 60s — chấp nhận staff vừa bị revoke vẫn có quyền tối đa 60s.

    LƯU Ý: cache per-process. Nếu chạy nhiều worker, mỗi worker có cache riêng.
    Production cần Redis (xem 6.3 trong spec).
    """

    def __init__(self, maxsize: int = 1024, ttl: int = 60):
        self._cache: TTLCache = TTLCache(maxsize=maxsize, ttl=ttl)

    @staticmethod
    def _key(user_id: int, tenant_id: int) -> tuple[int, int]:
        return (user_id, tenant_id)

    def get(self, user_id: int, tenant_id: int) -> str | None:
        return self._cache.get(self._key(user_id, tenant_id))

    def set(self, user_id: int, tenant_id: int, role: str) -> None:
        self._cache[self._key(user_id, tenant_id)] = role

    def invalidate(self, user_id: int, tenant_id: int) -> None:
        self._cache.pop(self._key(user_id, tenant_id), None)

    def invalidate_user(self, user_id: int) -> None:
        """Xoá toàn bộ cache entries của 1 user (mọi tenant).

        Dùng khi: user logout, đổi mật khẩu, bị remove khỏi tenant.
        """
        keys_to_remove = [k for k in self._cache if k[0] == user_id]
        for k in keys_to_remove:
            self._cache.pop(k, None)

    def clear(self) -> None:
        self._cache.clear()


tenant_role_cache = TenantRoleCache(maxsize=1024, ttl=60)
```

- [ ] **Step 4: Run test → PASS**

```bash
pytest tests/unit/test_tenant_cache.py -v
```

Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/tenant_cache.py backend/tests/unit/test_tenant_cache.py
git commit -m "feat(backend): add tenant role TTL cache with TDD"
```

---

### Task 3: Mở rộng `app/core/deps.py` thêm tenant dependencies

**Files:**
- Modify: `D:/DoAn/backend/app/core/deps.py`
- Create: `D:/DoAn/backend/tests/integration/test_tenant_deps.py`

> **Lưu ý:** Task này KHÔNG implement model `TenantStaff` (sẽ làm ở Task 10), nên test phải mock DB. Mình sẽ chỉ tạo các dependency function và test cơ chế đọc header — phần verify staff sẽ implement thực ở Task 10. Tạm thời `require_staff_in_tenant` raise NotImplementedError nếu chưa có model.

- [ ] **Step 1: Viết failing test cho `extract_tenant_id_from_header`**

Tạo `tests/integration/test_tenant_deps.py`:

```python
import pytest
from fastapi import HTTPException

from app.core.deps import extract_tenant_id_from_header


def test_extract_tenant_id_valid():
    assert extract_tenant_id_from_header("42") == 42


def test_extract_tenant_id_missing_raises_400():
    with pytest.raises(HTTPException) as exc_info:
        extract_tenant_id_from_header(None)
    assert exc_info.value.status_code == 400
    assert "X-Tenant-Id" in exc_info.value.detail


def test_extract_tenant_id_invalid_format_raises_400():
    with pytest.raises(HTTPException) as exc_info:
        extract_tenant_id_from_header("not-a-number")
    assert exc_info.value.status_code == 400


def test_extract_tenant_id_negative_raises_400():
    with pytest.raises(HTTPException) as exc_info:
        extract_tenant_id_from_header("-5")
    assert exc_info.value.status_code == 400
```

- [ ] **Step 2: Run test → FAIL**

```bash
pytest tests/integration/test_tenant_deps.py -v
```

- [ ] **Step 3: Update `app/core/deps.py` thêm `extract_tenant_id_from_header`**

Append vào file `app/core/deps.py`:

```python
from fastapi import Header

def extract_tenant_id_from_header(x_tenant_id: str | None) -> int:
    """Đọc và validate header X-Tenant-Id thành int.

    Raises HTTPException(400) nếu thiếu hoặc không phải int dương.
    """
    if x_tenant_id is None or x_tenant_id.strip() == "":
        raise HTTPException(
            status_code=400,
            detail="Missing X-Tenant-Id header",
        )
    try:
        tenant_id = int(x_tenant_id)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail="X-Tenant-Id must be a positive integer",
        ) from e
    if tenant_id <= 0:
        raise HTTPException(
            status_code=400,
            detail="X-Tenant-Id must be a positive integer",
        )
    return tenant_id


async def get_tenant_id(
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
) -> int:
    """FastAPI dependency: đọc X-Tenant-Id header và return int.

    Dùng cho endpoints `/merchant/*` và `/pos/*` cần biết tenant context.
    Dependency `require_staff_in_tenant` / `require_owner_in_tenant` sẽ
    verify role sau khi có model TenantStaff (Task 10).
    """
    return extract_tenant_id_from_header(x_tenant_id)
```

- [ ] **Step 4: Run test → PASS**

```bash
pytest tests/integration/test_tenant_deps.py -v
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/deps.py backend/tests/integration/test_tenant_deps.py
git commit -m "feat(backend): add X-Tenant-Id header extraction dependency"
```

---

## PHASE 2 — Tenants Model + Service + API

### Task 4: Tạo `app/models/tenant.py` + migration

**Files:**
- Create: `D:/DoAn/backend/app/models/tenant.py`
- Modify: `D:/DoAn/backend/app/models/__init__.py`
- Create: migration auto-generated

- [ ] **Step 1: Tạo `app/models/tenant.py`**

```python
import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class TenantStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"


class Tenant(Base, TimestampMixin):
    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    owner_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[TenantStatus] = mapped_column(
        Enum(TenantStatus, name="tenant_status"),
        default=TenantStatus.PENDING,
        nullable=False,
    )
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    settings: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    activated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    owner: Mapped["User"] = relationship("User", foreign_keys=[owner_user_id])
```

- [ ] **Step 2: Update `app/models/__init__.py`**

```python
from app.models.tenant import Tenant, TenantStatus
from app.models.user import User

__all__ = ["User", "Tenant", "TenantStatus"]
```

- [ ] **Step 3: Generate migration**

```bash
cd D:/DoAn
docker compose up -d postgres
cd backend
alembic revision --autogenerate -m "create tenants table"
```

- [ ] **Step 4: Verify migration file (sửa nếu thiếu enum type)**

Mở file vừa tạo trong `alembic/versions/`. Đảm bảo:
- Có `op.create_table('tenants', ...)` với cột status type là `sa.Enum(...)`
- Có `op.create_index(...)` cho `slug`
- Có FK `owner_user_id` → `users.id`

- [ ] **Step 5: Apply migration**

```bash
alembic upgrade head
docker compose exec postgres psql -U loyalty -d loyalty -c "\d tenants"
```

Expected: schema bảng `tenants` hiển thị đủ cột.

- [ ] **Step 6: Commit**

```bash
cd D:/DoAn
git add backend/app/models/tenant.py backend/app/models/__init__.py backend/alembic/versions/
git commit -m "feat(backend): add Tenant model + migration"
```

---

### Task 5: Tạo Pydantic schemas cho tenant

**Files:**
- Create: `D:/DoAn/backend/app/schemas/tenant.py`

- [ ] **Step 1: Tạo file**

```python
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.tenant import TenantStatus


class TenantCreateRequest(BaseModel):
    """Owner đăng ký doanh nghiệp."""

    name: str = Field(min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    logo_url: str | None = Field(default=None, max_length=500)


class TenantUpdateRequest(BaseModel):
    """Owner cập nhật thông tin tenant (PATCH)."""

    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    logo_url: str | None = Field(default=None, max_length=500)


class TenantResponse(BaseModel):
    """Trả cho owner/staff (đầy đủ thông tin)."""

    id: int
    name: str
    slug: str
    owner_user_id: int
    status: TenantStatus
    logo_url: str | None
    description: str | None
    settings: dict
    created_at: datetime
    activated_at: datetime | None

    model_config = {"from_attributes": True}


class TenantPublicResponse(BaseModel):
    """Trả cho khách hàng cuối browse danh sách shop public.
    Không chứa settings, owner_user_id, status."""

    id: int
    name: str
    slug: str
    logo_url: str | None
    description: str | None

    model_config = {"from_attributes": True}


class TenantApprovalRequest(BaseModel):
    """Super Admin approve/reject."""

    approve: bool
    reason: str | None = Field(default=None, max_length=500)
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/schemas/tenant.py
git commit -m "feat(backend): add tenant Pydantic schemas"
```

---

### Task 6: TDD — TenantService.create_tenant + approve_tenant

**Files:**
- Create: `D:/DoAn/backend/app/services/tenant_service.py`
- Create: `D:/DoAn/backend/tests/integration/test_tenant_service.py`

- [ ] **Step 1: Viết failing tests**

Tạo `tests/integration/test_tenant_service.py`:

```python
import pytest

from app.models.tenant import TenantStatus
from app.models.user import User
from app.schemas.tenant import TenantCreateRequest
from app.services.tenant_service import (
    SlugConflictError,
    TenantNotFoundError,
    TenantService,
)


@pytest.mark.asyncio
async def test_create_tenant_creates_pending_with_slug(db_session):
    user = User(email="owner@example.com", password_hash="x", is_active=True)
    db_session.add(user)
    await db_session.flush()

    service = TenantService(db_session)
    request = TenantCreateRequest(name="The Coffee House", description="Cà phê thủ công")
    tenant = await service.create_tenant(owner=user, request=request)

    assert tenant.id is not None
    assert tenant.name == "The Coffee House"
    assert tenant.slug == "the-coffee-house"
    assert tenant.status == TenantStatus.PENDING
    assert tenant.owner_user_id == user.id
    assert tenant.activated_at is None


@pytest.mark.asyncio
async def test_create_tenant_with_slug_conflict_appends_suffix(db_session):
    user1 = User(email="o1@example.com", password_hash="x", is_active=True)
    user2 = User(email="o2@example.com", password_hash="x", is_active=True)
    db_session.add_all([user1, user2])
    await db_session.flush()

    service = TenantService(db_session)
    t1 = await service.create_tenant(owner=user1, request=TenantCreateRequest(name="My Shop"))
    await db_session.flush()
    t2 = await service.create_tenant(owner=user2, request=TenantCreateRequest(name="My Shop"))

    assert t1.slug == "my-shop"
    assert t2.slug.startswith("my-shop-")
    assert len(t2.slug) == len("my-shop-") + 4


@pytest.mark.asyncio
async def test_approve_tenant_changes_status_and_sets_activated_at(db_session):
    user = User(email="o@example.com", password_hash="x", is_active=True)
    db_session.add(user)
    await db_session.flush()

    service = TenantService(db_session)
    tenant = await service.create_tenant(
        owner=user, request=TenantCreateRequest(name="Pending Shop")
    )
    await db_session.flush()
    assert tenant.status == TenantStatus.PENDING

    approved = await service.approve_tenant(tenant_id=tenant.id)
    assert approved.status == TenantStatus.ACTIVE
    assert approved.activated_at is not None


@pytest.mark.asyncio
async def test_approve_nonexistent_tenant_raises(db_session):
    service = TenantService(db_session)
    with pytest.raises(TenantNotFoundError):
        await service.approve_tenant(tenant_id=99999)


@pytest.mark.asyncio
async def test_list_pending_tenants(db_session):
    user = User(email="o@example.com", password_hash="x", is_active=True)
    db_session.add(user)
    await db_session.flush()

    service = TenantService(db_session)
    t1 = await service.create_tenant(owner=user, request=TenantCreateRequest(name="Shop A"))
    t2 = await service.create_tenant(owner=user, request=TenantCreateRequest(name="Shop B"))
    await db_session.flush()
    await service.approve_tenant(tenant_id=t1.id)

    pending = await service.list_tenants(status=TenantStatus.PENDING)
    pending_ids = [t.id for t in pending]
    assert t2.id in pending_ids
    assert t1.id not in pending_ids
```

- [ ] **Step 2: Run test → FAIL**

```bash
pytest tests/integration/test_tenant_service.py -v
```

- [ ] **Step 3: Implement `app/services/tenant_service.py`**

```python
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.slug import generate_unique_slug
from app.models.tenant import Tenant, TenantStatus
from app.models.user import User
from app.schemas.tenant import TenantCreateRequest, TenantUpdateRequest


class TenantNotFoundError(Exception):
    pass


class SlugConflictError(Exception):
    pass


class TenantService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_tenant(self, *, owner: User, request: TenantCreateRequest) -> Tenant:
        existing_slugs = set(
            (await self.db.scalars(select(Tenant.slug))).all()
        )
        slug = generate_unique_slug(request.name, existing_slugs)

        tenant = Tenant(
            name=request.name,
            slug=slug,
            owner_user_id=owner.id,
            status=TenantStatus.PENDING,
            description=request.description,
            logo_url=request.logo_url,
            settings={},
        )
        self.db.add(tenant)
        await self.db.flush()
        await self.db.refresh(tenant)
        return tenant

    async def get_tenant_by_id(self, tenant_id: int) -> Tenant:
        tenant = await self.db.get(Tenant, tenant_id)
        if tenant is None:
            raise TenantNotFoundError(f"Tenant {tenant_id} not found")
        return tenant

    async def get_tenant_by_slug(self, slug: str) -> Tenant | None:
        return await self.db.scalar(select(Tenant).where(Tenant.slug == slug))

    async def list_tenants(self, *, status: TenantStatus | None = None) -> list[Tenant]:
        stmt = select(Tenant).order_by(Tenant.created_at.desc())
        if status is not None:
            stmt = stmt.where(Tenant.status == status)
        return list((await self.db.scalars(stmt)).all())

    async def approve_tenant(self, *, tenant_id: int) -> Tenant:
        tenant = await self.get_tenant_by_id(tenant_id)
        tenant.status = TenantStatus.ACTIVE
        tenant.activated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return tenant

    async def suspend_tenant(self, *, tenant_id: int) -> Tenant:
        tenant = await self.get_tenant_by_id(tenant_id)
        tenant.status = TenantStatus.SUSPENDED
        await self.db.flush()
        return tenant

    async def update_tenant(
        self, *, tenant_id: int, request: TenantUpdateRequest
    ) -> Tenant:
        tenant = await self.get_tenant_by_id(tenant_id)
        for field, value in request.model_dump(exclude_unset=True).items():
            setattr(tenant, field, value)
        await self.db.flush()
        return tenant
```

- [ ] **Step 4: Run test → PASS**

```bash
pytest tests/integration/test_tenant_service.py -v
```

Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/tenant_service.py backend/tests/integration/test_tenant_service.py
git commit -m "feat(backend): add TenantService with create + approve + list (TDD)"
```

---

### Task 7: API endpoint `POST /merchant/register` (đăng ký tenant)

**Files:**
- Create: `D:/DoAn/backend/app/api/tenants.py`
- Create: `D:/DoAn/backend/tests/integration/test_tenants_api.py`
- Modify: `D:/DoAn/backend/app/main.py`

- [ ] **Step 1: Viết failing test**

Tạo `tests/integration/test_tenants_api.py`:

```python
import pytest


@pytest.mark.asyncio
async def test_merchant_register_creates_pending_tenant(client):
    register = await client.post(
        "/auth/register",
        json={"email": "owner@example.com", "password": "pass12345", "full_name": "Owner"},
    )
    token = register.json()["access_token"]

    response = await client.post(
        "/merchant/register",
        json={"name": "The Coffee House", "description": "Cà phê thủ công"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "The Coffee House"
    assert data["slug"] == "the-coffee-house"
    assert data["status"] == "pending"
    assert data["activated_at"] is None


@pytest.mark.asyncio
async def test_merchant_register_without_auth_returns_401(client):
    response = await client.post(
        "/merchant/register",
        json={"name": "Shop"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_merchant_register_invalid_name_returns_422(client):
    register = await client.post(
        "/auth/register",
        json={"email": "owner@example.com", "password": "pass12345", "full_name": "X"},
    )
    token = register.json()["access_token"]

    response = await client.post(
        "/merchant/register",
        json={"name": "X"},  # Quá ngắn (min 2)
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422
```

- [ ] **Step 2: Run test → FAIL**

```bash
pytest tests/integration/test_tenants_api.py -v
```

Expected: 404

- [ ] **Step 3: Tạo `app/api/tenants.py`**

```python
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.tenant import TenantCreateRequest, TenantResponse
from app.services.tenant_service import TenantService

router = APIRouter(prefix="/merchant", tags=["merchant"])


@router.post(
    "/register",
    response_model=TenantResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_tenant(
    request: TenantCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TenantResponse:
    """Owner đăng ký doanh nghiệp mới (status=pending, chờ Super Admin duyệt)."""
    service = TenantService(db)
    tenant = await service.create_tenant(owner=current_user, request=request)
    return TenantResponse.model_validate(tenant)
```

- [ ] **Step 4: Update `app/main.py` register router**

Thêm vào main.py:

```python
from app.api import tenants as tenants_router

app.include_router(tenants_router.router)
```

- [ ] **Step 5: Run test → PASS**

```bash
pytest tests/integration/test_tenants_api.py -v
```

Expected: 3 passed

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/tenants.py backend/app/main.py backend/tests/integration/test_tenants_api.py
git commit -m "feat(backend): add POST /merchant/register endpoint"
```

---

### Task 8: API endpoints `/admin/tenants` (list pending + approve)

**Files:**
- Create: `D:/DoAn/backend/app/api/admin.py`
- Modify: `D:/DoAn/backend/tests/integration/test_tenants_api.py`
- Modify: `D:/DoAn/backend/app/core/deps.py`
- Modify: `D:/DoAn/backend/app/main.py`

- [ ] **Step 1: Thêm `require_super_admin` dependency vào `app/core/deps.py`**

Append vào file:

```python
async def require_super_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Chỉ cho phép user có system_role='super_admin'."""
    if current_user.system_role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super Admin access required",
        )
    return current_user
```

- [ ] **Step 2: Viết failing tests**

Append vào `tests/integration/test_tenants_api.py`:

```python
@pytest.mark.asyncio
async def test_list_pending_tenants_super_admin(client, db_session):
    from app.models.user import User

    admin = User(
        email="admin@example.com",
        password_hash="x",
        is_active=True,
        system_role="super_admin",
    )
    db_session.add(admin)
    await db_session.flush()

    from app.core.security import create_access_token
    admin_token = create_access_token(user_id=admin.id)

    register = await client.post(
        "/auth/register",
        json={"email": "owner@example.com", "password": "pass12345", "full_name": "Owner"},
    )
    owner_token = register.json()["access_token"]
    await client.post(
        "/merchant/register",
        json={"name": "Pending Shop"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    response = await client.get(
        "/admin/tenants?status=pending",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(t["name"] == "Pending Shop" for t in data)


@pytest.mark.asyncio
async def test_list_tenants_not_super_admin_returns_403(client):
    register = await client.post(
        "/auth/register",
        json={"email": "regular@example.com", "password": "pass12345", "full_name": "Reg"},
    )
    token = register.json()["access_token"]

    response = await client.get(
        "/admin/tenants",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_approve_tenant_changes_status(client, db_session):
    from app.core.security import create_access_token
    from app.models.user import User

    admin = User(
        email="admin@example.com", password_hash="x", is_active=True, system_role="super_admin"
    )
    db_session.add(admin)
    await db_session.flush()
    admin_token = create_access_token(user_id=admin.id)

    register = await client.post(
        "/auth/register",
        json={"email": "owner@example.com", "password": "pass12345", "full_name": "Owner"},
    )
    owner_token = register.json()["access_token"]
    create_resp = await client.post(
        "/merchant/register",
        json={"name": "Pending Shop"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    tenant_id = create_resp.json()["id"]

    response = await client.post(
        f"/admin/tenants/{tenant_id}/approve",
        json={"approve": True},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "active"
    assert response.json()["activated_at"] is not None
```

- [ ] **Step 3: Tạo `app/api/admin.py` (★ FIX C2 — rename status param tránh shadow `fastapi.status` module)**

```python
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import require_super_admin
from app.models.tenant import TenantStatus
from app.models.user import User
from app.schemas.tenant import TenantApprovalRequest, TenantResponse
from app.services.tenant_service import TenantNotFoundError, TenantService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/tenants", response_model=list[TenantResponse])
async def list_tenants(
    # ★ FIX C2: param tên `tenant_status` để KHÔNG shadow `fastapi.status` module.
    # `alias="status"` giữ query param public là `?status=pending` cho client.
    tenant_status: TenantStatus | None = Query(default=None, alias="status"),
    _admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> list[TenantResponse]:
    service = TenantService(db)
    tenants = await service.list_tenants(status=tenant_status)
    return [TenantResponse.model_validate(t) for t in tenants]


@router.post("/tenants/{tenant_id}/approve", response_model=TenantResponse)
async def approve_tenant(
    tenant_id: int,
    body: TenantApprovalRequest,
    _admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> TenantResponse:
    service = TenantService(db)
    try:
        if body.approve:
            tenant = await service.approve_tenant(tenant_id=tenant_id)
        else:
            tenant = await service.suspend_tenant(tenant_id=tenant_id)
    except TenantNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return TenantResponse.model_validate(tenant)
```

- [ ] **Step 4: Update `app/main.py`**

Thêm:

```python
from app.api import admin as admin_router

app.include_router(admin_router.router)
```

- [ ] **Step 5: Run tests → PASS**

```bash
pytest tests/integration/test_tenants_api.py -v
```

Expected: 6 passed

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/admin.py backend/app/main.py backend/app/core/deps.py backend/tests/integration/test_tenants_api.py
git commit -m "feat(backend): add /admin tenants list + approve endpoints"
```

---

### Task 8.5 (★ NEW — fix I15): GET `/users/me/tenants` — list tenant của user hiện tại

> **★ FIX I15 từ review:** Plan ban đầu không có API này → flow login → /merchant bị broken (TenantContextProvider không biết tenant nào để set làm current). PHẢI thêm API + frontend logic dùng API này sau login.

**Files:**
- Modify: `D:/DoAn/backend/app/api/tenants.py`
- Modify: `D:/DoAn/backend/app/schemas/tenant.py`
- Modify: `D:/DoAn/backend/tests/integration/test_tenants_api.py`

- [ ] **Step 1: Schema `app/schemas/tenant.py` thêm `UserTenantSummary`**

```python
class UserTenantSummary(BaseModel):
    """Tenant summary cho user — dùng cho /users/me/tenants."""
    id: int
    name: str
    slug: str
    status: TenantStatus
    role: str  # owner / staff
    logo_url: str | None

    model_config = {"from_attributes": True}
```

- [ ] **Step 2: Endpoint trong `app/api/tenants.py` (thêm vào `tenants_router`)**

```python
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.models.tenant_staff import TenantStaff
from app.schemas.tenant import UserTenantSummary


@tenants_router.get("/users/me/tenants", response_model=list[UserTenantSummary])
async def list_my_tenants(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[UserTenantSummary]:
    """List tenant mà user là staff/owner. Frontend dùng để chọn tenant sau login."""
    rows = await db.scalars(
        select(TenantStaff)
        .options(joinedload(TenantStaff.tenant))
        .where(TenantStaff.user_id == user.id)
        .order_by(TenantStaff.added_at)
    )
    return [
        UserTenantSummary(
            id=row.tenant.id,
            name=row.tenant.name,
            slug=row.tenant.slug,
            status=row.tenant.status,
            role=row.role.value,
            logo_url=row.tenant.logo_url,
        )
        for row in rows.all()
    ]
```

- [ ] **Step 3: Test**

```python
@pytest.mark.asyncio
async def test_list_my_tenants_returns_owner_tenants(client, db_session):
    register = await client.post(
        "/auth/register",
        json={"email": "owner@example.com", "password": "pass12345", "full_name": "O"},
    )
    token = register.json()["access_token"]

    # Owner tạo 2 tenant
    await client.post(
        "/merchant/register", json={"name": "Shop A"},
        headers={"Authorization": f"Bearer {token}"},
    )
    await client.post(
        "/merchant/register", json={"name": "Shop B"},
        headers={"Authorization": f"Bearer {token}"},
    )

    response = await client.get(
        "/tenants/users/me/tenants",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    names = {t["name"] for t in data}
    assert names == {"Shop A", "Shop B"}
    assert all(t["role"] == "owner" for t in data)


@pytest.mark.asyncio
async def test_list_my_tenants_empty_for_new_user(client):
    register = await client.post(
        "/auth/register",
        json={"email": "new@example.com", "password": "pass12345", "full_name": "N"},
    )
    token = register.json()["access_token"]
    response = await client.get(
        "/tenants/users/me/tenants",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json() == []
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/tenants.py backend/app/schemas/tenant.py backend/tests/integration/test_tenants_api.py
git commit -m "feat(backend): thêm GET /tenants/users/me/tenants list tenant của user (★ fix I15)"
```

> **Frontend impact:** Task 38 (auth-store) hoặc Task 43 (TenantContextProvider) phải gọi endpoint này sau login để fetch danh sách tenant + auto-select 1 tenant nếu có 1 (hoặc hiển thị màn hình chọn nếu nhiều). Nếu list rỗng → redirect `/merchant/register`. Update Task 38/43/45 với logic này.

---

### Task 9: GET `/tenants/me` endpoint (lấy tenant hiện tại theo header)

**Files:**
- Modify: `D:/DoAn/backend/app/api/tenants.py`
- Modify: `D:/DoAn/backend/tests/integration/test_tenants_api.py`

> Lưu ý: endpoint này KHÔNG verify staff role (Task 13 sẽ verify), chỉ verify user đã đăng nhập + tenant tồn tại + status=active. Verify staff role sẽ được thêm trong Task 13.

- [ ] **Step 1: Append failing test**

```python
@pytest.mark.asyncio
async def test_get_tenant_me_returns_active_tenant(client, db_session):
    from app.models.tenant import TenantStatus
    from app.services.tenant_service import TenantService
    from app.schemas.tenant import TenantCreateRequest

    register = await client.post(
        "/auth/register",
        json={"email": "owner@example.com", "password": "pass12345", "full_name": "Owner"},
    )
    token = register.json()["access_token"]

    create_resp = await client.post(
        "/merchant/register",
        json={"name": "My Shop"},
        headers={"Authorization": f"Bearer {token}"},
    )
    tenant_id = create_resp.json()["id"]

    service = TenantService(db_session)
    await service.approve_tenant(tenant_id=tenant_id)
    await db_session.flush()

    response = await client.get(
        "/tenants/me",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Tenant-Id": str(tenant_id),
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == tenant_id
    assert data["status"] == "active"


@pytest.mark.asyncio
async def test_get_tenant_me_missing_header_returns_400(client):
    register = await client.post(
        "/auth/register",
        json={"email": "u@example.com", "password": "pass12345", "full_name": "U"},
    )
    token = register.json()["access_token"]

    response = await client.get(
        "/tenants/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_tenant_me_pending_tenant_returns_403(client, db_session):
    register = await client.post(
        "/auth/register",
        json={"email": "owner@example.com", "password": "pass12345", "full_name": "Owner"},
    )
    token = register.json()["access_token"]
    create_resp = await client.post(
        "/merchant/register",
        json={"name": "Pending"},
        headers={"Authorization": f"Bearer {token}"},
    )
    tenant_id = create_resp.json()["id"]

    response = await client.get(
        "/tenants/me",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Tenant-Id": str(tenant_id),
        },
    )
    assert response.status_code == 403  # Tenant chưa được duyệt
```

- [ ] **Step 2: Update `app/api/tenants.py`**

```python
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_user, get_tenant_id
from app.models.tenant import TenantStatus
from app.services.tenant_service import TenantNotFoundError


@router.get("/tenants/me", response_model=TenantResponse, tags=["tenants"])
async def get_my_tenant(
    tenant_id: int = Depends(get_tenant_id),
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TenantResponse:
    """Lấy thông tin tenant theo header X-Tenant-Id.

    Yêu cầu tenant.status == 'active'. Verify staff role chưa làm ở task này
    (sẽ thêm vào Task 13 sau khi có model TenantStaff).
    """
    service = TenantService(db)
    try:
        tenant = await service.get_tenant_by_id(tenant_id)
    except TenantNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    if tenant.status != TenantStatus.ACTIVE:
        raise HTTPException(
            status_code=403,
            detail=f"Tenant is {tenant.status.value}, not active",
        )

    return TenantResponse.model_validate(tenant)
```

> **Quan trọng:** prefix của router hiện tại là `/merchant`, nhưng endpoint này là `/tenants/me`. Có 2 cách: tách thành 2 router riêng, HOẶC đăng ký endpoint `/tenants/me` ở module riêng. Cách đơn giản: đổi tách thành 2 router trong cùng file.

Sửa lại `app/api/tenants.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user, get_tenant_id
from app.models.tenant import TenantStatus
from app.models.user import User
from app.schemas.tenant import TenantCreateRequest, TenantResponse
from app.services.tenant_service import TenantNotFoundError, TenantService

merchant_router = APIRouter(prefix="/merchant", tags=["merchant"])
tenants_router = APIRouter(prefix="/tenants", tags=["tenants"])


@merchant_router.post(
    "/register",
    response_model=TenantResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_tenant(
    request: TenantCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TenantResponse:
    service = TenantService(db)
    tenant = await service.create_tenant(owner=current_user, request=request)
    return TenantResponse.model_validate(tenant)


@tenants_router.get("/me", response_model=TenantResponse)
async def get_my_tenant(
    tenant_id: int = Depends(get_tenant_id),
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TenantResponse:
    service = TenantService(db)
    try:
        tenant = await service.get_tenant_by_id(tenant_id)
    except TenantNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    if tenant.status != TenantStatus.ACTIVE:
        raise HTTPException(
            status_code=403,
            detail=f"Tenant is {tenant.status.value}, not active",
        )

    return TenantResponse.model_validate(tenant)
```

- [ ] **Step 3: Update `app/main.py` đăng ký cả 2 router**

```python
from app.api import tenants as tenants_module

app.include_router(tenants_module.merchant_router)
app.include_router(tenants_module.tenants_router)
```

- [ ] **Step 4: Run tests → PASS**

```bash
pytest tests/integration/test_tenants_api.py -v
```

Expected: 9 passed

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/tenants.py backend/app/main.py backend/tests/integration/test_tenants_api.py
git commit -m "feat(backend): add GET /tenants/me with X-Tenant-Id header"
```

---

## PHASE 3 — Tenant Staff Model + Service + API (Luồng H)

### Task 10: Tạo `app/models/tenant_staff.py` + migration

**Files:**
- Create: `D:/DoAn/backend/app/models/tenant_staff.py`
- Modify: `D:/DoAn/backend/app/models/__init__.py`

- [ ] **Step 1: Tạo model**

```python
import enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.tenant import Tenant
    from app.models.user import User


class TenantStaffRole(str, enum.Enum):
    OWNER = "owner"
    STAFF = "staff"


class TenantStaff(Base, TimestampMixin):
    __tablename__ = "tenant_staff"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", name="uq_tenant_staff_tenant_user"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[TenantStaffRole] = mapped_column(
        Enum(TenantStaffRole, name="tenant_staff_role"), nullable=False
    )

    tenant: Mapped["Tenant"] = relationship("Tenant")
    user: Mapped["User"] = relationship("User")
```

- [ ] **Step 2: Update `app/models/__init__.py`**

```python
from app.models.tenant import Tenant, TenantStatus
from app.models.tenant_staff import TenantStaff, TenantStaffRole
from app.models.user import User

__all__ = ["User", "Tenant", "TenantStatus", "TenantStaff", "TenantStaffRole"]
```

- [ ] **Step 3: Generate + apply migration**

```bash
cd D:/DoAn/backend
alembic revision --autogenerate -m "create tenant_staff table"
alembic upgrade head
```

- [ ] **Step 4: Verify**

```bash
docker compose exec postgres psql -U loyalty -d loyalty -c "\d tenant_staff"
```

- [ ] **Step 5: Commit**

```bash
cd D:/DoAn
git add backend/app/models/tenant_staff.py backend/app/models/__init__.py backend/alembic/versions/
git commit -m "feat(backend): add TenantStaff model + migration"
```

---

### Task 11: Cập nhật `TenantService.create_tenant` để tự thêm owner vào `tenant_staff`

**Files:**
- Modify: `D:/DoAn/backend/app/services/tenant_service.py`
- Modify: `D:/DoAn/backend/tests/integration/test_tenant_service.py`

- [ ] **Step 1: Append failing test**

```python
from sqlalchemy import select
from app.models.tenant_staff import TenantStaff, TenantStaffRole


@pytest.mark.asyncio
async def test_create_tenant_auto_inserts_owner_into_tenant_staff(db_session):
    user = User(email="o@example.com", password_hash="x", is_active=True)
    db_session.add(user)
    await db_session.flush()

    service = TenantService(db_session)
    tenant = await service.create_tenant(
        owner=user, request=TenantCreateRequest(name="Auto Staff Shop")
    )
    await db_session.flush()

    staff = await db_session.scalar(
        select(TenantStaff).where(
            TenantStaff.tenant_id == tenant.id, TenantStaff.user_id == user.id
        )
    )
    assert staff is not None
    assert staff.role == TenantStaffRole.OWNER
```

- [ ] **Step 2: Run test → FAIL**

- [ ] **Step 3: Update `TenantService.create_tenant`**

Trong `app/services/tenant_service.py`, thêm import và sửa method:

```python
from app.models.tenant_staff import TenantStaff, TenantStaffRole


# Trong class TenantService, sửa create_tenant:
async def create_tenant(self, *, owner: User, request: TenantCreateRequest) -> Tenant:
    existing_slugs = set((await self.db.scalars(select(Tenant.slug))).all())
    slug = generate_unique_slug(request.name, existing_slugs)

    tenant = Tenant(
        name=request.name,
        slug=slug,
        owner_user_id=owner.id,
        status=TenantStatus.PENDING,
        description=request.description,
        logo_url=request.logo_url,
        settings={},
    )
    self.db.add(tenant)
    await self.db.flush()

    staff = TenantStaff(
        tenant_id=tenant.id,
        user_id=owner.id,
        role=TenantStaffRole.OWNER,
    )
    self.db.add(staff)
    await self.db.flush()
    await self.db.refresh(tenant)
    return tenant
```

- [ ] **Step 4: Run test → PASS**

```bash
pytest tests/integration/test_tenant_service.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/tenant_service.py backend/tests/integration/test_tenant_service.py
git commit -m "feat(backend): auto-insert owner into tenant_staff on tenant create"
```

---

### Task 12: TDD — `TenantStaffService` (add/remove/update role staff)

**Files:**
- Create: `D:/DoAn/backend/app/schemas/tenant_staff.py`
- Create: `D:/DoAn/backend/app/services/tenant_staff_service.py`
- Create: `D:/DoAn/backend/tests/integration/test_tenant_staff_service.py`

- [ ] **Step 1: Tạo schema `app/schemas/tenant_staff.py`**

```python
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.tenant_staff import TenantStaffRole


class StaffAddRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    role: TenantStaffRole = TenantStaffRole.STAFF


class StaffUpdateRoleRequest(BaseModel):
    role: TenantStaffRole


class StaffResponse(BaseModel):
    id: int
    tenant_id: int
    user_id: int
    role: TenantStaffRole
    user_email: str | None
    user_full_name: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class StaffAddResponse(BaseModel):
    """Response khi thêm staff. Nếu user mới (shadow), kèm verification_code (MVP)."""

    staff: StaffResponse
    verification_code: str | None = None  # Chỉ trả khi tạo shadow user mới
```

- [ ] **Step 2: Viết failing tests**

Tạo `tests/integration/test_tenant_staff_service.py`:

```python
import pytest
from sqlalchemy import select

from app.models.tenant import Tenant, TenantStatus
from app.models.tenant_staff import TenantStaff, TenantStaffRole
from app.models.user import User
from app.schemas.tenant_staff import StaffAddRequest, StaffUpdateRoleRequest
from app.services.tenant_staff_service import (
    StaffAlreadyInTenantError,
    StaffNotFoundError,
    TenantStaffService,
)


@pytest.fixture
async def active_tenant(db_session):
    owner = User(email="owner@example.com", password_hash="x", is_active=True)
    db_session.add(owner)
    await db_session.flush()

    tenant = Tenant(
        name="Test Shop",
        slug="test-shop",
        owner_user_id=owner.id,
        status=TenantStatus.ACTIVE,
        settings={},
    )
    db_session.add(tenant)
    await db_session.flush()

    db_session.add(TenantStaff(tenant_id=tenant.id, user_id=owner.id, role=TenantStaffRole.OWNER))
    await db_session.flush()

    return tenant, owner


@pytest.mark.asyncio
async def test_add_staff_existing_user(db_session, active_tenant):
    tenant, _owner = active_tenant
    existing = User(email="staff@example.com", password_hash="x", is_active=True)
    db_session.add(existing)
    await db_session.flush()

    service = TenantStaffService(db_session)
    result = await service.add_staff(
        tenant_id=tenant.id,
        request=StaffAddRequest(
            email="staff@example.com", full_name="Existing Staff", role=TenantStaffRole.STAFF
        ),
    )
    assert result.staff.user_id == existing.id
    assert result.staff.role == TenantStaffRole.STAFF
    assert result.verification_code is None  # Không phải shadow


@pytest.mark.asyncio
async def test_add_staff_new_user_creates_shadow_with_verification_code(
    db_session, active_tenant
):
    tenant, _owner = active_tenant
    service = TenantStaffService(db_session)
    result = await service.add_staff(
        tenant_id=tenant.id,
        request=StaffAddRequest(
            email="new@example.com", full_name="New Staff", role=TenantStaffRole.STAFF
        ),
    )
    assert result.staff.user_id is not None
    assert result.verification_code is not None
    assert len(result.verification_code) == 6  # Code 6 số
    assert result.verification_code.isdigit()

    user = await db_session.get(User, result.staff.user_id)
    assert user.is_shadow is True
    assert user.email == "new@example.com"


@pytest.mark.asyncio
async def test_add_staff_already_in_tenant_raises(db_session, active_tenant):
    tenant, _owner = active_tenant
    service = TenantStaffService(db_session)
    await service.add_staff(
        tenant_id=tenant.id,
        request=StaffAddRequest(
            email="dup@example.com", full_name="Dup", role=TenantStaffRole.STAFF
        ),
    )
    await db_session.flush()

    with pytest.raises(StaffAlreadyInTenantError):
        await service.add_staff(
            tenant_id=tenant.id,
            request=StaffAddRequest(
                email="dup@example.com", full_name="Dup2", role=TenantStaffRole.STAFF
            ),
        )


@pytest.mark.asyncio
async def test_remove_staff(db_session, active_tenant):
    tenant, _owner = active_tenant
    service = TenantStaffService(db_session)
    result = await service.add_staff(
        tenant_id=tenant.id,
        request=StaffAddRequest(
            email="remove@example.com", full_name="R", role=TenantStaffRole.STAFF
        ),
    )
    await db_session.flush()

    await service.remove_staff(tenant_id=tenant.id, staff_id=result.staff.id)
    await db_session.flush()

    found = await db_session.get(TenantStaff, result.staff.id)
    assert found is None


@pytest.mark.asyncio
async def test_update_role(db_session, active_tenant):
    tenant, _owner = active_tenant
    service = TenantStaffService(db_session)
    result = await service.add_staff(
        tenant_id=tenant.id,
        request=StaffAddRequest(
            email="staff@example.com", full_name="S", role=TenantStaffRole.STAFF
        ),
    )
    await db_session.flush()

    updated = await service.update_role(
        tenant_id=tenant.id,
        staff_id=result.staff.id,
        request=StaffUpdateRoleRequest(role=TenantStaffRole.OWNER),
    )
    assert updated.role == TenantStaffRole.OWNER


@pytest.mark.asyncio
async def test_list_staff_returns_only_tenant_members(db_session, active_tenant):
    tenant, owner = active_tenant
    service = TenantStaffService(db_session)
    await service.add_staff(
        tenant_id=tenant.id,
        request=StaffAddRequest(
            email="s1@example.com", full_name="S1", role=TenantStaffRole.STAFF
        ),
    )
    await db_session.flush()

    staff_list = await service.list_staff(tenant_id=tenant.id)
    emails = [s.user_email for s in staff_list]
    assert "owner@example.com" in emails
    assert "s1@example.com" in emails
    assert len(staff_list) == 2
```

- [ ] **Step 3: Run test → FAIL**

- [ ] **Step 4: Implement `app/services/tenant_staff_service.py`**

```python
import secrets

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.security import hash_password
from app.models.tenant_staff import TenantStaff, TenantStaffRole
from app.models.user import User
from app.schemas.tenant_staff import (
    StaffAddRequest,
    StaffAddResponse,
    StaffResponse,
    StaffUpdateRoleRequest,
)


class StaffNotFoundError(Exception):
    pass


class StaffAlreadyInTenantError(Exception):
    pass


def _generate_verification_code() -> str:
    """Sinh code 6 số ngẫu nhiên (cryptographically secure)."""
    return f"{secrets.randbelow(1_000_000):06d}"


class TenantStaffService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_staff(
        self, *, tenant_id: int, request: StaffAddRequest
    ) -> StaffAddResponse:
        existing_user = await self.db.scalar(
            select(User).where(User.email == request.email)
        )

        verification_code: str | None = None

        if existing_user is None:
            # Tạo shadow user
            verification_code = _generate_verification_code()
            existing_user = User(
                email=request.email,
                full_name=request.full_name,
                password_hash=hash_password(verification_code),  # tạm — sẽ replace khi claim
                is_active=True,
                is_shadow=True,
                system_role="regular",
            )
            self.db.add(existing_user)
            await self.db.flush()

        # Check đã có trong tenant_staff chưa
        existing_link = await self.db.scalar(
            select(TenantStaff).where(
                TenantStaff.tenant_id == tenant_id,
                TenantStaff.user_id == existing_user.id,
            )
        )
        if existing_link is not None:
            raise StaffAlreadyInTenantError(
                f"User {request.email} already in tenant {tenant_id}"
            )

        staff = TenantStaff(
            tenant_id=tenant_id,
            user_id=existing_user.id,
            role=request.role,
        )
        self.db.add(staff)
        await self.db.flush()
        await self.db.refresh(staff)

        return StaffAddResponse(
            staff=StaffResponse(
                id=staff.id,
                tenant_id=staff.tenant_id,
                user_id=staff.user_id,
                role=staff.role,
                user_email=existing_user.email,
                user_full_name=existing_user.full_name,
                created_at=staff.created_at,
            ),
            verification_code=verification_code,
        )

    async def remove_staff(self, *, tenant_id: int, staff_id: int) -> None:
        staff = await self.db.get(TenantStaff, staff_id)
        if staff is None or staff.tenant_id != tenant_id:
            raise StaffNotFoundError(f"Staff {staff_id} not in tenant {tenant_id}")
        await self.db.delete(staff)
        await self.db.flush()

    async def update_role(
        self, *, tenant_id: int, staff_id: int, request: StaffUpdateRoleRequest
    ) -> StaffResponse:
        staff = await self.db.scalar(
            select(TenantStaff)
            .options(joinedload(TenantStaff.user))
            .where(TenantStaff.id == staff_id, TenantStaff.tenant_id == tenant_id)
        )
        if staff is None:
            raise StaffNotFoundError(f"Staff {staff_id} not in tenant {tenant_id}")
        staff.role = request.role
        await self.db.flush()
        return StaffResponse(
            id=staff.id,
            tenant_id=staff.tenant_id,
            user_id=staff.user_id,
            role=staff.role,
            user_email=staff.user.email,
            user_full_name=staff.user.full_name,
            created_at=staff.created_at,
        )

    async def list_staff(self, *, tenant_id: int) -> list[StaffResponse]:
        rows = await self.db.scalars(
            select(TenantStaff)
            .options(joinedload(TenantStaff.user))
            .where(TenantStaff.tenant_id == tenant_id)
            .order_by(TenantStaff.created_at)
        )
        return [
            StaffResponse(
                id=s.id,
                tenant_id=s.tenant_id,
                user_id=s.user_id,
                role=s.role,
                user_email=s.user.email,
                user_full_name=s.user.full_name,
                created_at=s.created_at,
            )
            for s in rows
        ]
```

- [ ] **Step 5: Run test → PASS**

```bash
pytest tests/integration/test_tenant_staff_service.py -v
```

Expected: 6 passed

- [ ] **Step 6: Commit**

```bash
git add backend/app/schemas/tenant_staff.py backend/app/services/tenant_staff_service.py backend/tests/integration/test_tenant_staff_service.py
git commit -m "feat(backend): add TenantStaffService for Luồng H (TDD)"
```

---

### Task 13: API endpoints `/merchant/staff` + dependency `require_owner_in_tenant`

**Files:**
- Modify: `D:/DoAn/backend/app/core/deps.py`
- Create: `D:/DoAn/backend/app/api/tenant_staff.py`
- Create: `D:/DoAn/backend/tests/integration/test_tenant_staff_api.py`
- Modify: `D:/DoAn/backend/app/main.py`

- [ ] **Step 1: Thêm dependencies vào `app/core/deps.py`**

Append vào file:

```python
from sqlalchemy import select

from app.core.tenant_cache import tenant_role_cache
from app.models.tenant_staff import TenantStaff, TenantStaffRole


async def get_current_tenant_role(
    user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> TenantStaffRole:
    """Lấy role của current user trong current tenant.

    1. Lookup cache (TTL 60s)
    2. Cache miss → query DB tenant_staff
    3. Không có row → raise 403
    """
    cached = tenant_role_cache.get(user_id=user.id, tenant_id=tenant_id)
    if cached is not None:
        return TenantStaffRole(cached)

    staff = await db.scalar(
        select(TenantStaff).where(
            TenantStaff.tenant_id == tenant_id,
            TenantStaff.user_id == user.id,
        )
    )
    if staff is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User not in tenant {tenant_id}",
        )
    tenant_role_cache.set(user_id=user.id, tenant_id=tenant_id, role=staff.role.value)
    return staff.role


async def require_staff_in_tenant(
    role: TenantStaffRole = Depends(get_current_tenant_role),
) -> TenantStaffRole:
    """Dependency: user phải là staff hoặc owner của tenant."""
    return role


async def require_owner_in_tenant(
    role: TenantStaffRole = Depends(get_current_tenant_role),
) -> TenantStaffRole:
    """Dependency: user phải là owner của tenant."""
    if role != TenantStaffRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Owner access required",
        )
    return role
```

> Lưu ý import circular: `deps.py` import `TenantStaff` từ `models`, mà `models/tenant_staff.py` import `Base`. Không có vòng lặp vì `tenant_staff.py` không import từ `deps.py`.

- [ ] **Step 2: Cập nhật `tests/conftest.py` thêm fixture clear cache**

Append vào `conftest.py`:

```python
@pytest_asyncio.fixture(autouse=True)
async def clear_tenant_cache():
    from app.core.tenant_cache import tenant_role_cache
    tenant_role_cache.clear()
    yield
    tenant_role_cache.clear()
```

- [ ] **Step 3: Viết failing tests**

Tạo `tests/integration/test_tenant_staff_api.py`:

```python
import pytest

from app.core.security import create_access_token
from app.models.tenant import Tenant, TenantStatus
from app.models.tenant_staff import TenantStaff, TenantStaffRole
from app.models.user import User


async def _make_active_tenant_with_owner(db_session):
    owner = User(email="owner@example.com", password_hash="x", is_active=True)
    db_session.add(owner)
    await db_session.flush()
    tenant = Tenant(
        name="Test Shop",
        slug="test-shop",
        owner_user_id=owner.id,
        status=TenantStatus.ACTIVE,
        settings={},
    )
    db_session.add(tenant)
    await db_session.flush()
    db_session.add(
        TenantStaff(tenant_id=tenant.id, user_id=owner.id, role=TenantStaffRole.OWNER)
    )
    await db_session.flush()
    return tenant, owner, create_access_token(user_id=owner.id)


@pytest.mark.asyncio
async def test_add_staff_returns_201_with_verification_code(client, db_session):
    tenant, _owner, owner_token = await _make_active_tenant_with_owner(db_session)

    response = await client.post(
        "/merchant/staff",
        json={"email": "newstaff@example.com", "full_name": "New", "role": "staff"},
        headers={
            "Authorization": f"Bearer {owner_token}",
            "X-Tenant-Id": str(tenant.id),
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["staff"]["role"] == "staff"
    assert data["verification_code"] is not None
    assert len(data["verification_code"]) == 6


@pytest.mark.asyncio
async def test_add_staff_non_owner_returns_403(client, db_session):
    tenant, _owner, _ = await _make_active_tenant_with_owner(db_session)

    staff_user = User(email="s@example.com", password_hash="x", is_active=True)
    db_session.add(staff_user)
    await db_session.flush()
    db_session.add(
        TenantStaff(tenant_id=tenant.id, user_id=staff_user.id, role=TenantStaffRole.STAFF)
    )
    await db_session.flush()
    staff_token = create_access_token(user_id=staff_user.id)

    response = await client.post(
        "/merchant/staff",
        json={"email": "x@example.com", "full_name": "X", "role": "staff"},
        headers={
            "Authorization": f"Bearer {staff_token}",
            "X-Tenant-Id": str(tenant.id),
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_staff_owner_sees_all(client, db_session):
    tenant, _owner, owner_token = await _make_active_tenant_with_owner(db_session)
    await client.post(
        "/merchant/staff",
        json={"email": "s1@example.com", "full_name": "S1", "role": "staff"},
        headers={
            "Authorization": f"Bearer {owner_token}",
            "X-Tenant-Id": str(tenant.id),
        },
    )

    response = await client.get(
        "/merchant/staff",
        headers={
            "Authorization": f"Bearer {owner_token}",
            "X-Tenant-Id": str(tenant.id),
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2  # owner + s1


@pytest.mark.asyncio
async def test_remove_staff(client, db_session):
    tenant, _owner, owner_token = await _make_active_tenant_with_owner(db_session)
    add = await client.post(
        "/merchant/staff",
        json={"email": "s@example.com", "full_name": "S", "role": "staff"},
        headers={
            "Authorization": f"Bearer {owner_token}",
            "X-Tenant-Id": str(tenant.id),
        },
    )
    staff_id = add.json()["staff"]["id"]

    response = await client.delete(
        f"/merchant/staff/{staff_id}",
        headers={
            "Authorization": f"Bearer {owner_token}",
            "X-Tenant-Id": str(tenant.id),
        },
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_missing_tenant_header_returns_400(client, db_session):
    _tenant, _owner, owner_token = await _make_active_tenant_with_owner(db_session)

    response = await client.get(
        "/merchant/staff",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert response.status_code == 400
```

- [ ] **Step 4: Tạo `app/api/tenant_staff.py`**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_tenant_id, require_owner_in_tenant
from app.core.tenant_cache import tenant_role_cache
from app.models.tenant_staff import TenantStaffRole
from app.schemas.tenant_staff import (
    StaffAddRequest,
    StaffAddResponse,
    StaffResponse,
    StaffUpdateRoleRequest,
)
from app.services.tenant_staff_service import (
    StaffAlreadyInTenantError,
    StaffNotFoundError,
    TenantStaffService,
)

router = APIRouter(prefix="/merchant/staff", tags=["merchant-staff"])


@router.post("", response_model=StaffAddResponse, status_code=status.HTTP_201_CREATED)
async def add_staff(
    request: StaffAddRequest,
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_owner_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> StaffAddResponse:
    service = TenantStaffService(db)
    try:
        return await service.add_staff(tenant_id=tenant_id, request=request)
    except StaffAlreadyInTenantError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e


@router.get("", response_model=list[StaffResponse])
async def list_staff(
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_owner_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> list[StaffResponse]:
    service = TenantStaffService(db)
    return await service.list_staff(tenant_id=tenant_id)


@router.patch("/{staff_id}", response_model=StaffResponse)
async def update_staff_role(
    staff_id: int,
    body: StaffUpdateRoleRequest,
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_owner_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> StaffResponse:
    service = TenantStaffService(db)
    try:
        result = await service.update_role(
            tenant_id=tenant_id, staff_id=staff_id, request=body
        )
    except StaffNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    tenant_role_cache.invalidate(user_id=result.user_id, tenant_id=tenant_id)
    return result


@router.delete("/{staff_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_staff(
    staff_id: int,
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_owner_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = TenantStaffService(db)
    # Lấy user_id trước khi xóa để invalidate cache
    from sqlalchemy import select
    from app.models.tenant_staff import TenantStaff

    staff = await db.scalar(
        select(TenantStaff).where(
            TenantStaff.id == staff_id, TenantStaff.tenant_id == tenant_id
        )
    )
    try:
        await service.remove_staff(tenant_id=tenant_id, staff_id=staff_id)
    except StaffNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    if staff is not None:
        tenant_role_cache.invalidate(user_id=staff.user_id, tenant_id=tenant_id)
```

- [ ] **Step 5: Update `app/main.py`**

```python
from app.api import tenant_staff as tenant_staff_router

app.include_router(tenant_staff_router.router)
```

- [ ] **Step 6: Run tests → PASS**

```bash
pytest tests/integration/test_tenant_staff_api.py -v
```

Expected: 5 passed

- [ ] **Step 7: Commit**

```bash
git add backend/app/api/tenant_staff.py backend/app/core/deps.py backend/app/main.py backend/tests/conftest.py backend/tests/integration/test_tenant_staff_api.py
git commit -m "feat(backend): add /merchant/staff endpoints with require_owner_in_tenant"
```

---

## PHASE 4 — Tiers Model + Service + API

### Task 14: Tạo model `Tier` + migration

**Files:**
- Create: `D:/DoAn/backend/app/models/tier.py`
- Modify: `D:/DoAn/backend/app/models/__init__.py`

- [ ] **Step 1: Tạo `app/models/tier.py`**

```python
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Tier(Base, TimestampMixin):
    __tablename__ = "tiers"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    min_points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    perks: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index("ix_tiers_tenant_min_points", "tenant_id", "min_points"),
    )
```

- [ ] **Step 2: Update `app/models/__init__.py`**

```python
from app.models.tenant import Tenant, TenantStatus
from app.models.tenant_staff import TenantStaff, TenantStaffRole
from app.models.tier import Tier
from app.models.user import User

__all__ = ["User", "Tenant", "TenantStatus", "TenantStaff", "TenantStaffRole", "Tier"]
```

- [ ] **Step 3: Generate + apply migration**

```bash
cd D:/DoAn/backend
alembic revision --autogenerate -m "create tiers table"
alembic upgrade head
```

- [ ] **Step 4: Verify**

```bash
docker compose exec postgres psql -U loyalty -d loyalty -c "\d tiers"
```

- [ ] **Step 5: Commit**

```bash
cd D:/DoAn
git add backend/app/models/tier.py backend/app/models/__init__.py backend/alembic/versions/
git commit -m "feat(backend): add Tier model + migration"
```

---

### Task 15: Tạo Pydantic schemas + TierService TDD

**Files:**
- Create: `D:/DoAn/backend/app/schemas/tier.py`
- Create: `D:/DoAn/backend/app/services/tier_service.py`
- Create: `D:/DoAn/backend/tests/integration/test_tier_service.py`

- [ ] **Step 1: Tạo schema `app/schemas/tier.py`**

```python
from datetime import datetime

from pydantic import BaseModel, Field


class TierCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    min_points: int = Field(ge=0)
    perks: dict = Field(default_factory=dict)


class TierUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    min_points: int | None = Field(default=None, ge=0)
    perks: dict | None = None
    is_active: bool | None = None


class TierResponse(BaseModel):
    id: int
    tenant_id: int
    name: str
    min_points: int
    perks: dict
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 2: Viết failing tests**

Tạo `tests/integration/test_tier_service.py`:

```python
import pytest

from app.models.tenant import Tenant, TenantStatus
from app.models.tier import Tier
from app.models.user import User
from app.schemas.tier import TierCreateRequest, TierUpdateRequest
from app.services.tier_service import TierNotFoundError, TierService


@pytest.fixture
async def active_tenant(db_session):
    user = User(email="o@example.com", password_hash="x", is_active=True)
    db_session.add(user)
    await db_session.flush()
    tenant = Tenant(
        name="T", slug="t", owner_user_id=user.id, status=TenantStatus.ACTIVE, settings={}
    )
    db_session.add(tenant)
    await db_session.flush()
    return tenant


@pytest.mark.asyncio
async def test_create_tier(db_session, active_tenant):
    service = TierService(db_session)
    tier = await service.create_tier(
        tenant_id=active_tenant.id,
        request=TierCreateRequest(name="Bronze", min_points=0),
    )
    assert tier.id is not None
    assert tier.name == "Bronze"
    assert tier.min_points == 0
    assert tier.is_active is True
    assert tier.deleted_at is None


@pytest.mark.asyncio
async def test_list_tiers_excludes_soft_deleted(db_session, active_tenant):
    service = TierService(db_session)
    bronze = await service.create_tier(
        tenant_id=active_tenant.id, request=TierCreateRequest(name="Bronze", min_points=0)
    )
    silver = await service.create_tier(
        tenant_id=active_tenant.id, request=TierCreateRequest(name="Silver", min_points=500)
    )
    await db_session.flush()
    await service.delete_tier(tenant_id=active_tenant.id, tier_id=bronze.id)
    await db_session.flush()

    tiers = await service.list_tiers(tenant_id=active_tenant.id)
    names = [t.name for t in tiers]
    assert "Silver" in names
    assert "Bronze" not in names


@pytest.mark.asyncio
async def test_list_tiers_sorted_by_min_points(db_session, active_tenant):
    service = TierService(db_session)
    await service.create_tier(
        tenant_id=active_tenant.id, request=TierCreateRequest(name="Gold", min_points=2000)
    )
    await service.create_tier(
        tenant_id=active_tenant.id, request=TierCreateRequest(name="Bronze", min_points=0)
    )
    await service.create_tier(
        tenant_id=active_tenant.id, request=TierCreateRequest(name="Silver", min_points=500)
    )
    await db_session.flush()

    tiers = await service.list_tiers(tenant_id=active_tenant.id)
    assert [t.name for t in tiers] == ["Bronze", "Silver", "Gold"]


@pytest.mark.asyncio
async def test_update_tier(db_session, active_tenant):
    service = TierService(db_session)
    tier = await service.create_tier(
        tenant_id=active_tenant.id, request=TierCreateRequest(name="Bronze", min_points=0)
    )
    await db_session.flush()

    updated = await service.update_tier(
        tenant_id=active_tenant.id,
        tier_id=tier.id,
        request=TierUpdateRequest(name="Bronze+", min_points=100),
    )
    assert updated.name == "Bronze+"
    assert updated.min_points == 100


@pytest.mark.asyncio
async def test_update_tier_wrong_tenant_raises(db_session, active_tenant):
    service = TierService(db_session)
    tier = await service.create_tier(
        tenant_id=active_tenant.id, request=TierCreateRequest(name="X", min_points=0)
    )
    await db_session.flush()

    with pytest.raises(TierNotFoundError):
        await service.update_tier(
            tenant_id=99999,
            tier_id=tier.id,
            request=TierUpdateRequest(name="hacked"),
        )
```

- [ ] **Step 3: Run test → FAIL**

- [ ] **Step 4: Implement `app/services/tier_service.py`**

```python
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tier import Tier
from app.schemas.tier import TierCreateRequest, TierUpdateRequest


class TierNotFoundError(Exception):
    pass


class TierService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_tier(self, *, tenant_id: int, request: TierCreateRequest) -> Tier:
        tier = Tier(
            tenant_id=tenant_id,
            name=request.name,
            min_points=request.min_points,
            perks=request.perks,
            is_active=True,
        )
        self.db.add(tier)
        await self.db.flush()
        await self.db.refresh(tier)
        return tier

    async def get_tier(self, *, tenant_id: int, tier_id: int) -> Tier:
        tier = await self.db.scalar(
            select(Tier).where(
                Tier.id == tier_id,
                Tier.tenant_id == tenant_id,
                Tier.deleted_at.is_(None),
            )
        )
        if tier is None:
            raise TierNotFoundError(
                f"Tier {tier_id} not found in tenant {tenant_id}"
            )
        return tier

    async def list_tiers(self, *, tenant_id: int) -> list[Tier]:
        rows = await self.db.scalars(
            select(Tier)
            .where(Tier.tenant_id == tenant_id, Tier.deleted_at.is_(None))
            .order_by(Tier.min_points.asc())
        )
        return list(rows.all())

    async def update_tier(
        self, *, tenant_id: int, tier_id: int, request: TierUpdateRequest
    ) -> Tier:
        tier = await self.get_tier(tenant_id=tenant_id, tier_id=tier_id)
        for field, value in request.model_dump(exclude_unset=True).items():
            setattr(tier, field, value)
        await self.db.flush()
        return tier

    async def delete_tier(self, *, tenant_id: int, tier_id: int) -> None:
        """Soft delete: set deleted_at."""
        tier = await self.get_tier(tenant_id=tenant_id, tier_id=tier_id)
        tier.deleted_at = datetime.now(timezone.utc)
        tier.is_active = False
        await self.db.flush()
```

- [ ] **Step 5: Run test → PASS**

```bash
pytest tests/integration/test_tier_service.py -v
```

Expected: 5 passed

- [ ] **Step 6: Commit**

```bash
git add backend/app/schemas/tier.py backend/app/services/tier_service.py backend/tests/integration/test_tier_service.py
git commit -m "feat(backend): add TierService with CRUD + soft delete (TDD)"
```

---

### Task 16: API endpoints `/merchant/tiers`

**Files:**
- Create: `D:/DoAn/backend/app/api/tiers.py`
- Create: `D:/DoAn/backend/tests/integration/test_tiers_api.py`
- Modify: `D:/DoAn/backend/app/main.py`

- [ ] **Step 1: Viết failing tests**

Tạo `tests/integration/test_tiers_api.py`:

```python
import pytest

from app.core.security import create_access_token
from app.models.tenant import Tenant, TenantStatus
from app.models.tenant_staff import TenantStaff, TenantStaffRole
from app.models.user import User


async def _setup_owner(db_session):
    owner = User(email="o@example.com", password_hash="x", is_active=True)
    db_session.add(owner)
    await db_session.flush()
    tenant = Tenant(
        name="Shop", slug="shop", owner_user_id=owner.id,
        status=TenantStatus.ACTIVE, settings={}
    )
    db_session.add(tenant)
    await db_session.flush()
    db_session.add(
        TenantStaff(tenant_id=tenant.id, user_id=owner.id, role=TenantStaffRole.OWNER)
    )
    await db_session.flush()
    return tenant, owner, create_access_token(user_id=owner.id)


@pytest.mark.asyncio
async def test_create_tier(client, db_session):
    tenant, _owner, token = await _setup_owner(db_session)
    response = await client.post(
        "/merchant/tiers",
        json={"name": "Bronze", "min_points": 0},
        headers={"Authorization": f"Bearer {token}", "X-Tenant-Id": str(tenant.id)},
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Bronze"


@pytest.mark.asyncio
async def test_list_tiers(client, db_session):
    tenant, _owner, token = await _setup_owner(db_session)
    headers = {"Authorization": f"Bearer {token}", "X-Tenant-Id": str(tenant.id)}
    await client.post("/merchant/tiers", json={"name": "Silver", "min_points": 500}, headers=headers)
    await client.post("/merchant/tiers", json={"name": "Bronze", "min_points": 0}, headers=headers)

    response = await client.get("/merchant/tiers", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert [t["name"] for t in data] == ["Bronze", "Silver"]  # sort by min_points


@pytest.mark.asyncio
async def test_update_tier(client, db_session):
    tenant, _owner, token = await _setup_owner(db_session)
    headers = {"Authorization": f"Bearer {token}", "X-Tenant-Id": str(tenant.id)}
    create = await client.post(
        "/merchant/tiers", json={"name": "Bronze", "min_points": 0}, headers=headers
    )
    tier_id = create.json()["id"]

    response = await client.patch(
        f"/merchant/tiers/{tier_id}",
        json={"min_points": 100},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["min_points"] == 100


@pytest.mark.asyncio
async def test_delete_tier_soft_deletes(client, db_session):
    tenant, _owner, token = await _setup_owner(db_session)
    headers = {"Authorization": f"Bearer {token}", "X-Tenant-Id": str(tenant.id)}
    create = await client.post(
        "/merchant/tiers", json={"name": "Bronze", "min_points": 0}, headers=headers
    )
    tier_id = create.json()["id"]

    response = await client.delete(f"/merchant/tiers/{tier_id}", headers=headers)
    assert response.status_code == 204

    list_resp = await client.get("/merchant/tiers", headers=headers)
    assert all(t["id"] != tier_id for t in list_resp.json())


@pytest.mark.asyncio
async def test_create_tier_non_owner_returns_403(client, db_session):
    tenant, _owner, _ = await _setup_owner(db_session)
    staff_user = User(email="s@example.com", password_hash="x", is_active=True)
    db_session.add(staff_user)
    await db_session.flush()
    db_session.add(
        TenantStaff(tenant_id=tenant.id, user_id=staff_user.id, role=TenantStaffRole.STAFF)
    )
    await db_session.flush()
    staff_token = create_access_token(user_id=staff_user.id)

    response = await client.post(
        "/merchant/tiers",
        json={"name": "X", "min_points": 0},
        headers={"Authorization": f"Bearer {staff_token}", "X-Tenant-Id": str(tenant.id)},
    )
    assert response.status_code == 403
```

- [ ] **Step 2: Tạo `app/api/tiers.py`**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import (
    get_tenant_id,
    require_owner_in_tenant,
    require_staff_in_tenant,
)
from app.models.tenant_staff import TenantStaffRole
from app.schemas.tier import TierCreateRequest, TierResponse, TierUpdateRequest
from app.services.tier_service import TierNotFoundError, TierService

router = APIRouter(prefix="/merchant/tiers", tags=["merchant-tiers"])


@router.post("", response_model=TierResponse, status_code=status.HTTP_201_CREATED)
async def create_tier(
    request: TierCreateRequest,
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_owner_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> TierResponse:
    service = TierService(db)
    tier = await service.create_tier(tenant_id=tenant_id, request=request)
    return TierResponse.model_validate(tier)


@router.get("", response_model=list[TierResponse])
async def list_tiers(
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_staff_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> list[TierResponse]:
    service = TierService(db)
    tiers = await service.list_tiers(tenant_id=tenant_id)
    return [TierResponse.model_validate(t) for t in tiers]


@router.patch("/{tier_id}", response_model=TierResponse)
async def update_tier(
    tier_id: int,
    request: TierUpdateRequest,
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_owner_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> TierResponse:
    service = TierService(db)
    try:
        tier = await service.update_tier(
            tenant_id=tenant_id, tier_id=tier_id, request=request
        )
    except TierNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return TierResponse.model_validate(tier)


@router.delete("/{tier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tier(
    tier_id: int,
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_owner_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = TierService(db)
    try:
        await service.delete_tier(tenant_id=tenant_id, tier_id=tier_id)
    except TierNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
```

- [ ] **Step 3: Update `app/main.py`**

```python
from app.api import tiers as tiers_router

app.include_router(tiers_router.router)
```

- [ ] **Step 4: Run tests → PASS**

```bash
pytest tests/integration/test_tiers_api.py -v
```

Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/tiers.py backend/app/main.py backend/tests/integration/test_tiers_api.py
git commit -m "feat(backend): add /merchant/tiers CRUD endpoints"
```

---

### Task 17: Cross-tenant test cho tiers

**Files:**
- Modify: `D:/DoAn/backend/tests/integration/test_tiers_api.py`

- [ ] **Step 1: Append failing test**

```python
@pytest.mark.asyncio
async def test_owner_cannot_access_other_tenant_tiers(client, db_session):
    """Owner của tenant A không được CRUD tier của tenant B."""
    tenant_a, _, token_a = await _setup_owner(db_session)

    owner_b = User(email="ob@example.com", password_hash="x", is_active=True)
    db_session.add(owner_b)
    await db_session.flush()
    tenant_b = Tenant(
        name="Shop B", slug="shop-b", owner_user_id=owner_b.id,
        status=TenantStatus.ACTIVE, settings={},
    )
    db_session.add(tenant_b)
    await db_session.flush()
    db_session.add(
        TenantStaff(tenant_id=tenant_b.id, user_id=owner_b.id, role=TenantStaffRole.OWNER)
    )
    await db_session.flush()
    token_b = create_access_token(user_id=owner_b.id)

    create = await client.post(
        "/merchant/tiers",
        json={"name": "B-Bronze", "min_points": 0},
        headers={"Authorization": f"Bearer {token_b}", "X-Tenant-Id": str(tenant_b.id)},
    )
    tier_b_id = create.json()["id"]

    # Owner A cố cập nhật tier của B
    response = await client.patch(
        f"/merchant/tiers/{tier_b_id}",
        json={"name": "hacked"},
        headers={"Authorization": f"Bearer {token_a}", "X-Tenant-Id": str(tenant_a.id)},
    )
    # Không tìm thấy tier_b_id trong tenant_a → 404 (đúng — không leak existence)
    assert response.status_code == 404
```

- [ ] **Step 2: Run test → PASS**

```bash
pytest tests/integration/test_tiers_api.py -v
```

Expected: 6 passed

- [ ] **Step 3: Commit**

```bash
git add backend/tests/integration/test_tiers_api.py
git commit -m "test(backend): add cross-tenant isolation test for tiers"
```

---

## PHASE 5 — Point Rules Module

### Task 18: Tạo model `PointRule` + migration

**Files:**
- Create: `D:/DoAn/backend/app/models/point_rule.py`
- Modify: `D:/DoAn/backend/app/models/__init__.py`

- [ ] **Step 1: Tạo `app/models/point_rule.py`**

```python
from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Index, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class PointRule(Base, TimestampMixin):
    __tablename__ = "point_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    points_per_unit: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False
    )  # vd 1.00 điểm / 1000 VND
    unit_amount: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1000
    )  # đơn vị tiền (vd 1000 VND)
    min_amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        Index(
            "uq_point_rules_tenant_active",
            "tenant_id",
            unique=True,
            postgresql_where="is_active = true",
        ),
    )
```

- [ ] **Step 2: Update `app/models/__init__.py`**

```python
from app.models.point_rule import PointRule
from app.models.tenant import Tenant, TenantStatus
from app.models.tenant_staff import TenantStaff, TenantStaffRole
from app.models.tier import Tier
from app.models.user import User

__all__ = [
    "User", "Tenant", "TenantStatus", "TenantStaff", "TenantStaffRole",
    "Tier", "PointRule",
]
```

- [ ] **Step 3: Generate + apply migration**

```bash
cd D:/DoAn/backend
alembic revision --autogenerate -m "create point_rules table"
alembic upgrade head
```

- [ ] **Step 4: Verify partial unique index**

```bash
docker compose exec postgres psql -U loyalty -d loyalty -c "\d point_rules"
```

Expected: thấy index `uq_point_rules_tenant_active` với `WHERE (is_active = true)`.

- [ ] **Step 5: Commit**

```bash
cd D:/DoAn
git add backend/app/models/point_rule.py backend/app/models/__init__.py backend/alembic/versions/
git commit -m "feat(backend): add PointRule model with partial unique index"
```

---

### Task 19: TDD — `PointRuleService`

**Files:**
- Create: `D:/DoAn/backend/app/schemas/point_rule.py`
- Create: `D:/DoAn/backend/app/services/point_rule_service.py`
- Create: `D:/DoAn/backend/tests/integration/test_point_rule_service.py`

- [ ] **Step 1: Tạo schema**

```python
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class PointRuleCreateRequest(BaseModel):
    points_per_unit: Decimal = Field(gt=0)
    unit_amount: int = Field(default=1000, gt=0)
    min_amount: int = Field(default=0, ge=0)


class PointRuleResponse(BaseModel):
    id: int
    tenant_id: int
    points_per_unit: Decimal
    unit_amount: int
    min_amount: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 2: Viết failing tests**

Tạo `tests/integration/test_point_rule_service.py`:

```python
from decimal import Decimal

import pytest

from app.models.tenant import Tenant, TenantStatus
from app.models.user import User
from app.schemas.point_rule import PointRuleCreateRequest
from app.services.point_rule_service import PointRuleService


@pytest.fixture
async def active_tenant(db_session):
    user = User(email="o@example.com", password_hash="x", is_active=True)
    db_session.add(user)
    await db_session.flush()
    tenant = Tenant(
        name="T", slug="t", owner_user_id=user.id, status=TenantStatus.ACTIVE, settings={}
    )
    db_session.add(tenant)
    await db_session.flush()
    return tenant


@pytest.mark.asyncio
async def test_create_first_active_rule(db_session, active_tenant):
    service = PointRuleService(db_session)
    rule = await service.create_rule(
        tenant_id=active_tenant.id,
        request=PointRuleCreateRequest(
            points_per_unit=Decimal("1.00"), unit_amount=1000, min_amount=10000
        ),
    )
    assert rule.is_active is True
    assert rule.points_per_unit == Decimal("1.00")


@pytest.mark.asyncio
async def test_create_second_rule_deactivates_old(db_session, active_tenant):
    service = PointRuleService(db_session)
    old = await service.create_rule(
        tenant_id=active_tenant.id,
        request=PointRuleCreateRequest(points_per_unit=Decimal("1.00")),
    )
    await db_session.flush()
    new = await service.create_rule(
        tenant_id=active_tenant.id,
        request=PointRuleCreateRequest(points_per_unit=Decimal("2.00")),
    )
    await db_session.flush()
    await db_session.refresh(old)
    assert old.is_active is False
    assert new.is_active is True


@pytest.mark.asyncio
async def test_get_active_rule(db_session, active_tenant):
    service = PointRuleService(db_session)
    await service.create_rule(
        tenant_id=active_tenant.id,
        request=PointRuleCreateRequest(points_per_unit=Decimal("1.00")),
    )
    await db_session.flush()

    rule = await service.get_active_rule(tenant_id=active_tenant.id)
    assert rule is not None
    assert rule.points_per_unit == Decimal("1.00")


@pytest.mark.asyncio
async def test_get_active_rule_none_when_no_rule(db_session, active_tenant):
    service = PointRuleService(db_session)
    rule = await service.get_active_rule(tenant_id=active_tenant.id)
    assert rule is None
```

- [ ] **Step 3: Implement `app/services/point_rule_service.py`**

```python
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.point_rule import PointRule
from app.schemas.point_rule import PointRuleCreateRequest


class PointRuleService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_active_rule(self, *, tenant_id: int) -> PointRule | None:
        return await self.db.scalar(
            select(PointRule).where(
                PointRule.tenant_id == tenant_id, PointRule.is_active.is_(True)
            )
        )

    async def list_rules(self, *, tenant_id: int) -> list[PointRule]:
        rows = await self.db.scalars(
            select(PointRule)
            .where(PointRule.tenant_id == tenant_id)
            .order_by(PointRule.created_at.desc())
        )
        return list(rows.all())

    async def create_rule(
        self, *, tenant_id: int, request: PointRuleCreateRequest
    ) -> PointRule:
        # Deactivate active rules cũ
        await self.db.execute(
            update(PointRule)
            .where(
                PointRule.tenant_id == tenant_id, PointRule.is_active.is_(True)
            )
            .values(is_active=False)
        )
        await self.db.flush()

        rule = PointRule(
            tenant_id=tenant_id,
            points_per_unit=request.points_per_unit,
            unit_amount=request.unit_amount,
            min_amount=request.min_amount,
            is_active=True,
        )
        self.db.add(rule)
        await self.db.flush()
        await self.db.refresh(rule)
        return rule
```

- [ ] **Step 4: Run tests → PASS**

```bash
pytest tests/integration/test_point_rule_service.py -v
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add backend/app/schemas/point_rule.py backend/app/services/point_rule_service.py backend/tests/integration/test_point_rule_service.py
git commit -m "feat(backend): add PointRuleService with auto-deactivate (TDD)"
```

---

### Task 20: API endpoints `/merchant/point-rules`

**Files:**
- Create: `D:/DoAn/backend/app/api/point_rules.py`
- Create: `D:/DoAn/backend/tests/integration/test_point_rules_api.py`
- Modify: `D:/DoAn/backend/app/main.py`

- [ ] **Step 1: Tạo `app/api/point_rules.py`**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import (
    get_tenant_id,
    require_owner_in_tenant,
    require_staff_in_tenant,
)
from app.models.tenant_staff import TenantStaffRole
from app.schemas.point_rule import PointRuleCreateRequest, PointRuleResponse
from app.services.point_rule_service import PointRuleService

router = APIRouter(prefix="/merchant/point-rules", tags=["merchant-point-rules"])


@router.get("/active", response_model=PointRuleResponse | None)
async def get_active_rule(
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_staff_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> PointRuleResponse | None:
    service = PointRuleService(db)
    rule = await service.get_active_rule(tenant_id=tenant_id)
    if rule is None:
        return None
    return PointRuleResponse.model_validate(rule)


@router.get("", response_model=list[PointRuleResponse])
async def list_rules(
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_owner_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> list[PointRuleResponse]:
    service = PointRuleService(db)
    return [PointRuleResponse.model_validate(r) for r in await service.list_rules(tenant_id=tenant_id)]


@router.post("", response_model=PointRuleResponse, status_code=201)
async def create_rule(
    request: PointRuleCreateRequest,
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_owner_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> PointRuleResponse:
    service = PointRuleService(db)
    rule = await service.create_rule(tenant_id=tenant_id, request=request)
    return PointRuleResponse.model_validate(rule)
```

- [ ] **Step 2: Viết integration test**

Tạo `tests/integration/test_point_rules_api.py`:

```python
import pytest

from app.core.security import create_access_token
from app.models.tenant import Tenant, TenantStatus
from app.models.tenant_staff import TenantStaff, TenantStaffRole
from app.models.user import User


async def _setup(db_session):
    owner = User(email="o@example.com", password_hash="x", is_active=True)
    db_session.add(owner)
    await db_session.flush()
    tenant = Tenant(
        name="T", slug="t", owner_user_id=owner.id, status=TenantStatus.ACTIVE, settings={}
    )
    db_session.add(tenant)
    await db_session.flush()
    db_session.add(TenantStaff(tenant_id=tenant.id, user_id=owner.id, role=TenantStaffRole.OWNER))
    await db_session.flush()
    return tenant, create_access_token(user_id=owner.id)


@pytest.mark.asyncio
async def test_create_and_get_active_rule(client, db_session):
    tenant, token = await _setup(db_session)
    headers = {"Authorization": f"Bearer {token}", "X-Tenant-Id": str(tenant.id)}

    create = await client.post(
        "/merchant/point-rules",
        json={"points_per_unit": "1.00", "unit_amount": 1000, "min_amount": 10000},
        headers=headers,
    )
    assert create.status_code == 201

    get_active = await client.get("/merchant/point-rules/active", headers=headers)
    assert get_active.status_code == 200
    assert get_active.json()["points_per_unit"] == "1.00"


@pytest.mark.asyncio
async def test_create_rule_deactivates_old(client, db_session):
    tenant, token = await _setup(db_session)
    headers = {"Authorization": f"Bearer {token}", "X-Tenant-Id": str(tenant.id)}

    await client.post(
        "/merchant/point-rules",
        json={"points_per_unit": "1.00"},
        headers=headers,
    )
    await client.post(
        "/merchant/point-rules",
        json={"points_per_unit": "2.00"},
        headers=headers,
    )

    list_resp = await client.get("/merchant/point-rules", headers=headers)
    assert list_resp.status_code == 200
    rules = list_resp.json()
    assert len(rules) == 2
    active = [r for r in rules if r["is_active"]]
    assert len(active) == 1
    assert active[0]["points_per_unit"] == "2.00"
```

- [ ] **Step 3: Update `app/main.py`**

```python
from app.api import point_rules as point_rules_router

app.include_router(point_rules_router.router)
```

- [ ] **Step 4: Run tests → PASS**

```bash
pytest tests/integration/test_point_rules_api.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/point_rules.py backend/app/main.py backend/tests/integration/test_point_rules_api.py
git commit -m "feat(backend): add /merchant/point-rules CRUD endpoints"
```

---

### Task 21: Cross-tenant isolation test cho point rules

**Files:**
- Modify: `D:/DoAn/backend/tests/integration/test_point_rules_api.py`

- [ ] **Step 1: Append test**

```python
@pytest.mark.asyncio
async def test_point_rule_cross_tenant_isolation(client, db_session):
    tenant_a, token_a = await _setup(db_session)

    owner_b = User(email="ob@example.com", password_hash="x", is_active=True)
    db_session.add(owner_b)
    await db_session.flush()
    tenant_b = Tenant(
        name="B", slug="b", owner_user_id=owner_b.id,
        status=TenantStatus.ACTIVE, settings={}
    )
    db_session.add(tenant_b)
    await db_session.flush()
    db_session.add(
        TenantStaff(tenant_id=tenant_b.id, user_id=owner_b.id, role=TenantStaffRole.OWNER)
    )
    await db_session.flush()
    token_b = create_access_token(user_id=owner_b.id)

    await client.post(
        "/merchant/point-rules",
        json={"points_per_unit": "5.00"},
        headers={"Authorization": f"Bearer {token_b}", "X-Tenant-Id": str(tenant_b.id)},
    )

    response = await client.get(
        "/merchant/point-rules/active",
        headers={"Authorization": f"Bearer {token_a}", "X-Tenant-Id": str(tenant_a.id)},
    )
    assert response.status_code == 200
    # Tenant A không có rule, tenant B có rule 5.00 — A không thấy
    assert response.json() is None
```

- [ ] **Step 2: Run test → PASS**

- [ ] **Step 3: Commit**

```bash
git add backend/tests/integration/test_point_rules_api.py
git commit -m "test(backend): add cross-tenant isolation test for point rules"
```

---

## PHASE 6 — Settings Module + Audit Log

### Task 22: Tạo model `TenantSettingsAudit` + migration

**Files:**
- Create: `D:/DoAn/backend/app/models/tenant_settings_audit.py`
- Modify: `D:/DoAn/backend/app/models/__init__.py`

- [ ] **Step 1: Tạo model**

```python
from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class TenantSettingsAudit(Base, TimestampMixin):
    __tablename__ = "tenant_settings_audit"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    field_key: Mapped[str] = mapped_column(String(100), nullable=False)
    old_value: Mapped[dict] = mapped_column(JSON, nullable=True)
    new_value: Mapped[dict] = mapped_column(JSON, nullable=True)
```

- [ ] **Step 2: Update `__init__.py`**

```python
from app.models.tenant_settings_audit import TenantSettingsAudit
# Add to __all__
```

- [ ] **Step 3: Generate + apply migration**

```bash
cd D:/DoAn/backend
alembic revision --autogenerate -m "create tenant_settings_audit table"
alembic upgrade head
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/models/tenant_settings_audit.py backend/app/models/__init__.py backend/alembic/versions/
git commit -m "feat(backend): add TenantSettingsAudit model + migration"
```

---

### Task 23: TDD — `SettingsService` với schema fixed + audit log

**Files:**
- Create: `D:/DoAn/backend/app/schemas/settings.py`
- Create: `D:/DoAn/backend/app/services/settings_service.py`
- Create: `D:/DoAn/backend/tests/integration/test_settings_service.py`

- [ ] **Step 1: Tạo schema fixed `app/schemas/settings.py`**

```python
from datetime import datetime

from pydantic import BaseModel, Field


class TenantSettings(BaseModel):
    """Schema fixed cho tenants.settings JSONB. Validate chặt chẽ."""

    points_on_gross: bool = False
    birthday_campaign_id: int | None = None
    signup_bonus_points: int = Field(default=0, ge=0)
    voucher_default_ttl_days: int = Field(default=30, ge=1, le=365)
    redemption_default_ttl_days: int = Field(default=14, ge=1, le=365)
    default_tier_id: int | None = None

    model_config = {"extra": "forbid"}


class SettingsUpdateRequest(BaseModel):
    """PATCH — chỉ các field muốn đổi."""

    points_on_gross: bool | None = None
    birthday_campaign_id: int | None = None
    signup_bonus_points: int | None = Field(default=None, ge=0)
    voucher_default_ttl_days: int | None = Field(default=None, ge=1, le=365)
    redemption_default_ttl_days: int | None = Field(default=None, ge=1, le=365)
    default_tier_id: int | None = None

    model_config = {"extra": "forbid"}


class SettingsAuditEntry(BaseModel):
    id: int
    field_key: str
    old_value: object
    new_value: object
    user_id: int
    created_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 2: Viết failing tests**

Tạo `tests/integration/test_settings_service.py`:

```python
import pytest
from sqlalchemy import select

from app.models.tenant import Tenant, TenantStatus
from app.models.tenant_settings_audit import TenantSettingsAudit
from app.models.user import User
from app.schemas.settings import SettingsUpdateRequest, TenantSettings
from app.services.settings_service import SettingsService


@pytest.fixture
async def tenant_with_owner(db_session):
    user = User(email="o@example.com", password_hash="x", is_active=True)
    db_session.add(user)
    await db_session.flush()
    tenant = Tenant(
        name="T", slug="t", owner_user_id=user.id,
        status=TenantStatus.ACTIVE, settings={}
    )
    db_session.add(tenant)
    await db_session.flush()
    return tenant, user


@pytest.mark.asyncio
async def test_get_settings_returns_defaults(db_session, tenant_with_owner):
    tenant, _user = tenant_with_owner
    service = SettingsService(db_session)
    settings = await service.get_settings(tenant_id=tenant.id)
    assert isinstance(settings, TenantSettings)
    assert settings.points_on_gross is False
    assert settings.voucher_default_ttl_days == 30


@pytest.mark.asyncio
async def test_update_settings_writes_audit(db_session, tenant_with_owner):
    tenant, user = tenant_with_owner
    service = SettingsService(db_session)
    new = await service.update_settings(
        tenant_id=tenant.id,
        user_id=user.id,
        request=SettingsUpdateRequest(points_on_gross=True, voucher_default_ttl_days=60),
    )
    assert new.points_on_gross is True
    assert new.voucher_default_ttl_days == 60

    audits = await db_session.scalars(
        select(TenantSettingsAudit).where(TenantSettingsAudit.tenant_id == tenant.id)
    )
    audit_list = list(audits.all())
    assert len(audit_list) == 2
    keys = {a.field_key for a in audit_list}
    assert keys == {"points_on_gross", "voucher_default_ttl_days"}
```

- [ ] **Step 3: Implement `app/services/settings_service.py`**

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant
from app.models.tenant_settings_audit import TenantSettingsAudit
from app.schemas.settings import SettingsUpdateRequest, TenantSettings


class SettingsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_settings(self, *, tenant_id: int) -> TenantSettings:
        tenant = await self.db.get(Tenant, tenant_id)
        if tenant is None:
            raise ValueError(f"Tenant {tenant_id} not found")
        return TenantSettings(**tenant.settings)

    async def update_settings(
        self,
        *,
        tenant_id: int,
        user_id: int,
        request: SettingsUpdateRequest,
    ) -> TenantSettings:
        tenant = await self.db.get(Tenant, tenant_id)
        if tenant is None:
            raise ValueError(f"Tenant {tenant_id} not found")

        current = TenantSettings(**tenant.settings)
        changes = request.model_dump(exclude_unset=True)

        for field_key, new_value in changes.items():
            old_value = getattr(current, field_key)
            if old_value != new_value:
                self.db.add(
                    TenantSettingsAudit(
                        tenant_id=tenant_id,
                        user_id=user_id,
                        field_key=field_key,
                        old_value={"value": old_value},
                        new_value={"value": new_value},
                    )
                )
                setattr(current, field_key, new_value)

        tenant.settings = current.model_dump()
        await self.db.flush()
        return current

    async def list_audit(self, *, tenant_id: int, limit: int = 50) -> list[TenantSettingsAudit]:
        rows = await self.db.scalars(
            select(TenantSettingsAudit)
            .where(TenantSettingsAudit.tenant_id == tenant_id)
            .order_by(TenantSettingsAudit.created_at.desc())
            .limit(limit)
        )
        return list(rows.all())
```

- [ ] **Step 4: Run tests → PASS**

```bash
pytest tests/integration/test_settings_service.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/schemas/settings.py backend/app/services/settings_service.py backend/tests/integration/test_settings_service.py
git commit -m "feat(backend): add SettingsService with audit log (TDD)"
```

---

### Task 24: API endpoints `/tenants/me/settings`

**Files:**
- Create: `D:/DoAn/backend/app/api/settings.py`
- Create: `D:/DoAn/backend/tests/integration/test_settings_api.py`
- Modify: `D:/DoAn/backend/app/main.py`

- [ ] **Step 1: Tạo `app/api/settings.py`**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import (
    get_current_user,
    get_tenant_id,
    require_owner_in_tenant,
)
from app.models.tenant_staff import TenantStaffRole
from app.models.user import User
from app.schemas.settings import (
    SettingsAuditEntry,
    SettingsUpdateRequest,
    TenantSettings,
)
from app.services.settings_service import SettingsService

router = APIRouter(prefix="/tenants/me/settings", tags=["tenants-settings"])


@router.get("", response_model=TenantSettings)
async def get_settings(
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_owner_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> TenantSettings:
    service = SettingsService(db)
    return await service.get_settings(tenant_id=tenant_id)


@router.patch("", response_model=TenantSettings)
async def update_settings(
    request: SettingsUpdateRequest,
    tenant_id: int = Depends(get_tenant_id),
    user: User = Depends(get_current_user),
    _role: TenantStaffRole = Depends(require_owner_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> TenantSettings:
    service = SettingsService(db)
    return await service.update_settings(
        tenant_id=tenant_id, user_id=user.id, request=request
    )


@router.get("/audit", response_model=list[SettingsAuditEntry])
async def list_audit(
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_owner_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> list[SettingsAuditEntry]:
    service = SettingsService(db)
    rows = await service.list_audit(tenant_id=tenant_id)
    return [
        SettingsAuditEntry(
            id=r.id,
            field_key=r.field_key,
            old_value=r.old_value.get("value") if r.old_value else None,
            new_value=r.new_value.get("value") if r.new_value else None,
            user_id=r.user_id,
            created_at=r.created_at,
        )
        for r in rows
    ]
```

- [ ] **Step 2: Viết integration tests + Update main.py + commit**

Tạo `tests/integration/test_settings_api.py` với 3 tests: get default, update, list audit. Add router vào main.py. Test pass + commit.

```bash
git add backend/app/api/settings.py backend/app/main.py backend/tests/integration/test_settings_api.py
git commit -m "feat(backend): add /tenants/me/settings GET/PATCH + audit endpoints"
```

---

### Task 25: Cross-tenant test cho settings

**Files:**
- Modify: `D:/DoAn/backend/tests/integration/test_settings_api.py`

- [ ] **Step 1: Append test cross-tenant** (tương tự pattern Task 21)

- [ ] **Step 2: Commit**

```bash
git add backend/tests/integration/test_settings_api.py
git commit -m "test(backend): add cross-tenant isolation test for settings"
```

---

## PHASE 7 — Verification Codes + Claim Shadow Flow

### Task 26: Tạo model `VerificationCode` + migration

**Files:**
- Create: `D:/DoAn/backend/app/models/verification_code.py`
- Modify: `D:/DoAn/backend/app/models/__init__.py`

- [ ] **Step 1: Tạo model**

```python
import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class VerificationCodePurpose(str, enum.Enum):
    CLAIM_SHADOW = "claim_shadow"
    RESET_PASSWORD = "reset_password"


class VerificationCode(Base, TimestampMixin):
    __tablename__ = "verification_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    purpose: Mapped[VerificationCodePurpose] = mapped_column(
        Enum(VerificationCodePurpose, name="verification_code_purpose"), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
```

- [ ] **Step 2: Update `__init__.py`**, generate + apply migration, commit (rút gọn các step routine)

```bash
cd D:/DoAn/backend
alembic revision --autogenerate -m "create verification_codes table"
alembic upgrade head

cd D:/DoAn
git add backend/app/models/verification_code.py backend/app/models/__init__.py backend/alembic/versions/
git commit -m "feat(backend): add VerificationCode model + migration"
```

---

### Task 27: TDD — `VerificationCodeService` với HMAC-SHA256

**Files:**
- Create: `D:/DoAn/backend/app/services/verification_code_service.py`
- Create: `D:/DoAn/backend/tests/integration/test_verification_code_service.py`

- [ ] **Step 1: Viết failing tests**

```python
import pytest

from app.models.user import User
from app.models.verification_code import VerificationCodePurpose
from app.services.verification_code_service import (
    InvalidCodeError,
    VerificationCodeService,
)


@pytest.fixture
async def user(db_session):
    u = User(email="u@example.com", password_hash="x", is_active=True)
    db_session.add(u)
    await db_session.flush()
    return u


@pytest.mark.asyncio
async def test_create_code_returns_6_digit(db_session, user):
    service = VerificationCodeService(db_session)
    plain = await service.create_code(
        user_id=user.id, purpose=VerificationCodePurpose.CLAIM_SHADOW
    )
    assert len(plain) == 6
    assert plain.isdigit()


@pytest.mark.asyncio
async def test_verify_correct_code(db_session, user):
    service = VerificationCodeService(db_session)
    plain = await service.create_code(
        user_id=user.id, purpose=VerificationCodePurpose.CLAIM_SHADOW
    )
    await db_session.flush()

    verified = await service.verify_code(
        user_id=user.id,
        code=plain,
        purpose=VerificationCodePurpose.CLAIM_SHADOW,
    )
    assert verified is True


@pytest.mark.asyncio
async def test_verify_wrong_code_raises(db_session, user):
    service = VerificationCodeService(db_session)
    await service.create_code(
        user_id=user.id, purpose=VerificationCodePurpose.CLAIM_SHADOW
    )
    await db_session.flush()

    with pytest.raises(InvalidCodeError):
        await service.verify_code(
            user_id=user.id,
            code="000000",
            purpose=VerificationCodePurpose.CLAIM_SHADOW,
        )


@pytest.mark.asyncio
async def test_create_code_invalidates_old(db_session, user):
    service = VerificationCodeService(db_session)
    old = await service.create_code(
        user_id=user.id, purpose=VerificationCodePurpose.CLAIM_SHADOW
    )
    await db_session.flush()
    new = await service.create_code(
        user_id=user.id, purpose=VerificationCodePurpose.CLAIM_SHADOW
    )
    await db_session.flush()

    # Old code không còn dùng được
    with pytest.raises(InvalidCodeError):
        await service.verify_code(
            user_id=user.id, code=old, purpose=VerificationCodePurpose.CLAIM_SHADOW
        )
    # New code dùng được
    assert await service.verify_code(
        user_id=user.id, code=new, purpose=VerificationCodePurpose.CLAIM_SHADOW
    )


@pytest.mark.asyncio
async def test_verify_used_code_raises(db_session, user):
    service = VerificationCodeService(db_session)
    plain = await service.create_code(
        user_id=user.id, purpose=VerificationCodePurpose.CLAIM_SHADOW
    )
    await db_session.flush()
    await service.verify_code(
        user_id=user.id, code=plain, purpose=VerificationCodePurpose.CLAIM_SHADOW
    )
    await db_session.flush()

    with pytest.raises(InvalidCodeError):
        await service.verify_code(
            user_id=user.id, code=plain, purpose=VerificationCodePurpose.CLAIM_SHADOW
        )
```

- [ ] **Step 2: Implement `app/services/verification_code_service.py`**

```python
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.verification_code import VerificationCode, VerificationCodePurpose


class InvalidCodeError(Exception):
    pass


def _hmac_hash(code: str, secret: str) -> str:
    return hmac.new(secret.encode(), code.encode(), hashlib.sha256).hexdigest()


def _generate_6_digit() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


class VerificationCodeService:
    TTL_MINUTES = 10

    def __init__(self, db: AsyncSession):
        self.db = db
        self._secret = get_settings().jwt_secret  # Reuse JWT secret cho HMAC

    async def create_code(
        self, *, user_id: int, purpose: VerificationCodePurpose
    ) -> str:
        """Sinh code mới + invalidate code cũ chưa dùng. Trả plain code."""
        # Invalidate old codes
        await self.db.execute(
            update(VerificationCode)
            .where(
                VerificationCode.user_id == user_id,
                VerificationCode.purpose == purpose,
                VerificationCode.used_at.is_(None),
            )
            .values(used_at=datetime.now(timezone.utc))
        )

        plain = _generate_6_digit()
        code_hash = _hmac_hash(plain, self._secret)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=self.TTL_MINUTES)

        record = VerificationCode(
            user_id=user_id,
            code_hash=code_hash,
            purpose=purpose,
            expires_at=expires_at,
        )
        self.db.add(record)
        await self.db.flush()

        # Log ra console (MVP — không gửi SMS thật)
        print(f"[VERIFY CODE] user_id={user_id} purpose={purpose.value} code={plain} ttl={self.TTL_MINUTES}min")

        return plain

    async def verify_code(
        self, *, user_id: int, code: str, purpose: VerificationCodePurpose
    ) -> bool:
        code_hash = _hmac_hash(code, self._secret)
        now = datetime.now(timezone.utc)

        record = await self.db.scalar(
            select(VerificationCode).where(
                VerificationCode.user_id == user_id,
                VerificationCode.code_hash == code_hash,
                VerificationCode.purpose == purpose,
                VerificationCode.used_at.is_(None),
                VerificationCode.expires_at > now,
            )
        )
        if record is None:
            raise InvalidCodeError("Invalid, expired, or already used code")

        record.used_at = now
        await self.db.flush()
        return True
```

- [ ] **Step 3: Run tests → PASS**

```bash
pytest tests/integration/test_verification_code_service.py -v
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/verification_code_service.py backend/tests/integration/test_verification_code_service.py
git commit -m "feat(backend): add VerificationCodeService with HMAC-SHA256 (TDD)"
```

---

### Task 28: Update `TenantStaffService.add_staff` để gọi `VerificationCodeService`

**Files:**
- Modify: `D:/DoAn/backend/app/services/tenant_staff_service.py`

- [ ] **Step 1: Sửa `add_staff` dùng VerificationCodeService**

Trong `add_staff`, thay đoạn shadow user creation:

```python
# Cũ:
verification_code = _generate_verification_code()
existing_user = User(
    email=request.email,
    full_name=request.full_name,
    password_hash=hash_password(verification_code),
    is_active=True,
    is_shadow=True,
    system_role="regular",
)

# Mới:
existing_user = User(
    email=request.email,
    full_name=request.full_name,
    password_hash=None,  # Shadow chưa có password
    is_active=True,
    is_shadow=True,
    system_role="regular",
)
self.db.add(existing_user)
await self.db.flush()

from app.models.verification_code import VerificationCodePurpose
from app.services.verification_code_service import VerificationCodeService
vcs = VerificationCodeService(self.db)
verification_code = await vcs.create_code(
    user_id=existing_user.id, purpose=VerificationCodePurpose.CLAIM_SHADOW
)
```

> **Lưu ý:** Migration `users.password_hash` đã `nullable=True` từ tuần 1 (xem `app/models/user.py`). Confirm bằng `\d users` trong psql nếu cần.

- [ ] **Step 2: Run tests cũ → PASS**

```bash
pytest tests/integration/test_tenant_staff_service.py tests/integration/test_tenant_staff_api.py -v
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/tenant_staff_service.py
git commit -m "refactor(backend): use VerificationCodeService for shadow staff creation"
```

---

### Task 29: API endpoints claim shadow (`/auth/request-claim` + `/auth/claim-shadow`)

**Files:**
- Modify: `D:/DoAn/backend/app/services/auth_service.py`
- Modify: `D:/DoAn/backend/app/api/auth.py`
- Create: `D:/DoAn/backend/app/schemas/claim_shadow.py`
- Create: `D:/DoAn/backend/tests/integration/test_claim_shadow.py`

- [ ] **Step 1: Tạo schema `app/schemas/claim_shadow.py`**

```python
from datetime import date

from pydantic import BaseModel, EmailStr, Field


class RequestClaimRequest(BaseModel):
    email: EmailStr


class ClaimShadowRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6)
    password: str = Field(min_length=8, max_length=72)
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    birthday: date | None = None
```

- [ ] **Step 2: Thêm methods vào `AuthService`**

```python
from app.models.verification_code import VerificationCodePurpose
from app.services.verification_code_service import (
    InvalidCodeError,
    VerificationCodeService,
)


class UserNotShadowError(Exception):
    pass


class AuthService:
    # ... existing methods ...

    async def request_claim(self, *, email: str) -> bool:
        user = await self.db.scalar(select(User).where(User.email == email))
        if user is None:
            return False  # Không leak existence
        if not user.is_shadow:
            return False
        vcs = VerificationCodeService(self.db)
        await vcs.create_code(
            user_id=user.id, purpose=VerificationCodePurpose.CLAIM_SHADOW
        )
        return True

    async def claim_shadow(
        self,
        *,
        email: str,
        code: str,
        password: str,
        full_name: str | None,
        birthday: date | None,
    ) -> User:
        user = await self.db.scalar(select(User).where(User.email == email))
        if user is None or not user.is_shadow:
            raise InvalidCredentialsError("No claimable account for this email")

        vcs = VerificationCodeService(self.db)
        try:
            await vcs.verify_code(
                user_id=user.id,
                code=code,
                purpose=VerificationCodePurpose.CLAIM_SHADOW,
            )
        except InvalidCodeError as e:
            raise InvalidCredentialsError("Invalid or expired code") from e

        user.password_hash = hash_password(password)
        user.is_shadow = False
        if full_name is not None:
            user.full_name = full_name
        if birthday is not None:
            user.birthday = birthday
        await self.db.flush()
        return user
```

- [ ] **Step 3: Thêm endpoints vào `app/api/auth.py`**

```python
from app.schemas.claim_shadow import ClaimShadowRequest, RequestClaimRequest


@router.post("/request-claim", status_code=202)
async def request_claim(
    body: RequestClaimRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = AuthService(db)
    await service.request_claim(email=body.email)
    return {"message": "If account exists and is shadow, code has been sent"}


@router.post("/claim-shadow", response_model=TokenResponse)
async def claim_shadow(
    body: ClaimShadowRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    service = AuthService(db)
    try:
        user = await service.claim_shadow(
            email=body.email,
            code=body.code,
            password=body.password,
            full_name=body.full_name,
            birthday=body.birthday,
        )
    except InvalidCredentialsError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    return TokenResponse(
        access_token=create_access_token(user_id=user.id),
        refresh_token=create_refresh_token(user_id=user.id),
    )
```

- [ ] **Step 4: Viết integration tests**

Tạo `tests/integration/test_claim_shadow.py` với:
- `test_request_claim_for_shadow_user_returns_202`
- `test_request_claim_for_nonexistent_email_returns_202` (không leak)
- `test_claim_shadow_with_correct_code_succeeds`
- `test_claim_shadow_with_wrong_code_returns_401`
- `test_claim_shadow_user_can_login_after_claim`
- `test_claim_shadow_for_non_shadow_user_returns_401`

(Pattern tương tự các test trước, dùng VerificationCodeService trực tiếp để get code)

- [ ] **Step 5: Run tests → PASS**

```bash
pytest tests/integration/test_claim_shadow.py -v
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/auth_service.py backend/app/api/auth.py backend/app/schemas/claim_shadow.py backend/tests/integration/test_claim_shadow.py
git commit -m "feat(backend): add claim shadow flow (/auth/request-claim + /auth/claim-shadow)"
```

---

### Task 30: End-to-end test claim shadow flow qua add staff

**Files:**
- Modify: `D:/DoAn/backend/tests/integration/test_claim_shadow.py`

- [ ] **Step 1: Viết test E2E** — staff được Owner thêm → claim → login → list staff thành công

```python
@pytest.mark.asyncio
async def test_e2e_owner_adds_staff_then_staff_claims_and_logs_in(client, db_session):
    # Setup tenant + owner (như test_tenant_staff_api)
    tenant, _owner, owner_token = await _make_active_tenant_with_owner(db_session)

    # Owner thêm staff mới
    add = await client.post(
        "/merchant/staff",
        json={"email": "newstaff@example.com", "full_name": "Staff", "role": "staff"},
        headers={
            "Authorization": f"Bearer {owner_token}",
            "X-Tenant-Id": str(tenant.id),
        },
    )
    code = add.json()["verification_code"]

    # Staff claim account
    claim = await client.post(
        "/auth/claim-shadow",
        json={
            "email": "newstaff@example.com",
            "code": code,
            "password": "newpass12345",
            "full_name": "Staff Updated",
        },
    )
    assert claim.status_code == 200
    staff_token = claim.json()["access_token"]

    # Staff login bằng password mới
    login = await client.post(
        "/auth/login",
        json={"email": "newstaff@example.com", "password": "newpass12345"},
    )
    assert login.status_code == 200

    # Staff giờ đã có quyền access tenant (role=staff)
    list_staff = await client.get(
        "/merchant/staff",
        headers={
            "Authorization": f"Bearer {staff_token}",
            "X-Tenant-Id": str(tenant.id),
        },
    )
    # Staff không phải owner, không được list staff → 403
    assert list_staff.status_code == 403

    # Nhưng staff có thể GET tenant info
    me = await client.get(
        "/tenants/me",
        headers={
            "Authorization": f"Bearer {staff_token}",
            "X-Tenant-Id": str(tenant.id),
        },
    )
    assert me.status_code == 200
```

- [ ] **Step 2: Helper `_make_active_tenant_with_owner` cần import từ test_tenant_staff_api.py hoặc duplicate**

Để tránh circular import, copy helper vào file này (DRY violation chấp nhận được cho test).

- [ ] **Step 3: Run test → PASS**

- [ ] **Step 4: Commit**

```bash
git add backend/tests/integration/test_claim_shadow.py
git commit -m "test(backend): add E2E test for owner add staff → claim → login flow"
```

---

## PHASE 8 — Cross-tenant Isolation Tests

### Task 31: Tạo file `tests/integration/test_tenant_isolation.py` với fixture chung

**Files:**
- Create: `D:/DoAn/backend/tests/integration/test_tenant_isolation.py`

- [ ] **Step 1: Tạo file với fixture tạo 2 tenant + 2 owner**

```python
"""Cross-tenant isolation tests.

Mục đích: đảm bảo user của tenant A không thao tác được dữ liệu của tenant B,
KHÔNG dựa vào ORM scoping mặc định mà phải qua tenant_id filter ở mọi query.
"""
import pytest

from app.core.security import create_access_token
from app.models.tenant import Tenant, TenantStatus
from app.models.tenant_staff import TenantStaff, TenantStaffRole
from app.models.user import User


@pytest.fixture
async def two_tenants_with_owners(db_session):
    owner_a = User(email="a@example.com", password_hash="x", is_active=True)
    owner_b = User(email="b@example.com", password_hash="x", is_active=True)
    db_session.add_all([owner_a, owner_b])
    await db_session.flush()

    tenant_a = Tenant(
        name="Shop A", slug="shop-a", owner_user_id=owner_a.id,
        status=TenantStatus.ACTIVE, settings={},
    )
    tenant_b = Tenant(
        name="Shop B", slug="shop-b", owner_user_id=owner_b.id,
        status=TenantStatus.ACTIVE, settings={},
    )
    db_session.add_all([tenant_a, tenant_b])
    await db_session.flush()

    db_session.add_all([
        TenantStaff(tenant_id=tenant_a.id, user_id=owner_a.id, role=TenantStaffRole.OWNER),
        TenantStaff(tenant_id=tenant_b.id, user_id=owner_b.id, role=TenantStaffRole.OWNER),
    ])
    await db_session.flush()

    return {
        "tenant_a": tenant_a,
        "tenant_b": tenant_b,
        "owner_a": owner_a,
        "owner_b": owner_b,
        "token_a": create_access_token(user_id=owner_a.id),
        "token_b": create_access_token(user_id=owner_b.id),
    }
```

- [ ] **Step 2: Commit base fixture**

```bash
git add backend/tests/integration/test_tenant_isolation.py
git commit -m "test(backend): add cross-tenant isolation test fixtures"
```

---

### Task 32: Test isolation cho tiers, point_rules, staff, settings

**Files:**
- Modify: `D:/DoAn/backend/tests/integration/test_tenant_isolation.py`

- [ ] **Step 1: Append tests**

```python
@pytest.mark.asyncio
async def test_owner_a_cannot_use_tenant_b_header_for_tiers(client, two_tenants_with_owners):
    """Owner A gửi X-Tenant-Id của tenant B → 403."""
    ctx = two_tenants_with_owners
    response = await client.post(
        "/merchant/tiers",
        json={"name": "Hacked", "min_points": 0},
        headers={
            "Authorization": f"Bearer {ctx['token_a']}",
            "X-Tenant-Id": str(ctx["tenant_b"].id),
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_owner_a_cannot_use_tenant_b_header_for_staff(client, two_tenants_with_owners):
    ctx = two_tenants_with_owners
    response = await client.get(
        "/merchant/staff",
        headers={
            "Authorization": f"Bearer {ctx['token_a']}",
            "X-Tenant-Id": str(ctx["tenant_b"].id),
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_owner_a_cannot_use_tenant_b_header_for_settings(client, two_tenants_with_owners):
    ctx = two_tenants_with_owners
    response = await client.patch(
        "/tenants/me/settings",
        json={"points_on_gross": True},
        headers={
            "Authorization": f"Bearer {ctx['token_a']}",
            "X-Tenant-Id": str(ctx["tenant_b"].id),
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_owner_a_cannot_use_tenant_b_header_for_point_rules(client, two_tenants_with_owners):
    ctx = two_tenants_with_owners
    response = await client.post(
        "/merchant/point-rules",
        json={"points_per_unit": "100.00"},
        headers={
            "Authorization": f"Bearer {ctx['token_a']}",
            "X-Tenant-Id": str(ctx["tenant_b"].id),
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_tiers_listed_for_a_not_visible_to_b(client, two_tenants_with_owners):
    ctx = two_tenants_with_owners
    headers_a = {
        "Authorization": f"Bearer {ctx['token_a']}",
        "X-Tenant-Id": str(ctx["tenant_a"].id),
    }
    headers_b = {
        "Authorization": f"Bearer {ctx['token_b']}",
        "X-Tenant-Id": str(ctx["tenant_b"].id),
    }
    await client.post(
        "/merchant/tiers", json={"name": "A-Bronze", "min_points": 0}, headers=headers_a
    )
    await client.post(
        "/merchant/tiers", json={"name": "B-Bronze", "min_points": 0}, headers=headers_b
    )

    list_a = await client.get("/merchant/tiers", headers=headers_a)
    list_b = await client.get("/merchant/tiers", headers=headers_b)
    names_a = {t["name"] for t in list_a.json()}
    names_b = {t["name"] for t in list_b.json()}

    assert "A-Bronze" in names_a
    assert "B-Bronze" not in names_a
    assert "B-Bronze" in names_b
    assert "A-Bronze" not in names_b
```

- [ ] **Step 2: Run test → PASS**

```bash
pytest tests/integration/test_tenant_isolation.py -v
```

Expected: 5 passed

- [ ] **Step 3: Commit**

```bash
git add backend/tests/integration/test_tenant_isolation.py
git commit -m "test(backend): add cross-tenant isolation tests for all resources"
```

---

### Task 33: Test cache TTL — staff bị remove vẫn hoạt động trong 60s (documented behavior)

**Files:**
- Modify: `D:/DoAn/backend/tests/integration/test_tenant_isolation.py`

- [ ] **Step 1: Append test**

```python
@pytest.mark.asyncio
async def test_remove_staff_invalidates_cache_immediately(client, db_session, two_tenants_with_owners):
    """Khi remove staff, cache phải được invalidate ngay (không đợi 60s TTL)."""
    ctx = two_tenants_with_owners
    headers_a = {
        "Authorization": f"Bearer {ctx['token_a']}",
        "X-Tenant-Id": str(ctx["tenant_a"].id),
    }

    # Owner A thêm staff
    add = await client.post(
        "/merchant/staff",
        json={"email": "willremove@example.com", "full_name": "Will", "role": "staff"},
        headers=headers_a,
    )
    code = add.json()["verification_code"]
    staff_id = add.json()["staff"]["id"]

    # Staff claim
    claim = await client.post(
        "/auth/claim-shadow",
        json={
            "email": "willremove@example.com",
            "code": code,
            "password": "pass12345",
        },
    )
    staff_token = claim.json()["access_token"]
    staff_headers = {
        "Authorization": f"Bearer {staff_token}",
        "X-Tenant-Id": str(ctx["tenant_a"].id),
    }

    # Staff truy cập được /tenants/me (cache hit)
    me1 = await client.get("/tenants/me", headers=staff_headers)
    assert me1.status_code == 200

    # Owner remove staff
    remove = await client.delete(f"/merchant/staff/{staff_id}", headers=headers_a)
    assert remove.status_code == 204

    # Ngay lập tức staff không còn truy cập được (cache đã invalidate)
    me2 = await client.get("/tenants/me", headers=staff_headers)
    assert me2.status_code == 403
```

- [ ] **Step 2: Run test → PASS**

- [ ] **Step 3: Commit**

```bash
git add backend/tests/integration/test_tenant_isolation.py
git commit -m "test(backend): verify cache invalidation on staff remove"
```

---

## PHASE 9 — Seed Script v1

### Task 34: Tạo `scripts/seed.py` — 2 tenant + 5 tier + 3 point_rule + 5 staff

**Files:**
- Create: `D:/DoAn/backend/scripts/__init__.py`
- Create: `D:/DoAn/backend/scripts/seed.py`

- [ ] **Step 1: Tạo `scripts/__init__.py` (empty)**

- [ ] **Step 2: Tạo `scripts/seed.py`**

```python
"""Seed script v1 — Tuần 2.

Tạo:
- 1 super admin
- 2 tenants ACTIVE: "The Coffee House" và "Pizza 4P's"
- Mỗi tenant: 1 owner + 2 staff + 5 tiers (Bronze/Silver/Gold/Platinum/Diamond) + 1 active point_rule

Chạy:
    cd backend && python -m scripts.seed

Idempotent: chạy nhiều lần OK (skip nếu user/tenant đã có).
"""
import asyncio
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import AsyncSessionLocal
from app.core.security import hash_password
from app.models.point_rule import PointRule
from app.models.tenant import Tenant, TenantStatus
from app.models.tenant_staff import TenantStaff, TenantStaffRole
from app.models.tier import Tier
from app.models.user import User


SEED_DATA = {
    "super_admin": {
        "email": "admin@loyalty.local",
        "password": "admin12345",
        "full_name": "Super Admin",
    },
    "tenants": [
        {
            "name": "The Coffee House",
            "slug": "the-coffee-house",
            "owner": {
                "email": "owner1@loyalty.local",
                "password": "owner12345",
                "full_name": "TCH Owner",
            },
            "staff": [
                {"email": "staff1a@loyalty.local", "full_name": "Staff 1A"},
                {"email": "staff1b@loyalty.local", "full_name": "Staff 1B"},
            ],
            "tiers": [
                ("Bronze", 0),
                ("Silver", 500),
                ("Gold", 2000),
                ("Platinum", 5000),
                ("Diamond", 10000),
            ],
            "point_rule": {"points_per_unit": "1.00", "unit_amount": 1000, "min_amount": 10000},
        },
        {
            "name": "Pizza 4P's",
            "slug": "pizza-4ps",
            "owner": {
                "email": "owner2@loyalty.local",
                "password": "owner12345",
                "full_name": "P4 Owner",
            },
            "staff": [
                {"email": "staff2a@loyalty.local", "full_name": "Staff 2A"},
                {"email": "staff2b@loyalty.local", "full_name": "Staff 2B"},
            ],
            "tiers": [
                ("Bronze", 0),
                ("Silver", 1000),
                ("Gold", 3000),
                ("Platinum", 7000),
                ("Diamond", 15000),
            ],
            "point_rule": {"points_per_unit": "0.50", "unit_amount": 1000, "min_amount": 50000},
        },
    ],
}


async def get_or_create_user(
    db: AsyncSession, email: str, password: str | None, full_name: str, system_role: str = "regular"
) -> User:
    user = await db.scalar(select(User).where(User.email == email))
    if user is not None:
        return user
    user = User(
        email=email,
        password_hash=hash_password(password) if password else None,
        full_name=full_name,
        is_active=True,
        is_shadow=password is None,
        system_role=system_role,
    )
    db.add(user)
    await db.flush()
    return user


async def get_or_create_tenant(
    db: AsyncSession, name: str, slug: str, owner_id: int
) -> Tenant:
    tenant = await db.scalar(select(Tenant).where(Tenant.slug == slug))
    if tenant is not None:
        return tenant
    tenant = Tenant(
        name=name,
        slug=slug,
        owner_user_id=owner_id,
        status=TenantStatus.ACTIVE,
        activated_at=datetime.now(timezone.utc),
        settings={},
    )
    db.add(tenant)
    await db.flush()
    return tenant


async def get_or_create_staff(
    db: AsyncSession, tenant_id: int, user_id: int, role: TenantStaffRole
) -> TenantStaff:
    existing = await db.scalar(
        select(TenantStaff).where(
            TenantStaff.tenant_id == tenant_id, TenantStaff.user_id == user_id
        )
    )
    if existing is not None:
        return existing
    staff = TenantStaff(tenant_id=tenant_id, user_id=user_id, role=role)
    db.add(staff)
    await db.flush()
    return staff


async def seed_tier(
    db: AsyncSession, tenant_id: int, name: str, min_points: int
) -> Tier:
    existing = await db.scalar(
        select(Tier).where(
            Tier.tenant_id == tenant_id, Tier.name == name, Tier.deleted_at.is_(None)
        )
    )
    if existing is not None:
        return existing
    tier = Tier(
        tenant_id=tenant_id, name=name, min_points=min_points, perks={}, is_active=True
    )
    db.add(tier)
    await db.flush()
    return tier


async def seed_point_rule(db: AsyncSession, tenant_id: int, config: dict) -> PointRule:
    existing = await db.scalar(
        select(PointRule).where(
            PointRule.tenant_id == tenant_id, PointRule.is_active.is_(True)
        )
    )
    if existing is not None:
        return existing
    rule = PointRule(
        tenant_id=tenant_id,
        points_per_unit=Decimal(config["points_per_unit"]),
        unit_amount=config["unit_amount"],
        min_amount=config["min_amount"],
        is_active=True,
    )
    db.add(rule)
    await db.flush()
    return rule


async def seed():
    async with AsyncSessionLocal() as db:
        admin_data = SEED_DATA["super_admin"]
        await get_or_create_user(
            db,
            email=admin_data["email"],
            password=admin_data["password"],
            full_name=admin_data["full_name"],
            system_role="super_admin",
        )
        print(f"  ✓ Super admin: {admin_data['email']} / {admin_data['password']}")

        for tenant_data in SEED_DATA["tenants"]:
            owner_data = tenant_data["owner"]
            owner = await get_or_create_user(
                db,
                email=owner_data["email"],
                password=owner_data["password"],
                full_name=owner_data["full_name"],
            )
            tenant = await get_or_create_tenant(
                db,
                name=tenant_data["name"],
                slug=tenant_data["slug"],
                owner_id=owner.id,
            )
            await get_or_create_staff(
                db, tenant_id=tenant.id, user_id=owner.id, role=TenantStaffRole.OWNER
            )
            print(f"  ✓ Tenant: {tenant.name} (owner: {owner_data['email']} / {owner_data['password']})")

            for staff_data in tenant_data["staff"]:
                staff_user = await get_or_create_user(
                    db,
                    email=staff_data["email"],
                    password="staff12345",
                    full_name=staff_data["full_name"],
                )
                await get_or_create_staff(
                    db,
                    tenant_id=tenant.id,
                    user_id=staff_user.id,
                    role=TenantStaffRole.STAFF,
                )
                print(f"      + Staff: {staff_data['email']} / staff12345")

            for name, min_points in tenant_data["tiers"]:
                await seed_tier(db, tenant_id=tenant.id, name=name, min_points=min_points)
            print(f"      + 5 tiers")

            await seed_point_rule(db, tenant_id=tenant.id, config=tenant_data["point_rule"])
            print(f"      + 1 point_rule")

        await db.commit()
        print("\n✅ Seed completed.")


if __name__ == "__main__":
    asyncio.run(seed())
```

- [ ] **Step 3: Test seed**

```bash
cd D:/DoAn
docker compose up -d postgres
docker compose exec postgres psql -U loyalty -d loyalty -c "TRUNCATE users, tenants, tenant_staff, tiers, point_rules CASCADE;"
cd backend
python -m scripts.seed
```

Expected output:
```
  ✓ Super admin: admin@loyalty.local / admin12345
  ✓ Tenant: The Coffee House (...)
      + Staff: ...
      + 5 tiers
      + 1 point_rule
  ✓ Tenant: Pizza 4P's (...)
✅ Seed completed.
```

- [ ] **Step 4: Verify trong DB**

```bash
docker compose exec postgres psql -U loyalty -d loyalty -c "SELECT email FROM users;"
docker compose exec postgres psql -U loyalty -d loyalty -c "SELECT name, slug FROM tenants;"
```

- [ ] **Step 5: Commit**

```bash
git add backend/scripts/__init__.py backend/scripts/seed.py
git commit -m "feat(backend): add seed script v1 with 2 tenants + 10 users + 10 tiers + 2 rules"
```

---

### Task 35: Thêm `make seed` vào Makefile

**Files:**
- Modify: `D:/DoAn/Makefile`

- [ ] **Step 1: Thêm target**

```makefile
.PHONY: seed
seed:
	cd backend && python -m scripts.seed

.PHONY: seed-fresh
seed-fresh:
	docker compose exec postgres psql -U loyalty -d loyalty -c "TRUNCATE users, tenants, tenant_staff, tiers, point_rules, verification_codes, tenant_settings_audit CASCADE;"
	$(MAKE) seed
```

- [ ] **Step 2: Test**

```bash
cd D:/DoAn
make seed
```

- [ ] **Step 3: Commit**

```bash
git add Makefile
git commit -m "chore: add make seed and make seed-fresh targets"
```

---

## PHASE 10 — Frontend State + API Client Extension

### Task 36: Mở rộng `lib/api.ts` thêm endpoints + header `X-Tenant-Id`

**Files:**
- Modify: `D:/DoAn/frontend/src/lib/api.ts`
- Create: `D:/DoAn/frontend/src/types/tenant.ts`
- Create: `D:/DoAn/frontend/src/types/tier.ts`
- Create: `D:/DoAn/frontend/src/types/point-rule.ts`
- Create: `D:/DoAn/frontend/src/types/staff.ts`
- Create: `D:/DoAn/frontend/src/types/settings.ts`

- [ ] **Step 1: Tạo các type files**

`src/types/tenant.ts`:
```typescript
export type TenantStatus = "pending" | "active" | "suspended";

export interface Tenant {
  id: number;
  name: string;
  slug: string;
  owner_user_id: number;
  status: TenantStatus;
  logo_url: string | null;
  description: string | null;
  settings: Record<string, unknown>;
  created_at: string;
  activated_at: string | null;
}

export interface TenantCreateRequest {
  name: string;
  description?: string;
  logo_url?: string;
}
```

`src/types/tier.ts`:
```typescript
export interface Tier {
  id: number;
  tenant_id: number;
  name: string;
  min_points: number;
  perks: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
}

export interface TierCreateRequest {
  name: string;
  min_points: number;
  perks?: Record<string, unknown>;
}

export interface TierUpdateRequest {
  name?: string;
  min_points?: number;
  perks?: Record<string, unknown>;
  is_active?: boolean;
}
```

`src/types/point-rule.ts`:
```typescript
export interface PointRule {
  id: number;
  tenant_id: number;
  points_per_unit: string; // Decimal as string
  unit_amount: number;
  min_amount: number;
  is_active: boolean;
  created_at: string;
}

export interface PointRuleCreateRequest {
  points_per_unit: string;
  unit_amount?: number;
  min_amount?: number;
}
```

`src/types/staff.ts`:
```typescript
export type StaffRole = "owner" | "staff";

export interface Staff {
  id: number;
  tenant_id: number;
  user_id: number;
  role: StaffRole;
  user_email: string | null;
  user_full_name: string | null;
  created_at: string;
}

export interface StaffAddRequest {
  email: string;
  full_name: string;
  role?: StaffRole;
}

export interface StaffAddResponse {
  staff: Staff;
  verification_code: string | null;
}
```

`src/types/settings.ts`:
```typescript
export interface TenantSettings {
  points_on_gross: boolean;
  birthday_campaign_id: number | null;
  signup_bonus_points: number;
  voucher_default_ttl_days: number;
  redemption_default_ttl_days: number;
  default_tier_id: number | null;
}

export interface SettingsUpdateRequest {
  points_on_gross?: boolean;
  voucher_default_ttl_days?: number;
  redemption_default_ttl_days?: number;
  signup_bonus_points?: number;
  birthday_campaign_id?: number | null;
  default_tier_id?: number | null;
}

export interface SettingsAuditEntry {
  id: number;
  field_key: string;
  old_value: unknown;
  new_value: unknown;
  user_id: number;
  created_at: string;
}
```

- [ ] **Step 2: Mở rộng `src/lib/api.ts`**

Thêm vào file (sau `authApi`):

```typescript
import type { Tenant, TenantCreateRequest } from "@/types/tenant";
import type { Tier, TierCreateRequest, TierUpdateRequest } from "@/types/tier";
import type { PointRule, PointRuleCreateRequest } from "@/types/point-rule";
import type { Staff, StaffAddRequest, StaffAddResponse } from "@/types/staff";
import type {
  SettingsAuditEntry,
  SettingsUpdateRequest,
  TenantSettings,
} from "@/types/settings";

// Helper: thêm X-Tenant-Id header
function withTenant(tenantId: number) {
  return { headers: { "X-Tenant-Id": String(tenantId) } };
}

// === Merchant tenant ===
export const merchantApi = {
  register: (data: TenantCreateRequest) =>
    api.post<Tenant>("/merchant/register", data),
  getMyTenant: (tenantId: number) =>
    api.get<Tenant>("/tenants/me", withTenant(tenantId)),
};

// === Tiers ===
export const tierApi = {
  list: (tenantId: number) =>
    api.get<Tier[]>("/merchant/tiers", withTenant(tenantId)),
  create: (tenantId: number, data: TierCreateRequest) =>
    api.post<Tier>("/merchant/tiers", data, withTenant(tenantId)),
  update: (tenantId: number, tierId: number, data: TierUpdateRequest) =>
    api.patch<Tier>(`/merchant/tiers/${tierId}`, data, withTenant(tenantId)),
  delete: (tenantId: number, tierId: number) =>
    api.delete(`/merchant/tiers/${tierId}`, withTenant(tenantId)),
};

// === Point rules ===
export const pointRuleApi = {
  getActive: (tenantId: number) =>
    api.get<PointRule | null>("/merchant/point-rules/active", withTenant(tenantId)),
  list: (tenantId: number) =>
    api.get<PointRule[]>("/merchant/point-rules", withTenant(tenantId)),
  create: (tenantId: number, data: PointRuleCreateRequest) =>
    api.post<PointRule>("/merchant/point-rules", data, withTenant(tenantId)),
};

// === Staff ===
export const staffApi = {
  list: (tenantId: number) =>
    api.get<Staff[]>("/merchant/staff", withTenant(tenantId)),
  add: (tenantId: number, data: StaffAddRequest) =>
    api.post<StaffAddResponse>("/merchant/staff", data, withTenant(tenantId)),
  updateRole: (tenantId: number, staffId: number, role: "owner" | "staff") =>
    api.patch<Staff>(`/merchant/staff/${staffId}`, { role }, withTenant(tenantId)),
  remove: (tenantId: number, staffId: number) =>
    api.delete(`/merchant/staff/${staffId}`, withTenant(tenantId)),
};

// === Settings ===
export const settingsApi = {
  get: (tenantId: number) =>
    api.get<TenantSettings>("/tenants/me/settings", withTenant(tenantId)),
  update: (tenantId: number, data: SettingsUpdateRequest) =>
    api.patch<TenantSettings>("/tenants/me/settings", data, withTenant(tenantId)),
  audit: (tenantId: number) =>
    api.get<SettingsAuditEntry[]>("/tenants/me/settings/audit", withTenant(tenantId)),
};

// === Admin ===
export const adminApi = {
  listTenants: (status?: string) =>
    api.get<Tenant[]>(`/admin/tenants${status ? `?status=${status}` : ""}`),
  approveTenant: (tenantId: number, approve: boolean) =>
    api.post<Tenant>(`/admin/tenants/${tenantId}/approve`, { approve }),
};

// === Claim shadow ===
export const claimApi = {
  requestClaim: (email: string) =>
    api.post("/auth/request-claim", { email }),
  claimShadow: (data: {
    email: string;
    code: string;
    password: string;
    full_name?: string;
    birthday?: string;
  }) => api.post<TokenResponse>("/auth/claim-shadow", data),
};
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/types/ frontend/src/lib/api.ts
git commit -m "feat(frontend): add tenant/tier/staff/settings types + API client extensions"
```

---

### Task 37: Tạo Zustand `tenantStore` cho tenant context

**Files:**
- Create: `D:/DoAn/frontend/src/lib/tenant-store.ts`

- [ ] **Step 1: Tạo file**

```typescript
import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { Tenant } from "@/types/tenant";
import { merchantApi } from "./api";

interface TenantState {
  currentTenant: Tenant | null;
  isLoading: boolean;
  error: string | null;
  setCurrentTenant: (tenant: Tenant | null) => void;
  fetchTenant: (tenantId: number) => Promise<void>;
  clear: () => void;
}

export const useTenantStore = create<TenantState>()(
  persist(
    (set) => ({
      currentTenant: null,
      isLoading: false,
      error: null,

      setCurrentTenant: (tenant) => set({ currentTenant: tenant, error: null }),

      fetchTenant: async (tenantId: number) => {
        set({ isLoading: true, error: null });
        try {
          const { data } = await merchantApi.getMyTenant(tenantId);
          set({ currentTenant: data, isLoading: false });
        } catch (e: unknown) {
          const err = e as { response?: { data?: { detail?: string } } };
          set({
            currentTenant: null,
            isLoading: false,
            error: err.response?.data?.detail || "Failed to load tenant",
          });
        }
      },

      clear: () => set({ currentTenant: null, error: null }),
    }),
    {
      name: "tenant",
      storage: createJSONStorage(() => sessionStorage),
    }
  )
);
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/lib/tenant-store.ts
git commit -m "feat(frontend): add Zustand tenant store with persistence"
```

---

### Task 38: Update `auth-store.ts` để rehydrate user khi reload (fix tuần 1 I7)

**Files:**
- Modify: `D:/DoAn/frontend/src/lib/auth-store.ts`

- [ ] **Step 1: Wrap với `persist` middleware**

```typescript
import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { User } from "@/types/auth";
import { authApi } from "./api";

interface AuthState {
  user: User | null;
  isLoading: boolean;
  setTokens: (accessToken: string, refreshToken: string) => void;
  fetchMe: () => Promise<void>;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isLoading: false,

      setTokens: (accessToken, refreshToken) => {
        if (typeof window !== "undefined") {
          sessionStorage.setItem("access_token", accessToken);
          sessionStorage.setItem("refresh_token", refreshToken);
        }
      },

      fetchMe: async () => {
        set({ isLoading: true });
        try {
          const { data } = await authApi.me();
          set({ user: data, isLoading: false });
        } catch {
          set({ user: null, isLoading: false });
          if (typeof window !== "undefined") {
            sessionStorage.removeItem("access_token");
            sessionStorage.removeItem("refresh_token");
          }
        }
      },

      logout: () => {
        if (typeof window !== "undefined") {
          sessionStorage.removeItem("access_token");
          sessionStorage.removeItem("refresh_token");
        }
        set({ user: null });
      },
    }),
    {
      name: "auth",
      storage: createJSONStorage(() => sessionStorage),
      partialize: (state) => ({ user: state.user }),
    }
  )
);
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/lib/auth-store.ts
git commit -m "fix(frontend): persist user in auth store with rehydration"
```

---

## PHASE 11 — `/admin` Minimal

### Task 39: Tạo layout `/admin` + auth guard component

**Files:**
- Create: `D:/DoAn/frontend/src/components/auth-guard.tsx`
- Create: `D:/DoAn/frontend/src/app/admin/layout.tsx`

- [ ] **Step 1: Tạo `components/auth-guard.tsx`**

```typescript
"use client";

import { useEffect, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/auth-store";

interface AuthGuardProps {
  children: ReactNode;
  requireRole?: "super_admin" | "regular";
}

export function AuthGuard({ children, requireRole }: AuthGuardProps) {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const fetchMe = useAuthStore((s) => s.fetchMe);

  useEffect(() => {
    if (!user) {
      fetchMe();
    }
  }, [user, fetchMe]);

  useEffect(() => {
    if (user === null) return;
    if (requireRole && user.system_role !== requireRole) {
      router.push("/");
    }
  }, [user, requireRole, router]);

  if (user === null) {
    return <div className="p-8 text-center">Đang tải...</div>;
  }

  return <>{children}</>;
}
```

- [ ] **Step 2: Tạo `app/admin/layout.tsx`**

```typescript
import type { ReactNode } from "react";
import Link from "next/link";
import { AuthGuard } from "@/components/auth-guard";

export default function AdminLayout({ children }: { children: ReactNode }) {
  return (
    <AuthGuard requireRole="super_admin">
      <div className="min-h-screen flex">
        <aside className="w-64 bg-slate-900 text-white p-6">
          <h1 className="text-xl font-bold mb-6">Super Admin</h1>
          <nav className="space-y-2">
            <Link href="/admin" className="block hover:underline">Dashboard</Link>
            <Link href="/admin/tenants" className="block hover:underline">Doanh nghiệp</Link>
          </nav>
        </aside>
        <main className="flex-1 p-8">{children}</main>
      </div>
    </AuthGuard>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/auth-guard.tsx frontend/src/app/admin/layout.tsx
git commit -m "feat(frontend): add /admin layout + AuthGuard component"
```

---

### Task 40: Tạo `/admin` dashboard root + `/admin/tenants` page

**Files:**
- Create: `D:/DoAn/frontend/src/app/admin/page.tsx`
- Create: `D:/DoAn/frontend/src/app/admin/tenants/page.tsx`

- [ ] **Step 1: Tạo `admin/page.tsx`**

```typescript
export default function AdminDashboard() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Dashboard</h1>
      <p className="text-muted-foreground">
        Chào mừng. Vào tab "Doanh nghiệp" để duyệt yêu cầu đăng ký.
      </p>
    </div>
  );
}
```

- [ ] **Step 2: Tạo `admin/tenants/page.tsx`**

```typescript
"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { adminApi } from "@/lib/api";
import type { Tenant } from "@/types/tenant";

export default function AdminTenantsPage() {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const { data } = await adminApi.listTenants("pending");
      setTenants(data);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setError(err.response?.data?.detail || "Lỗi tải danh sách");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const approve = async (tenantId: number) => {
    await adminApi.approveTenant(tenantId, true);
    await load();
  };

  if (loading) return <p>Đang tải...</p>;
  if (error) return <p className="text-red-500">{error}</p>;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Doanh nghiệp chờ duyệt</h1>
      {tenants.length === 0 ? (
        <p className="text-muted-foreground">Không có doanh nghiệp nào chờ duyệt.</p>
      ) : (
        <div className="space-y-4">
          {tenants.map((t) => (
            <Card key={t.id}>
              <CardHeader>
                <CardTitle>{t.name}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground mb-2">
                  Slug: <code>{t.slug}</code>
                </p>
                {t.description && <p className="mb-2">{t.description}</p>}
                <p className="text-xs text-muted-foreground mb-4">
                  Đăng ký: {new Date(t.created_at).toLocaleString("vi-VN")}
                </p>
                <Button onClick={() => approve(t.id)}>Duyệt</Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Test thủ công**

```bash
cd D:/DoAn
docker compose up -d
make seed
# Mở http://localhost:3000/login → đăng nhập admin@loyalty.local / admin12345
# Vào http://localhost:3000/admin/tenants
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/app/admin/
git commit -m "feat(frontend): add /admin dashboard + tenants approval page"
```

---

### Task 41: Test E2E thủ công `/admin` flow

- [ ] **Step 1: Login với super admin → vào /admin/tenants → verify list pending**
- [ ] **Step 2: Approve 1 tenant → verify tenant biến mất khỏi list (hoặc reload thấy chuyển sang active)**
- [ ] **Step 3: Verify trong DB**

```bash
docker compose exec postgres psql -U loyalty -d loyalty -c "SELECT slug, status FROM tenants;"
```

- [ ] **Step 4: Commit (no code change, smoke check)**

---

## PHASE 12 — `/merchant/register` + Dashboard Root

### Task 42: Tạo `/merchant/register` page

**Files:**
- Create: `D:/DoAn/frontend/src/app/merchant/register/page.tsx`

- [ ] **Step 1: Tạo file**

```typescript
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

import { merchantApi } from "@/lib/api";
import { useTenantStore } from "@/lib/tenant-store";

const schema = z.object({
  name: z.string().min(2, "Tên tối thiểu 2 ký tự").max(255),
  description: z.string().max(1000).optional(),
});

type FormData = z.infer<typeof schema>;

export default function MerchantRegisterPage() {
  const router = useRouter();
  const setTenant = useTenantStore((s) => s.setCurrentTenant);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = async (data: FormData) => {
    setError(null);
    setSubmitting(true);
    try {
      const res = await merchantApi.register(data);
      setTenant(res.data);
      setSuccess(
        `Đăng ký thành công! Doanh nghiệp "${res.data.name}" đang chờ Super Admin duyệt.`
      );
      setTimeout(() => router.push("/merchant"), 2500);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setError(err.response?.data?.detail || "Đăng ký thất bại");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="container mx-auto flex min-h-screen items-center justify-center px-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Đăng ký doanh nghiệp</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <Label htmlFor="name">Tên doanh nghiệp</Label>
              <Input id="name" {...register("name")} />
              {errors.name && (
                <p className="text-sm text-red-500">{errors.name.message}</p>
              )}
            </div>
            <div>
              <Label htmlFor="description">Mô tả (tuỳ chọn)</Label>
              <Input id="description" {...register("description")} />
            </div>
            {error && <p className="text-sm text-red-500">{error}</p>}
            {success && <p className="text-sm text-green-600">{success}</p>}
            <Button type="submit" className="w-full" disabled={submitting}>
              {submitting ? "Đang đăng ký..." : "Đăng ký"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/app/merchant/register/
git commit -m "feat(frontend): add /merchant/register page"
```

---

### Task 43: Tạo `/merchant` layout với tenant context guard

**Files:**
- Create: `D:/DoAn/frontend/src/app/merchant/layout.tsx`
- Create: `D:/DoAn/frontend/src/components/tenant-context-provider.tsx`

- [ ] **Step 1: Tạo `tenant-context-provider.tsx`**

```typescript
"use client";

import { useEffect, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/auth-store";
import { useTenantStore } from "@/lib/tenant-store";

interface Props {
  children: ReactNode;
}

export function TenantContextProvider({ children }: Props) {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const fetchMe = useAuthStore((s) => s.fetchMe);
  const tenant = useTenantStore((s) => s.currentTenant);

  useEffect(() => {
    if (!user) fetchMe();
  }, [user, fetchMe]);

  useEffect(() => {
    if (user === null) return;
    if (!tenant) {
      // Nếu user đã đăng nhập nhưng chưa có tenant context → vào register
      router.push("/merchant/register");
    }
  }, [user, tenant, router]);

  if (user === null || !tenant) {
    return <div className="p-8 text-center">Đang tải...</div>;
  }

  if (tenant.status !== "active") {
    return (
      <div className="p-8">
        <div className="rounded-lg bg-yellow-100 p-4">
          <h2 className="font-bold text-yellow-900">
            Doanh nghiệp đang chờ duyệt
          </h2>
          <p className="text-yellow-800 mt-2">
            Trạng thái: <code>{tenant.status}</code>. Liên hệ Super Admin để được duyệt.
          </p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
```

- [ ] **Step 2: Tạo `merchant/layout.tsx`**

```typescript
import type { ReactNode } from "react";
import Link from "next/link";
import { AuthGuard } from "@/components/auth-guard";
import { TenantContextProvider } from "@/components/tenant-context-provider";

export default function MerchantLayout({ children }: { children: ReactNode }) {
  return (
    <AuthGuard>
      <TenantContextProvider>
        <div className="min-h-screen flex">
          <aside className="w-64 bg-slate-900 text-white p-6">
            <h1 className="text-xl font-bold mb-6">Merchant</h1>
            <nav className="space-y-2">
              <Link href="/merchant" className="block hover:underline">Dashboard</Link>
              <Link href="/merchant/tiers" className="block hover:underline">Hạng thành viên</Link>
              <Link href="/merchant/point-rules" className="block hover:underline">Quy tắc tích điểm</Link>
              <Link href="/merchant/staff" className="block hover:underline">Nhân viên</Link>
              <Link href="/merchant/settings" className="block hover:underline">Cài đặt</Link>
            </nav>
          </aside>
          <main className="flex-1 p-8">{children}</main>
        </div>
      </TenantContextProvider>
    </AuthGuard>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/tenant-context-provider.tsx frontend/src/app/merchant/layout.tsx
git commit -m "feat(frontend): add /merchant layout with tenant context guard"
```

---

### Task 44: Tạo `/merchant` dashboard root

**Files:**
- Create: `D:/DoAn/frontend/src/app/merchant/page.tsx`

- [ ] **Step 1: Tạo file**

```typescript
"use client";

import { useTenantStore } from "@/lib/tenant-store";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function MerchantDashboard() {
  const tenant = useTenantStore((s) => s.currentTenant);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">{tenant?.name}</h1>
      <p className="text-muted-foreground mb-6">
        Slug: <code>{tenant?.slug}</code>
      </p>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Hạng thành viên</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground text-sm">
              Cấu hình các hạng (Bronze/Silver/Gold...) và quyền lợi mỗi hạng.
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Quy tắc tích điểm</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground text-sm">
              Quy đổi VND sang điểm (vd 1 điểm / 1.000 VND).
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Nhân viên</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground text-sm">
              Thêm/xóa/đổi vai trò nhân viên cửa hàng.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/app/merchant/page.tsx
git commit -m "feat(frontend): add /merchant dashboard root"
```

---

### Task 45: Cập nhật flow login → fetch tenant context tự động

**Files:**
- Modify: `D:/DoAn/frontend/src/app/(auth)/login/page.tsx`

- [ ] **Step 1: Sau khi login, redirect dựa vào role**

Sửa `onSubmit` trong `login/page.tsx`:

```typescript
const onSubmit = async (data: FormData) => {
  setError(null);
  setSubmitting(true);
  try {
    const res = await authApi.login(data);
    setTokens(res.data.access_token, res.data.refresh_token);
    await fetchMe();

    const user = useAuthStore.getState().user;
    if (user?.system_role === "super_admin") {
      router.push("/admin");
    } else {
      router.push("/merchant");
    }
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } };
    setError(err.response?.data?.detail || "Đăng nhập thất bại");
  } finally {
    setSubmitting(false);
  }
};
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/app/(auth)/login/page.tsx
git commit -m "feat(frontend): redirect after login based on system_role"
```

---

## PHASE 13 — `/merchant/tiers` + `/merchant/point-rules`

### Task 46: Tạo `/merchant/tiers` page (list + add)

**Files:**
- Create: `D:/DoAn/frontend/src/app/merchant/tiers/page.tsx`

- [ ] **Step 1: Tạo file**

```typescript
"use client";

import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

import { tierApi } from "@/lib/api";
import { useTenantStore } from "@/lib/tenant-store";
import type { Tier } from "@/types/tier";

const schema = z.object({
  name: z.string().min(1, "Tên không được trống").max(100),
  min_points: z.coerce.number().int().min(0),
});

type FormData = z.infer<typeof schema>;

export default function MerchantTiersPage() {
  const tenant = useTenantStore((s) => s.currentTenant);
  const [tiers, setTiers] = useState<Tier[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const load = async () => {
    if (!tenant) return;
    setLoading(true);
    try {
      const { data } = await tierApi.list(tenant.id);
      setTiers(data);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setError(err.response?.data?.detail || "Lỗi tải danh sách");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [tenant]);

  const onSubmit = async (data: FormData) => {
    if (!tenant) return;
    try {
      if (editingId) {
        await tierApi.update(tenant.id, editingId, data);
      } else {
        await tierApi.create(tenant.id, data);
      }
      reset({ name: "", min_points: 0 });
      setEditingId(null);
      await load();
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setError(err.response?.data?.detail || "Lỗi lưu");
    }
  };

  const handleEdit = (tier: Tier) => {
    setEditingId(tier.id);
    reset({ name: tier.name, min_points: tier.min_points });
  };

  const handleDelete = async (tierId: number) => {
    if (!tenant) return;
    if (!confirm("Xoá hạng này? (soft delete — không xoá history)")) return;
    await tierApi.delete(tenant.id, tierId);
    await load();
  };

  if (loading) return <p>Đang tải...</p>;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Hạng thành viên</h1>
      {error && <p className="text-red-500 mb-4">{error}</p>}

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>{editingId ? "Sửa hạng" : "Thêm hạng mới"}</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <Label htmlFor="name">Tên hạng</Label>
              <Input id="name" {...register("name")} placeholder="Bronze" />
              {errors.name && (
                <p className="text-sm text-red-500">{errors.name.message}</p>
              )}
            </div>
            <div>
              <Label htmlFor="min_points">Điểm tối thiểu</Label>
              <Input id="min_points" type="number" {...register("min_points")} />
              {errors.min_points && (
                <p className="text-sm text-red-500">{errors.min_points.message}</p>
              )}
            </div>
            <div className="flex gap-2">
              <Button type="submit">{editingId ? "Cập nhật" : "Thêm"}</Button>
              {editingId && (
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setEditingId(null);
                    reset({ name: "", min_points: 0 });
                  }}
                >
                  Huỷ
                </Button>
              )}
            </div>
          </form>
        </CardContent>
      </Card>

      <div className="space-y-2">
        {tiers.map((t) => (
          <Card key={t.id}>
            <CardContent className="flex items-center justify-between py-4">
              <div>
                <h3 className="font-semibold">{t.name}</h3>
                <p className="text-sm text-muted-foreground">
                  Tối thiểu: {t.min_points.toLocaleString("vi-VN")} điểm
                </p>
              </div>
              <div className="flex gap-2">
                <Button size="sm" variant="outline" onClick={() => handleEdit(t)}>
                  Sửa
                </Button>
                <Button size="sm" variant="destructive" onClick={() => handleDelete(t.id)}>
                  Xoá
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Test thủ công sau khi seed**

```bash
docker compose up -d
make seed
# Login: owner1@loyalty.local / owner12345
# Vào http://localhost:3000/merchant/tiers
# Verify thấy 5 tier seed (Bronze, Silver, Gold, Platinum, Diamond)
# Thử thêm 1 tier mới + edit + xoá
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/app/merchant/tiers/
git commit -m "feat(frontend): add /merchant/tiers list + add + edit + delete"
```

---

### Task 47: Tạo `/merchant/point-rules` page

**Files:**
- Create: `D:/DoAn/frontend/src/app/merchant/point-rules/page.tsx`

- [ ] **Step 1: Tạo file**

```typescript
"use client";

import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

import { pointRuleApi } from "@/lib/api";
import { useTenantStore } from "@/lib/tenant-store";
import type { PointRule } from "@/types/point-rule";

const schema = z.object({
  points_per_unit: z.string().regex(/^\d+(\.\d{1,2})?$/, "Số dương, tối đa 2 chữ số thập phân"),
  unit_amount: z.coerce.number().int().min(1).default(1000),
  min_amount: z.coerce.number().int().min(0).default(0),
});

type FormData = z.infer<typeof schema>;

export default function MerchantPointRulesPage() {
  const tenant = useTenantStore((s) => s.currentTenant);
  const [activeRule, setActiveRule] = useState<PointRule | null>(null);
  const [history, setHistory] = useState<PointRule[]>([]);
  const [loading, setLoading] = useState(true);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { points_per_unit: "1.00", unit_amount: 1000, min_amount: 0 },
  });

  const load = async () => {
    if (!tenant) return;
    setLoading(true);
    const [active, list] = await Promise.all([
      pointRuleApi.getActive(tenant.id),
      pointRuleApi.list(tenant.id),
    ]);
    setActiveRule(active.data);
    setHistory(list.data);
    setLoading(false);
  };

  useEffect(() => {
    load();
  }, [tenant]);

  const onSubmit = async (data: FormData) => {
    if (!tenant) return;
    if (!confirm("Tạo rule mới sẽ deactivate rule hiện tại. Tiếp tục?")) return;
    await pointRuleApi.create(tenant.id, data);
    reset();
    await load();
  };

  if (loading) return <p>Đang tải...</p>;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Quy tắc tích điểm</h1>

      {activeRule && (
        <Card className="mb-6 border-green-500">
          <CardHeader>
            <CardTitle>Rule đang áp dụng</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-lg">
              <strong>{activeRule.points_per_unit}</strong> điểm /{" "}
              <strong>{activeRule.unit_amount.toLocaleString("vi-VN")}</strong> VND
            </p>
            <p className="text-sm text-muted-foreground">
              Đơn tối thiểu: {activeRule.min_amount.toLocaleString("vi-VN")} VND
            </p>
          </CardContent>
        </Card>
      )}

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Tạo rule mới</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <Label htmlFor="points_per_unit">Điểm / đơn vị</Label>
              <Input id="points_per_unit" {...register("points_per_unit")} placeholder="1.00" />
              {errors.points_per_unit && (
                <p className="text-sm text-red-500">{errors.points_per_unit.message}</p>
              )}
            </div>
            <div>
              <Label htmlFor="unit_amount">Đơn vị (VND)</Label>
              <Input id="unit_amount" type="number" {...register("unit_amount")} />
            </div>
            <div>
              <Label htmlFor="min_amount">Đơn tối thiểu (VND)</Label>
              <Input id="min_amount" type="number" {...register("min_amount")} />
            </div>
            <Button type="submit">Tạo rule mới</Button>
          </form>
        </CardContent>
      </Card>

      <h2 className="text-xl font-semibold mb-2">Lịch sử rules</h2>
      <div className="space-y-2">
        {history.map((r) => (
          <Card key={r.id}>
            <CardContent className="py-3 flex justify-between items-center">
              <span>
                {r.points_per_unit} điểm / {r.unit_amount.toLocaleString("vi-VN")} VND
                {r.is_active && (
                  <span className="ml-2 text-xs bg-green-100 text-green-800 px-2 py-0.5 rounded">
                    Đang dùng
                  </span>
                )}
              </span>
              <span className="text-xs text-muted-foreground">
                {new Date(r.created_at).toLocaleDateString("vi-VN")}
              </span>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/app/merchant/point-rules/
git commit -m "feat(frontend): add /merchant/point-rules page"
```

---

### Task 48: Test thủ công cả 2 page tiers + point rules

- [ ] **Step 1: Run docker + seed → login owner → vào /merchant/tiers, /merchant/point-rules**
- [ ] **Step 2: Verify 5 tiers từ seed hiển thị + 1 active rule hiển thị**
- [ ] **Step 3: Test thêm tier mới, edit, xoá**
- [ ] **Step 4: Test tạo rule mới → verify rule cũ deactivate**

(No commit nếu không có code change)

---

## PHASE 14 — `/merchant/settings`

### Task 49: Tạo `/merchant/settings` page với form PATCH

**Files:**
- Create: `D:/DoAn/frontend/src/app/merchant/settings/page.tsx`

- [ ] **Step 1: Tạo file**

```typescript
"use client";

import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

import { settingsApi } from "@/lib/api";
import { useTenantStore } from "@/lib/tenant-store";
import type { SettingsAuditEntry, TenantSettings } from "@/types/settings";

interface FormData {
  points_on_gross: boolean;
  voucher_default_ttl_days: number;
  redemption_default_ttl_days: number;
  signup_bonus_points: number;
}

export default function MerchantSettingsPage() {
  const tenant = useTenantStore((s) => s.currentTenant);
  const [settings, setSettings] = useState<TenantSettings | null>(null);
  const [audit, setAudit] = useState<SettingsAuditEntry[]>([]);
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { register, handleSubmit, reset, watch } = useForm<FormData>();
  const watchedGross = watch("points_on_gross");

  const load = async () => {
    if (!tenant) return;
    const [s, a] = await Promise.all([
      settingsApi.get(tenant.id),
      settingsApi.audit(tenant.id),
    ]);
    setSettings(s.data);
    setAudit(a.data);
    reset({
      points_on_gross: s.data.points_on_gross,
      voucher_default_ttl_days: s.data.voucher_default_ttl_days,
      redemption_default_ttl_days: s.data.redemption_default_ttl_days,
      signup_bonus_points: s.data.signup_bonus_points,
    });
  };

  useEffect(() => {
    load();
  }, [tenant]);

  const onSubmit = async (data: FormData) => {
    if (!tenant) return;
    setError(null);
    setSuccess(null);
    if (
      data.points_on_gross !== settings?.points_on_gross &&
      !confirm(
        "Đổi 'tính điểm trên giá gốc' ảnh hưởng kinh tế trực tiếp. Xác nhận?"
      )
    ) {
      return;
    }
    try {
      await settingsApi.update(tenant.id, {
        points_on_gross: data.points_on_gross,
        voucher_default_ttl_days: Number(data.voucher_default_ttl_days),
        redemption_default_ttl_days: Number(data.redemption_default_ttl_days),
        signup_bonus_points: Number(data.signup_bonus_points),
      });
      setSuccess("Đã cập nhật");
      await load();
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setError(err.response?.data?.detail || "Lỗi cập nhật");
    }
  };

  if (!settings) return <p>Đang tải...</p>;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Cài đặt</h1>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Cấu hình shop</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="flex items-center gap-2">
              <input
                id="points_on_gross"
                type="checkbox"
                {...register("points_on_gross")}
              />
              <Label htmlFor="points_on_gross">
                Tính điểm trên giá gốc (gross) thay vì giá sau voucher (net)
              </Label>
            </div>
            <p className="text-xs text-muted-foreground -mt-2">
              {watchedGross
                ? "⚠️ Điểm sẽ được tính trên giá GỐC. Khách được tích điểm cả phần đã giảm giá voucher."
                : "Mặc định: điểm tính trên giá NET (sau voucher), an toàn cho shop."}
            </p>

            <div>
              <Label htmlFor="voucher_default_ttl_days">TTL voucher mặc định (ngày)</Label>
              <Input
                id="voucher_default_ttl_days"
                type="number"
                min={1}
                max={365}
                {...register("voucher_default_ttl_days", { valueAsNumber: true })}
              />
            </div>

            <div>
              <Label htmlFor="redemption_default_ttl_days">TTL đổi quà (ngày)</Label>
              <Input
                id="redemption_default_ttl_days"
                type="number"
                min={1}
                max={365}
                {...register("redemption_default_ttl_days", { valueAsNumber: true })}
              />
            </div>

            <div>
              <Label htmlFor="signup_bonus_points">Điểm thưởng đăng ký</Label>
              <Input
                id="signup_bonus_points"
                type="number"
                min={0}
                {...register("signup_bonus_points", { valueAsNumber: true })}
              />
            </div>

            {success && <p className="text-sm text-green-600">{success}</p>}
            {error && <p className="text-sm text-red-500">{error}</p>}
            <Button type="submit">Lưu</Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Lịch sử thay đổi</CardTitle>
        </CardHeader>
        <CardContent>
          {audit.length === 0 ? (
            <p className="text-muted-foreground text-sm">Chưa có thay đổi nào.</p>
          ) : (
            <ul className="space-y-2 text-sm">
              {audit.map((entry) => (
                <li key={entry.id} className="border-b pb-2">
                  <code className="font-semibold">{entry.field_key}</code>:{" "}
                  <span className="text-muted-foreground">{String(entry.old_value)}</span>{" "}
                  → <span>{String(entry.new_value)}</span>
                  <span className="text-xs text-muted-foreground ml-2">
                    {new Date(entry.created_at).toLocaleString("vi-VN")}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/app/merchant/settings/
git commit -m "feat(frontend): add /merchant/settings with form + audit history"
```

---

### Task 50: Test thủ công settings + audit

- [ ] **Step 1: Login owner → /merchant/settings → toggle points_on_gross → verify confirm dialog**
- [ ] **Step 2: Save → verify success message + audit entry mới hiển thị**
- [ ] **Step 3: Verify trong DB**

```bash
docker compose exec postgres psql -U loyalty -d loyalty -c "SELECT * FROM tenant_settings_audit;"
```

(No commit)

---

## PHASE 15 — `/merchant/staff` (Luồng H)

### Task 51: Tạo `/merchant/staff` page với list

**Files:**
- Create: `D:/DoAn/frontend/src/app/merchant/staff/page.tsx`

- [ ] **Step 1: Tạo file**

```typescript
"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

import { staffApi } from "@/lib/api";
import { useTenantStore } from "@/lib/tenant-store";
import type { Staff } from "@/types/staff";
import { AddStaffDialog } from "./add-staff-dialog";

export default function MerchantStaffPage() {
  const tenant = useTenantStore((s) => s.currentTenant);
  const [staff, setStaff] = useState<Staff[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);

  const load = async () => {
    if (!tenant) return;
    setLoading(true);
    const { data } = await staffApi.list(tenant.id);
    setStaff(data);
    setLoading(false);
  };

  useEffect(() => {
    load();
  }, [tenant]);

  const handleRemove = async (staffId: number) => {
    if (!tenant) return;
    if (!confirm("Xoá nhân viên này khỏi shop?")) return;
    await staffApi.remove(tenant.id, staffId);
    await load();
  };

  const handleToggleRole = async (s: Staff) => {
    if (!tenant) return;
    const newRole = s.role === "owner" ? "staff" : "owner";
    if (!confirm(`Đổi role thành ${newRole}?`)) return;
    await staffApi.updateRole(tenant.id, s.id, newRole);
    await load();
  };

  if (loading) return <p>Đang tải...</p>;

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">Nhân viên</h1>
        <Button onClick={() => setShowAdd(true)}>+ Thêm nhân viên</Button>
      </div>

      {showAdd && (
        <AddStaffDialog
          tenantId={tenant!.id}
          onClose={() => setShowAdd(false)}
          onCreated={() => {
            setShowAdd(false);
            load();
          }}
        />
      )}

      <div className="space-y-2">
        {staff.map((s) => (
          <Card key={s.id}>
            <CardContent className="py-4 flex items-center justify-between">
              <div>
                <p className="font-semibold">{s.user_full_name || "—"}</p>
                <p className="text-sm text-muted-foreground">{s.user_email}</p>
                <span
                  className={`inline-block mt-1 text-xs px-2 py-0.5 rounded ${
                    s.role === "owner"
                      ? "bg-purple-100 text-purple-800"
                      : "bg-blue-100 text-blue-800"
                  }`}
                >
                  {s.role}
                </span>
              </div>
              <div className="flex gap-2">
                <Button size="sm" variant="outline" onClick={() => handleToggleRole(s)}>
                  Đổi role
                </Button>
                <Button size="sm" variant="destructive" onClick={() => handleRemove(s.id)}>
                  Xoá
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/app/merchant/staff/page.tsx
git commit -m "feat(frontend): add /merchant/staff list page"
```

---

### Task 52: Tạo `AddStaffDialog` component

**Files:**
- Create: `D:/DoAn/frontend/src/app/merchant/staff/add-staff-dialog.tsx`

- [ ] **Step 1: Tạo file**

```typescript
"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

import { staffApi } from "@/lib/api";

const schema = z.object({
  email: z.string().email(),
  full_name: z.string().min(1).max(255),
  role: z.enum(["owner", "staff"]).default("staff"),
});

type FormData = z.infer<typeof schema>;

interface Props {
  tenantId: number;
  onClose: () => void;
  onCreated: () => void;
}

export function AddStaffDialog({ tenantId, onClose, onCreated }: Props) {
  const [verificationCode, setVerificationCode] = useState<string | null>(null);
  const [staffName, setStaffName] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { role: "staff" },
  });

  const onSubmit = async (data: FormData) => {
    setError(null);
    setSubmitting(true);
    try {
      const res = await staffApi.add(tenantId, data);
      if (res.data.verification_code) {
        // Shadow user mới — hiển thị verification code cho owner
        setVerificationCode(res.data.verification_code);
        setStaffName(data.full_name);
      } else {
        // User đã có sẵn — đóng dialog ngay
        onCreated();
      }
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setError(err.response?.data?.detail || "Lỗi thêm nhân viên");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg p-6 max-w-md w-full">
        {verificationCode ? (
          <div>
            <h2 className="text-xl font-bold mb-2">Nhân viên đã được tạo</h2>
            <p className="text-sm text-muted-foreground mb-4">
              <strong>{staffName}</strong> là người dùng mới (shadow account).
              Đưa mã sau cho họ để claim tài khoản tại trang <code>/claim</code>:
            </p>
            <div className="bg-yellow-100 text-yellow-900 p-4 rounded text-center mb-4">
              <code className="text-3xl font-mono tracking-widest">{verificationCode}</code>
              <p className="text-xs mt-2">⚠️ Mã có hiệu lực 10 phút</p>
            </div>
            <Button onClick={onCreated} className="w-full">
              Đóng
            </Button>
          </div>
        ) : (
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <h2 className="text-xl font-bold">Thêm nhân viên</h2>
            <div>
              <Label htmlFor="full_name">Họ tên</Label>
              <Input id="full_name" {...register("full_name")} />
              {errors.full_name && (
                <p className="text-sm text-red-500">{errors.full_name.message}</p>
              )}
            </div>
            <div>
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" {...register("email")} />
              {errors.email && (
                <p className="text-sm text-red-500">{errors.email.message}</p>
              )}
            </div>
            <div>
              <Label htmlFor="role">Role</Label>
              <select
                id="role"
                {...register("role")}
                className="block w-full border rounded h-10 px-3"
              >
                <option value="staff">Staff</option>
                <option value="owner">Owner</option>
              </select>
            </div>
            {error && <p className="text-sm text-red-500">{error}</p>}
            <div className="flex gap-2">
              <Button type="submit" disabled={submitting} className="flex-1">
                {submitting ? "Đang tạo..." : "Tạo"}
              </Button>
              <Button type="button" variant="outline" onClick={onClose} className="flex-1">
                Huỷ
              </Button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/app/merchant/staff/add-staff-dialog.tsx
git commit -m "feat(frontend): add AddStaffDialog with verification code display"
```

---

### Task 53: Test thủ công staff flow (add + verification code + remove)

- [ ] **Step 1: Login owner → /merchant/staff → bấm "Thêm nhân viên"**
- [ ] **Step 2: Nhập email mới (chưa có trong hệ thống) → Tạo**
- [ ] **Step 3: Verify dialog hiển thị verification code 6 số**
- [ ] **Step 4: Note code cho Task 56 test claim**
- [ ] **Step 5: Test thêm nhân viên với email đã có (vd `staff1a@loyalty.local` từ seed) → verify không có verification code**
- [ ] **Step 6: Test đổi role + remove**

(No commit nếu không có code change)

---

### Task 54: Cross-tenant guard cho `/merchant/staff` (vẫn dùng layout chung)

Verify rằng layout `/merchant` đã có `TenantContextProvider` chặn user không đúng tenant. Test bằng cách:

- [ ] **Step 1: Login owner1 → mở DevTools → vào sessionStorage → sửa `tenant.state.currentTenant.id` thành tenant của owner2 → reload → verify bị redirect về `/merchant/register` (vì user không là staff của tenant đó)**

(Hoặc test bằng URL khác — cần verify guard hoạt động)

(No commit)

---

## PHASE 16 — Claim Shadow Page

### Task 55: Tạo `/claim` page

**Files:**
- Create: `D:/DoAn/frontend/src/app/(auth)/claim/page.tsx`

- [ ] **Step 1: Tạo file**

```typescript
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

import { claimApi } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";

const requestSchema = z.object({
  email: z.string().email(),
});

const claimSchema = z.object({
  email: z.string().email(),
  code: z.string().length(6).regex(/^\d{6}$/),
  password: z.string().min(8).max(72),
  full_name: z.string().min(1).max(255).optional(),
});

type RequestData = z.infer<typeof requestSchema>;
type ClaimData = z.infer<typeof claimSchema>;

export default function ClaimPage() {
  const router = useRouter();
  const setTokens = useAuthStore((s) => s.setTokens);
  const fetchMe = useAuthStore((s) => s.fetchMe);

  const [step, setStep] = useState<"request" | "claim">("request");
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const requestForm = useForm<RequestData>({ resolver: zodResolver(requestSchema) });
  const claimForm = useForm<ClaimData>({
    resolver: zodResolver(claimSchema),
    defaultValues: { email: "" },
  });

  const onRequestSubmit = async (data: RequestData) => {
    setError(null);
    setSubmitting(true);
    try {
      await claimApi.requestClaim(data.email);
      setEmail(data.email);
      claimForm.setValue("email", data.email);
      setStep("claim");
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setError(err.response?.data?.detail || "Lỗi");
    } finally {
      setSubmitting(false);
    }
  };

  const onClaimSubmit = async (data: ClaimData) => {
    setError(null);
    setSubmitting(true);
    try {
      const res = await claimApi.claimShadow(data);
      setTokens(res.data.access_token, res.data.refresh_token);
      await fetchMe();
      router.push("/merchant");
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setError(err.response?.data?.detail || "Code không hợp lệ");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="container mx-auto flex min-h-screen items-center justify-center px-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Nhận tài khoản</CardTitle>
        </CardHeader>
        <CardContent>
          {step === "request" ? (
            <form onSubmit={requestForm.handleSubmit(onRequestSubmit)} className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Nếu Owner đã thêm bạn vào shop, nhập email để nhận code claim.
              </p>
              <div>
                <Label htmlFor="email">Email</Label>
                <Input id="email" type="email" {...requestForm.register("email")} />
              </div>
              {error && <p className="text-sm text-red-500">{error}</p>}
              <Button type="submit" className="w-full" disabled={submitting}>
                {submitting ? "Đang gửi..." : "Gửi mã"}
              </Button>
              <p className="text-xs text-muted-foreground text-center">
                ⚠️ MVP: code được log ra console backend (không gửi email thật).
                Liên hệ Owner để lấy code.
              </p>
            </form>
          ) : (
            <form onSubmit={claimForm.handleSubmit(onClaimSubmit)} className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Nhập code 6 số từ Owner và set mật khẩu mới.
              </p>
              <div>
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  {...claimForm.register("email")}
                  readOnly
                  className="bg-muted"
                />
              </div>
              <div>
                <Label htmlFor="code">Mã 6 số</Label>
                <Input
                  id="code"
                  maxLength={6}
                  {...claimForm.register("code")}
                  className="text-center text-2xl font-mono tracking-widest"
                />
              </div>
              <div>
                <Label htmlFor="password">Mật khẩu mới</Label>
                <Input id="password" type="password" {...claimForm.register("password")} />
              </div>
              <div>
                <Label htmlFor="full_name">Họ tên (tuỳ chọn)</Label>
                <Input id="full_name" {...claimForm.register("full_name")} />
              </div>
              {error && <p className="text-sm text-red-500">{error}</p>}
              <Button type="submit" className="w-full" disabled={submitting}>
                {submitting ? "Đang xác nhận..." : "Nhận tài khoản"}
              </Button>
              <Button
                type="button"
                variant="outline"
                className="w-full"
                onClick={() => setStep("request")}
              >
                ← Quay lại
              </Button>
            </form>
          )}
        </CardContent>
      </Card>
    </main>
  );
}
```

- [ ] **Step 2: Add link "Nhận tài khoản" vào login page**

Sửa `app/(auth)/login/page.tsx`, thêm link cuối form:

```typescript
<p className="text-center text-sm text-muted-foreground">
  Chưa có tài khoản?{" "}
  <Link href="/register" className="underline">
    Đăng ký
  </Link>
  {" · "}
  <Link href="/claim" className="underline">
    Nhận tài khoản (cho nhân viên)
  </Link>
</p>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/app/(auth)/claim/ frontend/src/app/(auth)/login/page.tsx
git commit -m "feat(frontend): add /claim page for shadow account claim"
```

---

### Task 56: Test E2E claim flow qua UI

- [ ] **Step 1: Setup**
  - `docker compose up -d`, `make seed-fresh`
  - Login owner1@loyalty.local
  - Vào `/merchant/staff` → thêm staff `newuser@example.com` → note verification code (vd `123456`)

- [ ] **Step 2: Logout owner**
- [ ] **Step 3: Vào `/login` → bấm "Nhận tài khoản"**
- [ ] **Step 4: Nhập email `newuser@example.com` → Gửi mã**
- [ ] **Step 5: Nhập code 123456 + password mới + họ tên → Nhận tài khoản**
- [ ] **Step 6: Verify redirect về `/merchant`**
- [ ] **Step 7: Verify staff thấy được tenant nhưng KHÔNG có quyền vào `/merchant/staff` (403)**
- [ ] **Step 8: Logout → login lại với newuser + password mới → verify thành công**

(No commit nếu không có code change)

---

## PHASE 17 — Smoke Test E2E + Milestone Review #1 Prep

### Task 57: Smoke test E2E full workflow tuần 2

- [ ] **Step 1: Reset môi trường**

```bash
cd D:/DoAn
docker compose down
docker compose up -d --build
make seed-fresh
```

- [ ] **Step 2: Verify backend OK**

```bash
curl http://localhost:8000/health
```

- [ ] **Step 3: Run toàn bộ tests**

```bash
cd backend
pytest -v
```

Expected: ~60 tests pass (25 từ tuần 1 + ~35 mới)

- [ ] **Step 4: Manual workflow test (browser)**

| # | Hành động | Expected |
|---|---|---|
| 1 | Login `admin@loyalty.local / admin12345` | Redirect `/admin` |
| 2 | Vào `/admin/tenants` | Hiển thị 0 pending (đã seed active) |
| 3 | Logout, login `owner1@loyalty.local / owner12345` | Redirect `/merchant` |
| 4 | Verify dashboard hiển thị tên "The Coffee House" | OK |
| 5 | Vào `/merchant/tiers` | Thấy 5 tiers seed |
| 6 | Thêm tier mới "Test" min=100, sửa, xoá | OK |
| 7 | Vào `/merchant/point-rules` | Thấy rule active 1.00 / 1000 VND |
| 8 | Tạo rule mới 2.00 / 1000 → confirm warning → verify rule cũ deactivate | OK |
| 9 | Vào `/merchant/staff` | Thấy owner + 2 staff seed |
| 10 | Thêm staff mới `claim-test@example.com` → note code | Code 6 số hiển thị |
| 11 | Logout, vào `/claim` → email + code → set password `newpass1234` | Redirect `/merchant` |
| 12 | Login lại với `claim-test@example.com / newpass1234` | OK |
| 13 | Verify staff không vào được `/merchant/staff` (403 hoặc redirect) | OK |
| 14 | Vào `/merchant/settings` (cần owner) | 403 (vì giờ là staff) |
| 15 | Login lại owner1, vào `/merchant/settings` → toggle `points_on_gross` → confirm → save | Audit entry hiển thị |
| 16 | Test cross-tenant: owner1 sửa sessionStorage `tenant.state.currentTenant.id` thành tenant_id của owner2 → reload | Bị redirect/lỗi |

- [ ] **Step 5: Kiểm CI**

```bash
cd D:/DoAn
git push origin main
```

Vào GitHub Actions → verify CI xanh.

- [ ] **Step 6: Note bất kỳ bug nào tìm thấy → tạo issue / fix ngay**

---

### Task 58: Chuẩn bị Milestone Review #1 với giảng viên

- [ ] **Step 1: Tạo file `docs/milestone-1-demo.md`**

```markdown
# Milestone Review #1 — Cuối tuần 2

## Demo scenario (15 phút)

### Phần 1 — Multi-tenant + Owner workflow (5 phút)
1. Login Super Admin → /admin → giải thích role
2. Logout, login Owner1 → /merchant → giải thích tenant context (X-Tenant-Id)
3. Vào /merchant/tiers → demo CRUD 5 hạng (Bronze → Diamond)
4. Vào /merchant/point-rules → demo tạo rule mới + auto deactivate rule cũ
5. Vào /merchant/settings → toggle points_on_gross + show audit log

### Phần 2 — Quản lý nhân viên + Claim shadow (5 phút)
1. /merchant/staff → demo list nhân viên
2. Thêm nhân viên mới → giải thích shadow account + verification code
3. Logout, /claim → nhập code → set password → đăng nhập thành công
4. Verify nhân viên có quyền hạn chế (không vào được /merchant/staff)

### Phần 3 — Cross-tenant isolation + Tests (5 phút)
1. Show test_tenant_isolation.py → giải thích pattern
2. Run `pytest tests/integration/test_tenant_isolation.py -v`
3. Mở DevTools → demo sửa tenant_id → bị reject
4. Show GitHub Actions CI xanh
5. Show seed script + cách reset môi trường

## Câu hỏi giảng viên có thể hỏi

| Câu hỏi | Trả lời chuẩn bị sẵn |
|---|---|
| Vì sao JWT không chứa tenant list? | Cấp quyền staff mới không cần re-login. Staff làm nhiều shop OK. |
| Cache TTL 60s — staff bị remove vẫn login được không? | Không, đã invalidate cache ngay khi remove (test_remove_staff_invalidates_cache). |
| Multi-worker thì cache thế nào? | Mỗi worker có cache riêng. MVP dùng 1 worker. Luận văn chuyển Redis. |
| Verification code log console — production thì sao? | Adapter pattern đã chuẩn bị. Luận văn integrate Twilio/eSMS. |
| Soft delete tier — khách đang ở tier đó thì sao? | Recompute tier trigger khi tier deleted (Luồng K — implement tuần 3 hoặc luận văn). |
| Tại sao dùng HMAC thay bcrypt cho code 6 số? | Code 10^6 tổ hợp + rate limit = bcrypt cost 12 (~250ms) là overkill. HMAC <1ms, đủ an toàn vì attacker không lấy được secret. |

## Tiêu chí đạt cuối tuần 2

- [x] Backend ~60 tests pass (25 từ tuần 1 + 35 mới)
- [x] Cross-tenant isolation tests pass (5+ tests)
- [x] Frontend 5 pages (`/admin`, `/merchant/{register,tiers,point-rules,settings,staff}`, `/claim`)
- [x] Seed script v1 chạy 1 lệnh
- [x] Docker Compose up chạy được
- [x] CI xanh
- [x] Demo end-to-end manual smoke test pass
- [x] Multi-tenant context middleware (X-Tenant-Id + cache TTL)
- [x] Verification codes + claim shadow flow đầy đủ
- [x] Settings audit log
```

- [ ] **Step 2: Commit**

```bash
cd D:/DoAn
git add docs/milestone-1-demo.md
git commit -m "docs: add milestone review #1 demo scenario + Q&A prep"
```

- [ ] **Step 3: Hẹn lịch milestone review với giảng viên**

Email/Zalo giảng viên hướng dẫn xin lịch demo cuối tuần 2 hoặc đầu tuần 3.

---

## Tổng kết Tuần 2

### Đã hoàn thành (58 tasks)

**Backend (Phase 1-9):**
- ✅ Multi-tenant context middleware (X-Tenant-Id + TTLCache 60s + 4 dependencies)
- ✅ 6 backend modules: tenants, tenant_staff, tiers, point_rules, settings, verification_codes
- ✅ Tenant lifecycle: register pending → super admin approve → active
- ✅ Luồng H — quản lý nhân viên đầy đủ (add/remove/update role)
- ✅ Verification code HMAC-SHA256 + claim shadow flow (Luồng B Phần 2)
- ✅ Settings module với audit log
- ✅ Soft delete tier (chuẩn bị Luồng G recompute tuần 3)
- ✅ Partial unique index point_rules (1 active per tenant)
- ✅ Cross-tenant isolation tests (5+ tests, mỗi resource)
- ✅ Cache invalidation khi remove staff
- ✅ Seed script v1 (super admin + 2 tenant + 2 owner + 4 staff + 10 tier + 2 rule)
- ✅ Makefile target `make seed` + `make seed-fresh`

**Frontend (Phase 10-16):**
- ✅ Tenant store + auth store rehydration (fix tuần 1 I7)
- ✅ API client với header `X-Tenant-Id` cho tất cả endpoints
- ✅ AuthGuard + TenantContextProvider components
- ✅ `/admin` minimal — list pending tenants + approve
- ✅ `/merchant/register` — đăng ký tenant
- ✅ `/merchant` layout với tenant context guard
- ✅ `/merchant` dashboard root
- ✅ `/merchant/tiers` — CRUD đầy đủ
- ✅ `/merchant/point-rules` — tạo rule mới + history
- ✅ `/merchant/settings` — form PATCH + audit history
- ✅ `/merchant/staff` — list + AddStaffDialog (verification code display) + remove + update role
- ✅ `/claim` — request code + verify shadow account

**Testing & DevOps (Phase 8, 17):**
- ✅ ~35 new tests (services + APIs + cross-tenant + claim flow E2E)
- ✅ Smoke test manual E2E full workflow
- ✅ Milestone review #1 demo prep + Q&A

### Files được tạo (tổng số ~50 files)

**Backend:** 6 models, 6 services, 6 schemas, 7 routers, 1 cache util, 1 slug util, 7 test files, 1 seed script

**Frontend:** 8 pages, 2 components, 5 type files, 2 stores, API client extension

### Số liệu

- ~58 tasks trong 17 phases
- ~35 commits mới
- ~2700 LOC backend + ~2250 LOC frontend
- ~35 new tests (target met)
- 5 backend migrations mới
- Tổng tests cuối tuần 2: ~60 (25 từ tuần 1 + ~35 mới)

### Acceptance criteria — kiểm cuối tuần 2

- [x] Super Admin login → approve tenant
- [x] Owner đăng ký + cấu hình tier/rule/settings
- [x] Owner thêm staff → staff claim shadow → login
- [x] Cross-tenant isolation: 5+ tests pass
- [x] Seed v1 1 lệnh chạy được
- [x] Docker compose up chạy được full stack
- [x] CI xanh
- [x] Milestone review #1 demo sẵn sàng

---

## Sang tuần 3

Tuần 3 sẽ làm:
- Module `members` (shadow flow qua POS — khác claim shadow của staff)
- `transactions` method (a) nhập thủ công (Luồng B Phần 1)
- `point_ledger` (append-only + DB trigger + reconcile invariant)
- Luồng G — auto upgrade tier sau mỗi transaction
- `/pos` UI skeleton + form nhập giao dịch thủ công
- Test ledger invariant
- Cuối tuần phải có: tích điểm thủ công + ledger reconcile pass

Plan tuần 3 sẽ được tạo riêng tại `docs/superpowers/plans/2026-04-12-tuan-3-members-transactions.md`.


