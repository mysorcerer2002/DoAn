# MVP Features Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Hoàn thiện 9 lỗ hổng MVP "Cân bằng" (SMTP reset / Ví Voucher / QR raw / Login log + lock / Admin logs + summary / Partner staff CRUD).

**Architecture:** Append-only `login_log` cho audit + sliding-window lock 5/15min. `partner_staff` chứa staff (owner ngoài bảng — vẫn `partners.owner_user_id`). QR cá nhân raw `user.id` int gen client-side bằng `qrcode.react`. Email plain text qua `aiosmtplib` async + timeout 10s + 2 policy đối xứng (public fail-silent vs authenticated return temp_password). Pivot `point_ledger` thêm `actor_user_id` cho audit ADJUST.

**Tech Stack:** FastAPI + SQLAlchemy 2.0 async + asyncpg + Alembic + Pydantic v2 + aiosmtplib + Next.js 14 App Router + TypeScript + TanStack Query + qrcode.react + Zustand.

**Spec canonical:** `docs/superpowers/specs/2026-04-26-mvp-features-completion-design.md` (v2 post code-review opus).

**Migration head trước khi bắt đầu:** `d4e5f6a7b8c9_pivot_to_mvp_balanced`.

---

## File Structure (lock decisions trước khi vào tasks)

### Backend — files mới

| File | Trách nhiệm |
|---|---|
| `backend/alembic/versions/<hex>_m6_login_log_partner_staff_actor.py` | DDL M6: tạo `login_log`, `partner_staff`, thêm `point_ledger.actor_user_id` |
| `backend/app/models/login_log.py` | `LoginLog` model |
| `backend/app/models/partner_staff.py` | `PartnerStaff` model |
| `backend/app/schemas/login_log.py` | `LoginLogResponse`, `LoginLogListResponse`, `LoginLogFilter` |
| `backend/app/schemas/partner_staff.py` | `StaffCreateRequest`, `StaffPatchRequest`, `StaffResponse`, `StaffListResponse`, `StaffResetResponse` |
| `backend/app/services/login_log_service.py` | `log_attempt()`, `count_recent_failures()`, `list_for_admin()` |
| `backend/app/services/staff_service.py` | `list_staff()`, `add_staff()`, `toggle_active()`, `reset_staff_password()` |
| `backend/app/services/email_service.py` | `send_email(to, subject, body, timeout=10)` async với `EmailDeliveryError` |
| `backend/app/api/partner.py` (extend hoặc mới module `staff`) | `/partner/staff` CRUD endpoints |
| `backend/tests/unit/test_email_service.py` | Unit test EmailService |
| `backend/tests/unit/test_login_log_service.py` | Unit test lock window logic |
| `backend/tests/unit/test_staff_service.py` | Unit test add staff atomic + guard |
| `backend/tests/integration/test_auth_lock.py` | Integration test 5-fail-15min lock |
| `backend/tests/integration/test_admin_logs.py` | Integration test admin logs endpoints |

### Backend — files sửa

| File | Lý do sửa |
|---|---|
| `backend/app/models/point_ledger.py` | Thêm `actor_user_id` Mapped column |
| `backend/app/models/__init__.py` | Export `LoginLog`, `PartnerStaff` |
| `backend/app/api/auth.py` | login: lock check + log; forgot_password: gửi email thật |
| `backend/app/api/admin.py` | Thêm 3 endpoints (login-logs, point-adjustments, system-points); mở rộng `AdminResetPasswordResponse` với `email_sent + user_email`, inject EmailService vào route reset (KHÔNG tạo `services/admin_service.py` — logic giữ INLINE như hiện tại) |
| `backend/app/api/users.py` (hoặc tạo `me.py`) | Thêm GET `/users/me/redemptions` list + detail |
| `backend/app/api/transactions.py` | POST `/partner/transactions/qr` parse `int(qr_payload)` |
| `backend/app/api/qr.py` | XOÁ route GET `/qr` (giữ /checkin shop QR) |
| `backend/app/core/qr.py` | XOÁ personal QR primitives (giữ shop_token HMAC) |
| `backend/app/core/deps.py` | Thêm `require_staff_in_partner` dep |
| `backend/app/services/auth_service.py` | `reset_password_send_temp` integrate EmailService, trả temp_password |
| `backend/app/core/exceptions.py` | Thêm `EmailDeliveryError` |
| `backend/app/core/config.py` | Add SMTP env vars (HOST/PORT/USER/PASSWORD/FROM_EMAIL/FROM_NAME/TIMEOUT) |
| `backend/pyproject.toml` | Thêm `aiosmtplib>=3.0` |

### Frontend — files mới

| File | Trách nhiệm |
|---|---|
| `frontend/src/app/(member)/member/vouchers/page.tsx` | List redemption với tabs pending/used/expired (lowercase match BE) |
| `frontend/src/app/(member)/member/vouchers/[id]/page.tsx` | Detail + render QR `redemption_code` |
| `frontend/src/app/(partner)/partner/staff/page.tsx` | List + Add modal + Reset/Toggle actions |
| `frontend/src/app/(admin)/admin/logs/page.tsx` | 2 tabs: login logs + point adjustments |
| `frontend/src/app/(admin)/admin/system-points/page.tsx` | Tổng điểm + breakdown by partner |
| `frontend/src/lib/hooks/useRedemptions.ts` | TanStack Query hooks |
| `frontend/src/lib/hooks/useAdminLogs.ts` | TanStack Query hooks |
| `frontend/src/lib/hooks/useSystemPoints.ts` | TanStack Query hook |

### Frontend — files sửa

| File | Lý do |
|---|---|
| `frontend/src/app/(member)/member/qr/page.tsx` | Bỏ poll JWT, render `<QRCode value={user.id.toString()} />` |
| `frontend/src/app/(staff)/staff/scan/page.tsx` | Scan trả raw text → POST trực tiếp `qr_payload` |
| `frontend/src/lib/api-partner.ts` | Xoá `staffApi.updateRole`, `staffApi.remove`. Đổi `addStaff` schema. Thêm `resetStaff`, `toggleStaffActive`. Đổi POS `confirmFromQr` payload. |
| `frontend/src/lib/hooks/use-partner.ts` | Xoá `useUpdateStaffRole`, `useRemoveStaff`. Thêm `useResetStaff`, `useToggleStaff`. |
| `frontend/src/lib/api.ts` | Admin clients: `loginLogs`, `pointAdjustments`, `pointsSummary`. Auth interceptor: handle 423 + `Retry-After`. |
| `frontend/src/lib/hooks/useLogin.ts` (hoặc form login page) | Show countdown khi 423 |

---

## Phase 7.1: M6 Migration + Models + Schemas

### Task 1: Tạo Alembic revision M6 (DDL only, no model code)

**Files:**
- Create: `backend/alembic/versions/<auto-hex>_m6_login_log_partner_staff_actor.py`

- [ ] **Step 1: Generate revision**

```bash
docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend \
  alembic revision -m "m6_login_log_partner_staff_actor"
```

Expected: file mới ở `backend/alembic/versions/` với `down_revision = 'd4e5f6a7b8c9'`. Nếu không phải, sửa tay `down_revision`.

- [ ] **Step 2: Viết upgrade()**

Open file mới tạo, thay block `def upgrade()` bằng:

```python
def upgrade() -> None:
    # 1. login_log table
    op.create_table(
        "login_log",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("identifier", sa.String(255), nullable=False),
        sa.Column("ip", sa.String(45), nullable=False),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("success", sa.Boolean, nullable=False),
        sa.Column("failure_reason", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_login_log_failed_recent",
        "login_log",
        ["identifier", sa.text("created_at DESC")],
        postgresql_where=sa.text("success = false"),
    )
    op.create_index(
        "ix_login_log_user_created",
        "login_log",
        ["user_id", sa.text("created_at DESC")],
    )

    # 2. partner_staff table (chỉ chứa staff, không owner)
    op.create_table(
        "partner_staff",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("partner_id", sa.Integer, sa.ForeignKey("partners.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", name="uq_partner_staff_user"),
    )
    op.create_index("ix_partner_staff_partner", "partner_staff", ["partner_id"])

    # 3. point_ledger.actor_user_id — disable trigger để ALTER, sau đó re-enable
    op.execute("ALTER TABLE point_ledger DISABLE TRIGGER no_update_or_delete_point_ledger")
    op.add_column(
        "point_ledger",
        sa.Column(
            "actor_user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_point_ledger_actor_created",
        "point_ledger",
        ["actor_user_id", sa.text("created_at DESC")],
        postgresql_where=sa.text("actor_user_id IS NOT NULL"),
    )
    op.execute("ALTER TABLE point_ledger ENABLE TRIGGER no_update_or_delete_point_ledger")
```

- [ ] **Step 3: Viết downgrade()**

```python
def downgrade() -> None:
    op.execute("ALTER TABLE point_ledger DISABLE TRIGGER no_update_or_delete_point_ledger")
    op.drop_index("ix_point_ledger_actor_created", table_name="point_ledger")
    op.drop_column("point_ledger", "actor_user_id")
    op.execute("ALTER TABLE point_ledger ENABLE TRIGGER no_update_or_delete_point_ledger")

    op.drop_index("ix_partner_staff_partner", table_name="partner_staff")
    op.drop_table("partner_staff")

    op.drop_index("ix_login_log_user_created", table_name="login_log")
    op.drop_index("ix_login_log_failed_recent", table_name="login_log")
    op.drop_table("login_log")
```

- [ ] **Step 4: Verify SQL bằng dry-run**

```bash
docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend \
  alembic upgrade head --sql > /tmp/m6.sql
```

Đọc `/tmp/m6.sql`, đảm bảo có 3 CREATE TABLE / 3 ALTER TRIGGER, không lỗi parse.

### Task 2: Tạo `LoginLog` model

**Files:**
- Create: `backend/app/models/login_log.py`

- [ ] **Step 1: Viết model**

```python
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class LoginLog(Base):
    """Audit trail mọi attempt login. Append-only ở app code (không trigger DB)."""

    __tablename__ = "login_log"
    __table_args__ = (
        Index(
            "ix_login_log_failed_recent",
            "identifier",
            "created_at",
            postgresql_where="success = false",
        ),
        Index("ix_login_log_user_created", "user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    identifier: Mapped[str] = mapped_column(String(255), nullable=False)
    ip: Mapped[str] = mapped_column(String(45), nullable=False)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
```

Lưu ý: KHÔNG dùng `TimestampMixin` — chỉ cần `created_at`, không cần `updated_at` (append-only).

### Task 3: Tạo `PartnerStaff` model

**Files:**
- Create: `backend/app/models/partner_staff.py`

- [ ] **Step 1: Viết model**

```python
from sqlalchemy import Boolean, ForeignKey, Index, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class PartnerStaff(Base, TimestampMixin):
    """Staff thuộc 1 partner. Owner KHÔNG nằm trong bảng này (dùng partners.owner_user_id)."""

    __tablename__ = "partner_staff"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_partner_staff_user"),
        Index("ix_partner_staff_partner", "partner_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    partner_id: Mapped[int] = mapped_column(
        ForeignKey("partners.id", ondelete="RESTRICT"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
```

### Task 4: Sửa `PointLedger` model thêm `actor_user_id`

**Files:**
- Modify: `backend/app/models/point_ledger.py`

- [ ] **Step 1: Thêm import + Index trong `__table_args__`**

Thêm vào `__table_args__` tuple (sau Index `ix_point_ledger_partner_created`):

```python
        Index(
            "ix_point_ledger_actor_created",
            "actor_user_id",
            "created_at",
            postgresql_where="actor_user_id IS NOT NULL",
        ),
```

Thêm `ForeignKey` vào import nếu chưa có (đã có).

- [ ] **Step 2: Thêm column ngay sau `description`**

```python
    actor_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
```

### Task 5: Export models mới trong `__init__.py`

**Files:**
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: Thêm exports**

Thêm 2 dòng vào `from .X import Y` block:

```python
from .login_log import LoginLog
from .partner_staff import PartnerStaff
```

Update `__all__` nếu có.

### Task 6: Tạo Pydantic schemas

**Files:**
- Create: `backend/app/schemas/login_log.py`
- Create: `backend/app/schemas/partner_staff.py`

- [ ] **Step 1: Viết `schemas/login_log.py`**

```python
from datetime import datetime

from pydantic import BaseModel


class LoginLogResponse(BaseModel):
    id: int
    user_id: int | None
    identifier: str
    ip: str
    user_agent: str | None
    success: bool
    failure_reason: str | None
    created_at: datetime
    user_email: str | None = None  # populated by service via JOIN

    model_config = {"from_attributes": True}


class LoginLogListResponse(BaseModel):
    items: list[LoginLogResponse]
    total: int
    limit: int
    offset: int
```

- [ ] **Step 2: Viết `schemas/partner_staff.py`**

```python
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class StaffCreateRequest(BaseModel):
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=20)
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=100)


class StaffPatchRequest(BaseModel):
    is_active: bool


class StaffResponse(BaseModel):
    id: int                # partner_staff.id
    user_id: int
    email: str | None
    phone: str | None
    full_name: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class StaffListResponse(BaseModel):
    items: list[StaffResponse]
    total: int


class StaffResetResponse(BaseModel):
    email_sent: bool
    temp_password: str
    message: str
```

### Task 7: Apply migration + verify schema

- [ ] **Step 1: Apply M6**

```bash
docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend alembic upgrade head
```

Expected: `INFO  [alembic.runtime.migration] Running upgrade d4e5f6a7b8c9 -> <new_hex>, m6_login_log_partner_staff_actor`.

- [ ] **Step 2: Verify schema**

```bash
docker exec loyalty-postgres-prod psql -U loyalty -d loyalty -c "\d login_log"
docker exec loyalty-postgres-prod psql -U loyalty -d loyalty -c "\d partner_staff"
docker exec loyalty-postgres-prod psql -U loyalty -d loyalty -c "\d point_ledger"
```

Expected: thấy đủ columns + indexes như spec.

- [ ] **Step 3: Verify trigger còn active**

```bash
docker exec loyalty-postgres-prod psql -U loyalty -d loyalty -c \
  "SELECT tgname, tgenabled FROM pg_trigger WHERE tgrelid = 'point_ledger'::regclass;"
```

Expected: `no_update_or_delete_point_ledger | O` (enabled).

### Task 8: Commit Phase 7.1

- [ ] **Step 1: Stage + commit**

```bash
git add backend/alembic/versions/ backend/app/models/login_log.py backend/app/models/partner_staff.py backend/app/models/__init__.py backend/app/models/point_ledger.py backend/app/schemas/login_log.py backend/app/schemas/partner_staff.py
git commit -m "feat(schema): M6 add login_log + partner_staff + point_ledger.actor_user_id"
```

---

## Phase 7.2: EmailService + integrate forgot/reset password

### Task 1: Add `aiosmtplib` dependency

**Files:**
- Modify: `backend/pyproject.toml`

- [ ] **Step 1: Thêm vào `[project.dependencies]`**

```toml
"aiosmtplib>=3.0",
```

- [ ] **Step 2: Rebuild backend container**

```bash
docker compose -p loyalty-prod -f docker-compose.prod.yml build backend
docker compose -p loyalty-prod -f docker-compose.prod.yml up -d backend
docker logs loyalty-backend-prod --tail 20
```

Expected: container start OK, log `Application startup complete`.

### Task 2: Add SMTP config + EmailDeliveryError exception

**Files:**
- Modify: `backend/app/core/config.py`
- Modify: `backend/app/core/exceptions.py`

- [ ] **Step 1: Thêm SMTP fields vào `Settings` class**

Trong `app/core/config.py` thêm vào class Settings:

```python
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_from_name: str = "Loyalty Platform"
    smtp_timeout: int = 10
```

- [ ] **Step 2: Thêm exception**

Trong `app/core/exceptions.py` thêm:

```python
class EmailDeliveryError(Exception):
    """Raise khi SMTP gửi email fail (timeout, auth, network)."""
    pass
```

### Task 3: Tạo `EmailService` (TDD)

**Files:**
- Create: `backend/app/services/email_service.py`
- Create: `backend/tests/unit/test_email_service.py`

- [ ] **Step 1: Viết failing test**

```python
import asyncio

import pytest

from app.core.exceptions import EmailDeliveryError
from app.services.email_service import EmailService


@pytest.mark.asyncio
async def test_send_email_timeout_raises(monkeypatch):
    """SMTP hang → wait_for timeout → EmailDeliveryError."""
    async def fake_send(*args, **kwargs):
        await asyncio.sleep(60)

    monkeypatch.setattr("aiosmtplib.send", fake_send)
    service = EmailService(timeout=1)
    with pytest.raises(EmailDeliveryError, match="timeout"):
        await service.send_email(
            to="x@example.com",
            subject="test",
            body="hi",
        )


@pytest.mark.asyncio
async def test_send_email_smtp_error_raises(monkeypatch):
    """aiosmtplib raise → EmailDeliveryError với cause."""
    async def fake_send(*args, **kwargs):
        raise ConnectionError("Connection refused")

    monkeypatch.setattr("aiosmtplib.send", fake_send)
    service = EmailService(timeout=10)
    with pytest.raises(EmailDeliveryError):
        await service.send_email(to="x@example.com", subject="s", body="b")
```

- [ ] **Step 2: Run test, expect FAIL (no module)**

```bash
docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend \
  pytest tests/unit/test_email_service.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement EmailService**

```python
import asyncio
import logging
from email.message import EmailMessage

import aiosmtplib

from app.core.config import settings
from app.core.exceptions import EmailDeliveryError

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self, timeout: int | None = None):
        self.timeout = timeout if timeout is not None else settings.smtp_timeout

    async def send_email(self, to: str, subject: str, body: str) -> None:
        """Gửi plain text email. Raise EmailDeliveryError nếu fail/timeout."""
        msg = EmailMessage()
        msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)

        try:
            await asyncio.wait_for(
                aiosmtplib.send(
                    msg,
                    hostname=settings.smtp_host,
                    port=settings.smtp_port,
                    username=settings.smtp_user,
                    password=settings.smtp_password,
                    start_tls=True,
                ),
                timeout=self.timeout,
            )
        except asyncio.TimeoutError as e:
            logger.warning("email_service.timeout", extra={"to": to, "subject": subject})
            raise EmailDeliveryError(f"SMTP send timeout after {self.timeout}s") from e
        except Exception as e:
            logger.warning("email_service.error", extra={"to": to, "error": str(e)})
            raise EmailDeliveryError(f"SMTP send failed: {e}") from e
```

- [ ] **Step 4: Run test, expect PASS**

```bash
docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend \
  pytest tests/unit/test_email_service.py -v
```

Expected: 2 passed.

### Task 4: Integrate vào `/auth/forgot-password` (fail-silent)

**Files:**
- Modify: `backend/app/services/auth_service.py`
- Modify: `backend/app/api/auth.py`

- [ ] **Step 1: Sửa `auth_service.reset_password_send_temp` trả thêm temp_password**

Tìm method, đổi return signature:

```python
async def reset_password_send_temp(self, email: str) -> tuple[str, str] | None:
    """Reset password + return (temp_password, target_email).
    
    Caller decide có gửi email hay không (asymmetric policy).
    Return None nếu user không tồn tại.
    """
    # ... existing logic gen temp_password + bcrypt + UPDATE
    # Cuối cùng return (temp_password, user.email)
```

- [ ] **Step 2: Sửa route `/auth/forgot-password`**

```python
@router.post("/forgot-password", status_code=200)
@limiter.limit("5/minute")
async def forgot_password(
    request: Request,
    body: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    result = await service.reset_password_send_temp(email=body.email)
    if result is not None:
        temp_password, target_email = result
        email_service = EmailService()
        try:
            await email_service.send_email(
                to=target_email,
                subject="[Loyalty] Mật khẩu mới của bạn",
                body=(
                    f"Chào bạn,\n\n"
                    f"Bạn vừa yêu cầu đặt lại mật khẩu.\n"
                    f"Mật khẩu tạm thời: {temp_password}\n\n"
                    f"Vui lòng đăng nhập và đổi mật khẩu ngay sau khi nhận được."
                ),
            )
        except EmailDeliveryError:
            logger.warning(
                "auth.forgot_password.SMTP_FAIL",
                extra={"email": target_email, "temp_password_dev": temp_password},
            )
            # Fail-silent — vẫn trả 200 generic để không leak
    return {"message": "Nếu email hợp lệ, mật khẩu mới đã được gửi."}
```

### Task 5: Integrate vào `/admin/users/{id}/reset-password`

**Files:**
- Modify: `backend/app/api/admin.py` (logic reset đang INLINE ở route lines 660-685, KHÔNG có `services/admin_service.py`)

> **CRITICAL — đọc trước khi sửa**: Hiện tại `api/admin.py` đã có:
> - Class `AdminResetPasswordResponse(user_id: int, temporary_password: str)` (line 535)
> - Helper `_generate_temp_password(length=12)` module-private (line 540)
> - Route `POST /admin/users/{user_id}/reset-password` inline 663-685, không qua service layer.
>
> Plan này CHỈ extend response schema + inject email send vào route — KHÔNG tạo `admin_service.py`.

- [ ] **Step 1: Mở rộng `AdminResetPasswordResponse` (giữ tên `temporary_password` để khớp FE & test cũ)**

Sửa class ở `api/admin.py` line 535 (giữ `user_id` + `temporary_password`, thêm 2 field):

```python
class AdminResetPasswordResponse(BaseModel):
    user_id: int
    temporary_password: str
    email_sent: bool = False
    user_email: str | None = None
```

- [ ] **Step 2: Inject email send vào route inline**

Sửa function body `reset_user_password` (line 663-685), giữ logic gen temp + bcrypt nguyên, chỉ thêm khối try-send-email + populate response:

```python
@router.post(
    "/users/{user_id}/reset-password", response_model=AdminResetPasswordResponse
)
async def reset_user_password(
    user_id: int,
    admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminResetPasswordResponse:
    """Super Admin reset mật khẩu user, trả mật khẩu tạm thời để chuyển cho user."""
    target = await db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="Người dùng không tồn tại")

    if target.id == admin.id:
        raise HTTPException(
            status_code=409,
            detail="Không thể reset mật khẩu của chính mình qua trang admin",
        )

    temp_password = _generate_temp_password()
    target.password_hash = hash_password(temp_password)
    await db.commit()

    email_sent = False
    if target.email:
        try:
            await EmailService().send_email(
                to=target.email,
                subject="[Loyalty] Admin đã reset mật khẩu của bạn",
                body=(
                    f"Chào bạn,\n\n"
                    f"Quản trị viên vừa reset mật khẩu của bạn.\n"
                    f"Mật khẩu tạm thời: {temp_password}\n\n"
                    f"Đăng nhập và đổi mật khẩu ngay."
                ),
            )
            email_sent = True
        except EmailDeliveryError:
            logger.warning(
                "admin.reset_password.SMTP_FAIL",
                extra={"user_id": user_id, "temp_password_dev": temp_password},
            )

    return AdminResetPasswordResponse(
        user_id=target.id,
        temporary_password=temp_password,
        email_sent=email_sent,
        user_email=target.email,
    )
```

- [ ] **Step 3: Đảm bảo import `EmailService` + `EmailDeliveryError` + `logger` ở đầu `api/admin.py`**

```python
import logging
from app.services.email_service import EmailService
from app.core.exceptions import EmailDeliveryError

logger = logging.getLogger(__name__)
```

(skip nếu đã có sẵn).

### Task 6: Smoke test gửi email thật

- [ ] **Step 1: Restart backend pickup .env**

```bash
docker compose -p loyalty-prod -f docker-compose.prod.yml restart backend
docker logs loyalty-backend-prod --tail 30 | grep -i smtp
```

- [ ] **Step 2: Trigger forgot password cho khach1@gmail.com**

```bash
curl -X POST https://loyalty.ecom-bill.com/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email":"khach1@gmail.com"}'
```

Expected: `{"message":"Nếu email hợp lệ..."}` + log backend không thấy `SMTP_FAIL` (gửi OK).

- [ ] **Step 3: Verify hộp thư**

User mở Gmail khach1@gmail.com → nhận email từ `Loyalty Platform <mysorcerer2k2@gmail.com>` chứa temp password.

- [ ] **Step 4: Login với temp password**

```bash
curl -X POST https://loyalty.ecom-bill.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"identifier":"khach1@gmail.com","password":"<TEMP_PWD_FROM_EMAIL>"}'
```

Expected: 200 + access_token. Sau đó reset lại về `khach1234` qua `/auth/change-password` để các test sau chạy được.

### Task 7: Commit Phase 7.2

```bash
git add backend/pyproject.toml backend/app/core/config.py backend/app/core/exceptions.py backend/app/services/email_service.py backend/tests/unit/test_email_service.py backend/app/services/auth_service.py backend/app/api/auth.py backend/app/api/admin.py
git commit -m "feat(email): aiosmtplib EmailService + integrate forgot/admin reset password"
```

---

## Phase 7.3: QR raw user_id (BE drop endpoint + FE render local)

### Task 1: Strip personal QR primitives trong `core/qr.py`

**Files:**
- Modify: `backend/app/core/qr.py`

- [ ] **Step 1: Đọc file hiện tại để xác định scope strip**

```bash
docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend \
  cat app/core/qr.py
```

Note danh sách function cần XOÁ: `sign_qr_jwt`, `decode_qr_jwt`, `generate_fallback_code`, `verify_fallback_code_with_candidates`. **GIỮ**: `sign_shop_token`, `verify_shop_token`.

- [ ] **Step 2: Xoá 4 functions trên + import liên quan (jose JWT, hashlib personal-qr-only)**

Giữ lại HMAC primitives nếu shop_token cần.

### Task 2: Xoá route `GET /member/qr`

**Files:**
- Modify: `backend/app/api/qr.py` (router prefix `/member`, route `GET /qr` → URL final `/member/qr`)

- [ ] **Step 1: Verify route hiện tại**

```bash
grep -n '@router.get\|prefix=' backend/app/api/qr.py
```
Expected: `prefix="/member"` (line 17), `@router.get("/qr")` (line 20), `@router.get("/checkin")` (line 33).

- [ ] **Step 2: Xoá route handler `@router.get("/qr")` + function body. GIỮ `@router.get("/checkin")` shop QR. Xoá import liên quan personal-QR (sign_qr_jwt, generate_fallback_code...).**

### Task 3: Refactor `services/qr_service.py` (decode QR layer)

**Files:**
- Modify: `backend/app/services/qr_service.py`

> **CRITICAL — đọc trước khi sửa**: Logic decode QR KHÔNG inline ở `api/transactions.py`. Route gọi `TransactionService.create_qr_customer()` → service gọi `QrService.decode_qr_payload()`. Phải sửa ở `qr_service.py`, route giữ nguyên (thin route / fat service pattern).

- [ ] **Step 1: Đọc current `qr_service.py`**

```bash
cat backend/app/services/qr_service.py
```

Note: hiện tại `decode_qr_payload()` gọi `decode_qr_jwt` + `verify_fallback_code_with_candidates` từ `core/qr.py`.

- [ ] **Step 2: Rewrite `decode_qr_payload()` thành parse int + DB lookup**

```python
# backend/app/services/qr_service.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.membership import Membership
from app.models.user import User


class QrPayloadInvalidError(Exception):
    pass


class QrUserNotFoundError(Exception):
    pass


class QrUserNotMemberError(Exception):
    pass


class QrService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def decode_qr_payload(self, payload: str, partner_id: int) -> tuple[User, Membership]:
        """Parse QR payload (raw user_id string) và return (user, membership).

        Raises:
            QrPayloadInvalidError: payload không phải số dương.
            QrUserNotFoundError: user không tồn tại hoặc inactive.
            QrUserNotMemberError: user chưa là thành viên partner này.
        """
        try:
            user_id = int(payload.strip())
            if user_id <= 0:
                raise ValueError
        except (ValueError, AttributeError):
            raise QrPayloadInvalidError("QR payload không hợp lệ.")

        user = await self.db.get(User, user_id)
        if user is None or not user.is_active:
            raise QrUserNotFoundError("Không tìm thấy khách hàng từ QR.")

        membership = await self.db.scalar(
            select(Membership).where(
                Membership.partner_id == partner_id,
                Membership.user_id == user_id,
            )
        )
        if membership is None:
            raise QrUserNotMemberError("Khách hàng chưa là thành viên shop này.")

        return user, membership
```

- [ ] **Step 3: Update `transaction_service.create_qr_customer` map exception → HTTPException ở route layer**

Trong `api/transactions.py` route `POST /qr`: catch 3 exception mới → map `QrPayloadInvalidError → 400`, `QrUserNotFoundError → 404`, `QrUserNotMemberError → 404`.

- [ ] **Step 4: Verify imports trong `services/qr_service.py` không còn reference `core/qr.py` personal-QR primitives**

```bash
grep -n "decode_qr_jwt\|sign_qr_jwt\|verify_fallback_code\|generate_fallback_code" backend/app/services/qr_service.py
```
Expected: 0 hits.

### Task 4: FE — sửa `/member/qr/page.tsx` render local

**Files:**
- Modify: `frontend/src/app/(member)/member/qr/page.tsx`

- [ ] **Step 1: Đọc file hiện tại**

```bash
cat frontend/src/app/\(member\)/member/qr/page.tsx
```

- [ ] **Step 2: Thay toàn bộ logic poll JWT bằng render local**

```tsx
"use client";

import { QRCodeSVG } from "qrcode.react";
import { useAuthStore } from "@/lib/auth-store";

export default function MemberQRPage() {
  const user = useAuthStore((s) => s.user);
  if (!user) return <div className="p-4">Đang tải...</div>;

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] p-4">
      <h1 className="text-xl font-semibold mb-4">QR cá nhân của bạn</h1>
      <div className="bg-white p-6 rounded-2xl shadow-lg">
        <QRCodeSVG value={user.id.toString()} size={240} level="H" />
      </div>
      <p className="mt-4 text-sm text-muted-foreground">
        Xuất trình QR này để nhân viên quét tích điểm.
      </p>
      <p className="mt-2 text-xs text-muted-foreground">ID: {user.id}</p>
    </div>
  );
}
```

- [ ] **Step 3: Verify `qrcode.react` đã trong dependencies**

```bash
grep qrcode frontend/package.json
```

Expected: `"qrcode.react": "^X.Y.Z"`. Nếu thiếu: `npm install qrcode.react` trong `frontend/`.

### Task 5: FE — sửa `staff/scan` parse raw text

**Files:**
- Modify: `frontend/src/app/(staff)/staff/scan/page.tsx` (hoặc page tương đương)

- [ ] **Step 1: Tìm chỗ scanner trả `decodedText`**

```bash
grep -rn "decodedText\|onScanSuccess" frontend/src/app/\(staff\)/
```

- [ ] **Step 2: Sửa POST body**

Đổi từ truyền JWT/object → truyền raw text trực tiếp:

```ts
const onScanSuccess = async (decodedText: string) => {
  const result = await transactionsApi.confirmFromQr({
    qr_payload: decodedText.trim(),
    gross_amount: amount,
    method: "cash",
  });
  // hiển thị result.points_earned + customer info
};
```

### Task 6: FE — sửa `api-partner.ts` POS `confirmFromQr`

**Files:**
- Modify: `frontend/src/lib/api-partner.ts`

- [ ] **Step 1: Tìm `confirmFromQr` (hoặc `createFromQr`)**

```bash
grep -n "QrPayload\|qr_payload" frontend/src/lib/api-partner.ts
```

- [ ] **Step 2: Đổi type signature** payload chỉ là `{qr_payload: string, gross_amount: number, method: string, note?: string}`. Xoá tham chiếu JWT decode logic ở FE nếu có.

### Task 7: Smoke test scan flow E2E

- [ ] **Step 1: Verify FE render QR**

Đăng nhập khach1, vào `/member/qr` → xem QR hiển thị, mở QR scanner phone scan → đọc ra string `"5"` (user.id của khach1).

- [ ] **Step 2: Verify POS scan**

Đăng nhập owner Cafe Cộng, vào `/staff/scan` (or merchant POS), scan QR vừa rồi, nhập gross_amount=50000, submit → 200, response chứa `points_earned`.

- [ ] **Step 3: Verify ledger**

```bash
docker exec loyalty-postgres-prod psql -U loyalty -d loyalty -c \
  "SELECT id, user_id, partner_id, delta, reason FROM point_ledger ORDER BY id DESC LIMIT 3;"
```

Expected: row mới với `user_id=5, reason='earn'`.

### Task 8: Commit Phase 7.3

```bash
git add backend/app/core/qr.py backend/app/api/qr.py backend/app/api/transactions.py frontend/src/app/\(member\)/member/qr/ frontend/src/app/\(staff\)/staff/scan/ frontend/src/lib/api-partner.ts
git commit -m "feat(qr): personal QR raw user_id (FE local render, BE drop /qr endpoint)"
```

---

## Phase 7.4: Ví Voucher (BE endpoints + FE pages)

### Task 1: BE — GET `/users/me/redemptions` list endpoint

**Files:**
- Modify: `backend/app/api/users.py` (hoặc tạo `me_redemptions.py` router con)
- Modify: `backend/app/schemas/redemption.py` (thêm list response nếu chưa có)

- [ ] **Step 1: Add schema**

Trong `schemas/redemption.py`:

```python
class MyRedemptionListItem(BaseModel):
    id: int
    redemption_code: str
    points_spent: int
    status: str
    redeemed_at: datetime
    expires_at: datetime
    used_at: datetime | None
    partner_id: int
    partner_name: str
    reward_id: int
    reward_name: str
    reward_image_url: str | None

    model_config = {"from_attributes": True}


class MyRedemptionListResponse(BaseModel):
    items: list[MyRedemptionListItem]
    total: int
    limit: int
    offset: int
```

- [ ] **Step 2: Add route**

```python
@router.get("/me/redemptions", response_model=MyRedemptionListResponse)
async def list_my_redemptions(
    status: str | None = Query(default=None, regex="^(pending|used|expired)$"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = (
        select(Redemption, Partner.name.label("partner_name"), Reward.name.label("reward_name"), Reward.image_url.label("reward_image_url"))
        .join(Partner, Partner.id == Redemption.partner_id)
        .join(Reward, Reward.id == Redemption.reward_id)
        .where(Redemption.user_id == user.id)
    )
    if status:
        stmt = stmt.where(Redemption.status == status)
    
    total_stmt = select(func.count()).select_from(Redemption).where(Redemption.user_id == user.id)
    if status:
        total_stmt = total_stmt.where(Redemption.status == status)
    total = await db.scalar(total_stmt)

    stmt = stmt.order_by(Redemption.redeemed_at.desc()).limit(limit).offset(offset)
    rows = (await db.execute(stmt)).all()
    items = [
        MyRedemptionListItem(
            id=r.Redemption.id,
            redemption_code=r.Redemption.redemption_code,
            points_spent=r.Redemption.points_spent,
            status=r.Redemption.status,
            redeemed_at=r.Redemption.redeemed_at,
            expires_at=r.Redemption.expires_at,
            used_at=r.Redemption.used_at,
            partner_id=r.Redemption.partner_id,
            partner_name=r.partner_name,
            reward_id=r.Redemption.reward_id,
            reward_name=r.reward_name,
            reward_image_url=r.reward_image_url,
        )
        for r in rows
    ]
    return MyRedemptionListResponse(items=items, total=total, limit=limit, offset=offset)
```

### Task 2: BE — GET `/users/me/redemptions/{id}` detail

- [ ] **Step 1: Add schema**

```python
class MyRedemptionDetailResponse(MyRedemptionListItem):
    snapshot_image_url: str | None
    reward_description: str | None
    reward_terms: str | None
```

- [ ] **Step 2: Add route**

```python
@router.get("/me/redemptions/{redemption_id}", response_model=MyRedemptionDetailResponse)
async def get_my_redemption(
    redemption_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = (
        select(Redemption, Partner, Reward)
        .join(Partner, Partner.id == Redemption.partner_id)
        .join(Reward, Reward.id == Redemption.reward_id)
        .where(Redemption.id == redemption_id, Redemption.user_id == user.id)
    )
    row = (await db.execute(stmt)).one_or_none()
    if row is None:
        raise HTTPException(404, "Không tìm thấy quà đã đổi.")
    r, p, w = row
    return MyRedemptionDetailResponse(
        id=r.id, redemption_code=r.redemption_code, points_spent=r.points_spent,
        status=r.status, redeemed_at=r.redeemed_at, expires_at=r.expires_at,
        used_at=r.used_at, partner_id=p.id, partner_name=p.name,
        reward_id=w.id, reward_name=w.name, reward_image_url=w.image_url,
        snapshot_image_url=r.snapshot_image_url,
        reward_description=w.description, reward_terms=w.terms,
    )
```

### Task 3: Test endpoints qua curl

- [ ] **Step 1: Login khach1, lưu token**

```bash
TOKEN=$(curl -s -X POST https://loyalty.ecom-bill.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"identifier":"khach1@gmail.com","password":"khach1234"}' | jq -r .access_token)
```

- [ ] **Step 2: Call list**

```bash
curl -s "https://loyalty.ecom-bill.com/users/me/redemptions?status=pending" \
  -H "Authorization: Bearer $TOKEN" | jq
```

Expected: `{items: [...], total: N, limit: 50, offset: 0}`.

- [ ] **Step 3: Call detail (lấy id từ list)**

```bash
curl -s "https://loyalty.ecom-bill.com/users/me/redemptions/1" \
  -H "Authorization: Bearer $TOKEN" | jq
```

Expected: detail object với `redemption_code` 8 ký tự.

### Task 4: FE — `useRedemptions` hook

**Files:**
- Create: `frontend/src/lib/hooks/useRedemptions.ts`

- [ ] **Step 1: Implement**

```ts
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export type RedemptionStatus = "pending" | "used" | "expired";

export type MyRedemption = {
  id: number;
  redemption_code: string;
  points_spent: number;
  status: RedemptionStatus;
  redeemed_at: string;
  expires_at: string;
  used_at: string | null;
  partner_id: number;
  partner_name: string;
  reward_id: number;
  reward_name: string;
  reward_image_url: string | null;
};

export function useMyRedemptions(status?: RedemptionStatus) {
  return useQuery({
    queryKey: ["my-redemptions", status],
    queryFn: async () => {
      const res = await api.get("/users/me/redemptions", {
        params: status ? { status } : {},
      });
      return res.data as { items: MyRedemption[]; total: number };
    },
  });
}

export function useMyRedemption(id: number | null) {
  return useQuery({
    queryKey: ["my-redemption", id],
    queryFn: async () => {
      const res = await api.get(`/users/me/redemptions/${id}`);
      return res.data as MyRedemption & {
        snapshot_image_url: string | null;
        reward_description: string | null;
        reward_terms: string | null;
      };
    },
    enabled: id !== null,
  });
}
```

### Task 5: FE — `/member/vouchers/page.tsx` (list with tabs)

**Files:**
- Create: `frontend/src/app/(member)/member/vouchers/page.tsx`

- [ ] **Step 1: Implement**

```tsx
"use client";

import { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { useMyRedemptions, type RedemptionStatus } from "@/lib/hooks/useRedemptions";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function MyVouchersPage() {
  const [tab, setTab] = useState<RedemptionStatus>("pending");
  const { data, isLoading } = useMyRedemptions(tab);

  return (
    <div className="p-4 max-w-md mx-auto">
      <h1 className="text-2xl font-semibold mb-4">Ví Voucher</h1>
      <Tabs value={tab} onValueChange={(v) => setTab(v as RedemptionStatus)}>
        <TabsList className="grid grid-cols-3 mb-4">
          <TabsTrigger value="pending">Chưa dùng</TabsTrigger>
          <TabsTrigger value="used">Đã dùng</TabsTrigger>
          <TabsTrigger value="expired">Hết hạn</TabsTrigger>
        </TabsList>
      </Tabs>

      {isLoading && <p>Đang tải...</p>}
      {data && data.items.length === 0 && (
        <p className="text-muted-foreground text-center py-8">Chưa có voucher nào.</p>
      )}
      <div className="space-y-3">
        {data?.items.map((r) => (
          <Link key={r.id} href={`/member/vouchers/${r.id}`}>
            <div className="flex gap-3 p-3 border rounded-xl hover:bg-accent">
              {r.reward_image_url && (
                <Image src={r.reward_image_url} alt={r.reward_name} width={64} height={64} className="rounded object-cover" />
              )}
              <div className="flex-1">
                <p className="font-medium">{r.reward_name}</p>
                <p className="text-xs text-muted-foreground">{r.partner_name}</p>
                <p className="text-xs">HSD: {new Date(r.expires_at).toLocaleDateString("vi-VN")}</p>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
```

### Task 6: FE — `/member/vouchers/[id]/page.tsx` (detail + QR)

**Files:**
- Create: `frontend/src/app/(member)/member/vouchers/[id]/page.tsx`

- [ ] **Step 1: Implement**

```tsx
"use client";

import { useParams } from "next/navigation";
import { QRCodeSVG } from "qrcode.react";
import { useMyRedemption } from "@/lib/hooks/useRedemptions";

export default function VoucherDetailPage() {
  const params = useParams();
  const id = Number(params.id);
  const { data, isLoading } = useMyRedemption(id);

  if (isLoading) return <div className="p-4">Đang tải...</div>;
  if (!data) return <div className="p-4">Không tìm thấy.</div>;

  return (
    <div className="p-4 max-w-md mx-auto flex flex-col items-center">
      <h1 className="text-xl font-semibold mb-2">{data.reward_name}</h1>
      <p className="text-sm text-muted-foreground mb-4">{data.partner_name}</p>

      {data.status === "pending" && (
        <>
          <div className="bg-white p-6 rounded-2xl shadow-lg">
            <QRCodeSVG value={data.redemption_code} size={220} level="H" />
          </div>
          <p className="mt-3 font-mono text-lg tracking-wider">{data.redemption_code}</p>
          <p className="mt-2 text-xs text-muted-foreground">
            HSD: {new Date(data.expires_at).toLocaleString("vi-VN")}
          </p>
        </>
      )}
      {data.status === "used" && (
        <p className="text-green-600">Đã sử dụng lúc {new Date(data.used_at!).toLocaleString("vi-VN")}</p>
      )}
      {data.status === "expired" && <p className="text-destructive">Voucher đã hết hạn.</p>}

      {data.reward_description && (
        <div className="mt-6 w-full">
          <h2 className="font-medium">Mô tả</h2>
          <p className="text-sm">{data.reward_description}</p>
        </div>
      )}
      {data.reward_terms && (
        <div className="mt-4 w-full">
          <h2 className="font-medium">Điều khoản</h2>
          <p className="text-sm whitespace-pre-line">{data.reward_terms}</p>
        </div>
      )}
    </div>
  );
}
```

### Task 7: Smoke test E2E

- [ ] **Step 1: Build FE + verify type-check**

```bash
cd frontend && npx tsc --noEmit
```

Expected: 0 errors.

- [ ] **Step 2: Browser test**

Đăng nhập khach1, mở `/member/vouchers` → thấy tab + list. Click voucher pending → trang detail render QR `redemption_code`. Click tab used/expired không lỗi.

### Task 8: Commit Phase 7.4

```bash
git add backend/app/api/users.py backend/app/schemas/redemption.py frontend/src/lib/hooks/useRedemptions.ts frontend/src/app/\(member\)/member/vouchers/
git commit -m "feat(member): Ví Voucher list + detail page (FE render QR redemption_code)"
```

---

## Phase 7.5: Login log + lock 5/15min + 423 Locked

### Task 1: `LoginLogService` (TDD)

**Files:**
- Create: `backend/app/services/login_log_service.py`
- Create: `backend/tests/unit/test_login_log_service.py`

- [ ] **Step 1: Failing test**

```python
import pytest
from datetime import datetime, timedelta, timezone

from app.models.login_log import LoginLog
from app.services.login_log_service import LoginLogService


@pytest.mark.asyncio
async def test_count_recent_failures_excludes_old(db_session):
    """Failed records ngoài 15 phút không count."""
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


@pytest.mark.asyncio
async def test_count_recent_failures_excludes_success(db_session):
    """success=True không count vào failure window."""
    now = datetime.now(timezone.utc)
    db_session.add_all([
        LoginLog(identifier="x@y.com", ip="1.1.1.1", success=True, created_at=now),
        LoginLog(identifier="x@y.com", ip="1.1.1.1", success=False,
                 failure_reason="wrong_password", created_at=now),
    ])
    await db_session.commit()
    svc = LoginLogService(db_session)
    assert await svc.count_recent_failures("x@y.com", minutes=15) == 1
```

- [ ] **Step 2: Run test → FAIL (no service)**

- [ ] **Step 3: Implement**

```python
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.login_log import LoginLog


class LoginLogService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_attempt(
        self,
        *,
        identifier: str,
        ip: str,
        success: bool,
        user_id: int | None = None,
        user_agent: str | None = None,
        failure_reason: str | None = None,
    ) -> LoginLog:
        ua = user_agent[:500] if user_agent else None
        log = LoginLog(
            identifier=identifier,
            ip=ip,
            success=success,
            user_id=user_id,
            user_agent=ua,
            failure_reason=failure_reason,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(log)
        await self.db.flush()
        return log

    async def count_recent_failures(self, identifier: str, *, minutes: int = 15) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        return (await self.db.scalar(
            select(func.count())
            .select_from(LoginLog)
            .where(
                LoginLog.identifier == identifier,
                LoginLog.success.is_(False),
                LoginLog.created_at > cutoff,
            )
        )) or 0
```

- [ ] **Step 4: Run test → PASS**

### Task 2: Integrate vào POST `/auth/login`

**Files:**
- Modify: `backend/app/api/auth.py`

- [ ] **Step 1: Sửa route login**

```python
LOCK_THRESHOLD = 5
LOCK_WINDOW_MIN = 15


@router.post("/login", response_model=TokenResponse)
@limiter.limit("30/minute")
async def login(
    request: Request,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    log_svc = LoginLogService(db)
    ip = request.headers.get("x-forwarded-for", request.client.host).split(",")[0].strip()
    user_agent = request.headers.get("user-agent")

    # Lock check TRƯỚC khi verify password — KHÔNG ghi log row khi reject
    fail_count = await log_svc.count_recent_failures(body.identifier, minutes=LOCK_WINDOW_MIN)
    if fail_count >= LOCK_THRESHOLD:
        raise HTTPException(
            status_code=423,
            detail=f"Tài khoản tạm khoá {LOCK_WINDOW_MIN} phút do sai quá nhiều lần.",
            headers={"Retry-After": str(LOCK_WINDOW_MIN * 60)},
        )

    auth_svc = AuthService(db)
    try:
        user = await auth_svc.authenticate(body.identifier, body.password)
    except InvalidCredentialsError:
        # AuthService.authenticate() raise duy nhất InvalidCredentialsError
        # cho mọi failure (user-not-found / wrong password / inactive).
        # Lookup user qua identifier (email/phone) để gán user_id nếu tồn tại.
        existing = await db.scalar(
            select(User).where(
                or_(User.email == body.identifier, User.phone == body.identifier)
            )
        )
        await log_svc.log_attempt(
            identifier=body.identifier, ip=ip, success=False,
            user_id=existing.id if existing else None,
            user_agent=user_agent, failure_reason="wrong_password",
        )
        await db.commit()
        raise HTTPException(401, "Thông tin đăng nhập không đúng.")

    await log_svc.log_attempt(
        identifier=body.identifier, ip=ip, success=True,
        user_id=user.id, user_agent=user_agent,
    )
    await db.commit()
    return create_token_pair(user)
```

Imports cần thêm: `from sqlalchemy import select, or_`, `from app.models.user import User`, `from app.services.auth_service import AuthService, InvalidCredentialsError`, `from app.services.login_log_service import LoginLogService`.

> **Decision (sau code-review #2)**: `AuthService.authenticate()` ở `backend/app/services/auth_service.py:85,91,125` raise duy nhất `InvalidCredentialsError`. KHÔNG refactor split exception (giữ scope đồ án). Mọi failure log `failure_reason="wrong_password"` đồng nhất. Trade-off: mất nuance giữa user-not-found vs wrong password vs inactive — chấp nhận được cho thesis.

### Task 3: FE — handle 423 + Retry-After

**Files:**
- Modify: `frontend/src/lib/api.ts`
- Modify: `frontend/src/app/(auth)/login/page.tsx` (hoặc form login)

- [ ] **Step 1: Update axios interceptor**

```ts
api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 423) {
      const retryAfter = parseInt(err.response.headers["retry-after"] || "900", 10);
      err.lockedUntil = Date.now() + retryAfter * 1000;
    }
    if (err.response?.status === 401) {
      // existing logic redirect
    }
    return Promise.reject(err);
  }
);
```

- [ ] **Step 2: Login form show countdown**

Trong handler submit:

```tsx
} catch (err: any) {
  if (err.response?.status === 423) {
    const lockedUntil = err.lockedUntil as number;
    const interval = setInterval(() => {
      const remaining = Math.max(0, Math.floor((lockedUntil - Date.now()) / 1000));
      if (remaining === 0) {
        setError(null);
        clearInterval(interval);
      } else {
        const min = Math.floor(remaining / 60);
        const sec = remaining % 60;
        setError(`Tài khoản tạm khoá. Thử lại sau ${min}:${sec.toString().padStart(2, "0")}`);
      }
    }, 1000);
  } else {
    setError(err.response?.data?.detail || "Đăng nhập thất bại");
  }
}
```

### Task 4: Smoke test 5-fail-lock

- [ ] **Step 1: TRUNCATE login_log**

```bash
docker exec loyalty-postgres-prod psql -U loyalty -d loyalty -c "TRUNCATE login_log;"
```

- [ ] **Step 2: Send 5 wrong-password requests**

```bash
for i in 1 2 3 4 5; do
  curl -s -o /dev/null -w "%{http_code}\n" -X POST https://loyalty.ecom-bill.com/auth/login \
    -H "Content-Type: application/json" \
    -d '{"identifier":"khach1@gmail.com","password":"WRONG"}'
done
```

Expected: 5 lần `401`.

- [ ] **Step 3: Lần thứ 6**

```bash
curl -i -X POST https://loyalty.ecom-bill.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"identifier":"khach1@gmail.com","password":"khach1234"}'
```

Expected: `HTTP/2 423` + header `retry-after: 900` + body chứa "tạm khoá 15 phút".

- [ ] **Step 4: Verify log không có row 'locked'**

```bash
docker exec loyalty-postgres-prod psql -U loyalty -d loyalty -c \
  "SELECT failure_reason, COUNT(*) FROM login_log GROUP BY failure_reason;"
```

Expected: chỉ có `wrong_password`, KHÔNG có `locked`.

- [ ] **Step 5: TRUNCATE để cleanup**

```bash
docker exec loyalty-postgres-prod psql -U loyalty -d loyalty -c "TRUNCATE login_log;"
```

### Task 5: Commit Phase 7.5

```bash
git add backend/app/services/login_log_service.py backend/tests/unit/test_login_log_service.py backend/app/api/auth.py frontend/src/lib/api.ts frontend/src/app/\(auth\)/login/
git commit -m "feat(auth): login log + lock 5-fail-15min sliding window (HTTP 423 + Retry-After)"
```

---

## Phase 7.6: Admin endpoints — login logs + point adjustments + summary

### Task 1: GET `/admin/login-logs`

**Files:**
- Modify: `backend/app/api/admin.py`

- [ ] **Step 1: Add route**

```python
@router.get("/login-logs", response_model=LoginLogListResponse)
async def list_login_logs(
    identifier: str | None = None,
    success: bool | None = None,
    from_date: datetime | None = Query(default=None, alias="from"),
    to_date: datetime | None = Query(default=None, alias="to"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_super_admin),
):
    base = select(LoginLog).outerjoin(User, User.id == LoginLog.user_id)
    if identifier:
        base = base.where(LoginLog.identifier.ilike(f"%{identifier}%"))
    if success is not None:
        base = base.where(LoginLog.success == success)
    if from_date:
        base = base.where(LoginLog.created_at >= from_date)
    if to_date:
        base = base.where(LoginLog.created_at <= to_date)

    total = await db.scalar(select(func.count()).select_from(base.subquery()))
    stmt = base.order_by(LoginLog.created_at.desc()).limit(limit).offset(offset)
    rows = (await db.execute(stmt)).scalars().all()

    items = []
    for log in rows:
        item = LoginLogResponse.model_validate(log)
        if log.user_id:
            user = await db.get(User, log.user_id)
            item.user_email = user.email if user else None
        items.append(item)
    return LoginLogListResponse(items=items, total=total or 0, limit=limit, offset=offset)
```

### Task 2: GET `/admin/point-adjustments`

- [ ] **Step 1: Add schema**

Trong `schemas/admin.py`:

```python
class PointAdjustmentResponse(BaseModel):
    id: int
    user_id: int
    user_email: str | None
    partner_id: int
    partner_name: str | None
    actor_user_id: int | None
    actor_email: str | None
    delta: int
    balance_after: int
    description: str | None
    created_at: datetime


class PointAdjustmentListResponse(BaseModel):
    items: list[PointAdjustmentResponse]
    total: int
    limit: int
    offset: int
```

- [ ] **Step 2: Add route**

```python
@router.get("/point-adjustments", response_model=PointAdjustmentListResponse)
async def list_point_adjustments(
    user_id: int | None = None,
    partner_id: int | None = None,
    actor_user_id: int | None = None,
    from_date: datetime | None = Query(default=None, alias="from"),
    to_date: datetime | None = Query(default=None, alias="to"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_super_admin),
):
    UserSubject = aliased(User)
    UserActor = aliased(User)
    stmt = (
        select(PointLedger, UserSubject.email.label("subj_email"),
               UserActor.email.label("actor_email"), Partner.name.label("p_name"))
        .join(UserSubject, UserSubject.id == PointLedger.user_id)
        .outerjoin(UserActor, UserActor.id == PointLedger.actor_user_id)
        .outerjoin(Partner, Partner.id == PointLedger.partner_id)
        .where(PointLedger.reason == "adjust")
    )
    if user_id:
        stmt = stmt.where(PointLedger.user_id == user_id)
    if partner_id:
        stmt = stmt.where(PointLedger.partner_id == partner_id)
    if actor_user_id:
        stmt = stmt.where(PointLedger.actor_user_id == actor_user_id)
    if from_date:
        stmt = stmt.where(PointLedger.created_at >= from_date)
    if to_date:
        stmt = stmt.where(PointLedger.created_at <= to_date)

    total = await db.scalar(
        select(func.count()).select_from(stmt.subquery())
    )
    stmt = stmt.order_by(PointLedger.created_at.desc()).limit(limit).offset(offset)
    rows = (await db.execute(stmt)).all()
    items = [
        PointAdjustmentResponse(
            id=r.PointLedger.id, user_id=r.PointLedger.user_id, user_email=r.subj_email,
            partner_id=r.PointLedger.partner_id, partner_name=r.p_name,
            actor_user_id=r.PointLedger.actor_user_id, actor_email=r.actor_email,
            delta=r.PointLedger.delta, balance_after=r.PointLedger.balance_after,
            description=r.PointLedger.description, created_at=r.PointLedger.created_at,
        )
        for r in rows
    ]
    return PointAdjustmentListResponse(items=items, total=total or 0, limit=limit, offset=offset)
```

### Task 3: GET `/admin/points-summary`

- [ ] **Step 1: Add schema**

```python
class PartnerEarnedItem(BaseModel):
    partner_id: int
    name: str
    total_earned: int


class PointsSummaryResponse(BaseModel):
    total_circulating: int
    total_earned: int
    total_redeemed: int
    total_adjusted: int
    by_partner: list[PartnerEarnedItem]
```

- [ ] **Step 2: Add route**

```python
@router.get("/points-summary", response_model=PointsSummaryResponse)
async def points_summary(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_super_admin),
):
    total_circulating = await db.scalar(
        select(func.coalesce(func.sum(User.points_balance), 0)).where(User.is_active.is_(True))
    )
    total_earned = await db.scalar(
        select(func.coalesce(func.sum(PointLedger.delta), 0))
        .where(PointLedger.reason == "earn", PointLedger.delta > 0)
    )
    total_redeemed_neg = await db.scalar(
        select(func.coalesce(func.sum(PointLedger.delta), 0))
        .where(PointLedger.reason == "redeem", PointLedger.delta < 0)
    )
    total_redeemed = -(total_redeemed_neg or 0)
    total_adjusted = await db.scalar(
        select(func.coalesce(func.sum(PointLedger.delta), 0))
        .where(PointLedger.reason == "adjust")
    ) or 0

    # by_partner: tổng điểm EARN per partner.
    # KHÔNG cần "partner_id IS NOT NULL" vì point_ledger.partner_id NOT NULL (verify models/point_ledger.py:40-42).
    # Pattern: filter EARN ở ON clause của LEFT JOIN để partner KHÔNG có EARN nào vẫn hiện 0 (chứ không bị WHERE đẩy ra).
    by_partner_rows = (await db.execute(
        select(
            Partner.id.label("pid"),
            Partner.name.label("name"),
            func.coalesce(func.sum(PointLedger.delta), 0).label("total"),
        )
        .outerjoin(
            PointLedger,
            and_(
                PointLedger.partner_id == Partner.id,
                PointLedger.reason == "earn",
                PointLedger.delta > 0,
            ),
        )
        .group_by(Partner.id, Partner.name)
        .order_by(Partner.id)
    )).all()
    by_partner = [
        PartnerEarnedItem(partner_id=r.pid, name=r.name, total_earned=int(r.total))
        for r in by_partner_rows
    ]
    return PointsSummaryResponse(
        total_circulating=int(total_circulating or 0),
        total_earned=int(total_earned or 0),
        total_redeemed=int(total_redeemed),
        total_adjusted=int(total_adjusted),
        by_partner=by_partner,
    )
```

### Task 4: Update existing `/admin/stats` thêm `total_points_circulating`

- [ ] **Step 1: Find current stats endpoint + response schema**

```bash
grep -n "/stats\|PlatformStatsResponse" backend/app/api/admin.py
grep -rn "PlatformStatsResponse" backend/app/schemas/
```

> Verify tên schema thực tế (có thể là `PlatformStatsResponse` chứ không phải `AdminStatsResponse`). Dùng tên đúng cho Step 2.

- [ ] **Step 2: BE — Thêm field vào response model + compute**

Trong schema response (vd `PlatformStatsResponse`) thêm `total_points_circulating: int`. Trong handler thêm:

```python
total_points = await db.scalar(
    select(func.coalesce(func.sum(User.points_balance), 0))
    .where(User.is_active.is_(True))
)
# include trong response
```

- [ ] **Step 3: FE — Đồng bộ TypeScript type**

Tìm + sửa type tương ứng:

```bash
grep -rn "PlatformStats\|total_users\|total_partners" frontend/src/lib/ frontend/src/app/\(admin\)/
```

Thêm field `total_points_circulating: number` vào type ở `frontend/src/lib/api.ts` (hoặc `lib/api-admin.ts` nếu có) + render trong `(admin)/admin/page.tsx` dashboard card "Tổng điểm lưu hành" để FE không miss thay đổi.

### Task 5: ADJUST endpoint actor_user_id binding (out-of-MVP — skip)

> **Decision (2026-04-26)**: Hiện tại MVP **CHƯA có** endpoint admin ADJUST điểm. `LedgerReason.ADJUST` enum đã có (`models/point_ledger.py:12`) nhưng không route nào INSERT entry với reason này. Nếu sau này thêm endpoint `POST /admin/users/{id}/adjust-points`, INSERT ledger phải set `actor_user_id=admin.id` để `/admin/point-adjustments` log hiển thị "ai điều chỉnh". MVP hiện tại chỉ list ledger entries có `reason='adjust'` — list trống cũng OK (column hiển thị "-" cho actor).
>
> **Action**: Task này NO-OP. Skip qua Task 6.

### Task 6: FE — `useAdminLogs` + `useSystemPoints` hooks

**Files:**
- Create: `frontend/src/lib/hooks/useAdminLogs.ts`
- Create: `frontend/src/lib/hooks/useSystemPoints.ts`

- [ ] **Step 1: Implement (xem pattern useRedemptions ở Phase 7.4 Task 4)**

Hook signature:

```ts
useAdminLoginLogs(filters: {identifier?, success?, from?, to?, limit?, offset?})
useAdminPointAdjustments(filters: {user_id?, partner_id?, ...})
useSystemPoints()  // không filter
```

### Task 7: FE — `/admin/logs/page.tsx` (2 tabs)

**Files:**
- Create: `frontend/src/app/(admin)/admin/logs/page.tsx`

- [ ] **Step 1: Implement** với 2 Tabs (Login / Point Adjustments), mỗi tab dùng `<Table>` của shadcn/ui hiển thị 8 cột tương ứng. Filter form ở trên (input identifier + select success + date range) với debounce 500ms.

### Task 8: FE — `/admin/system-points/page.tsx`

**Files:**
- Create: `frontend/src/app/(admin)/admin/system-points/page.tsx`

- [ ] **Step 1: Implement** với 4 stat cards (circulating / earned / redeemed / adjusted) + 1 table breakdown by partner.

### Task 9: Smoke test E2E

- [ ] **Step 1: Đăng nhập admin@loyalty.vn → vào /admin/logs → verify 2 tabs hoạt động + filter chạy.**

- [ ] **Step 2: /admin/system-points** → verify số liệu hợp lý:
  ```
  total_circulating ≈ total_earned - total_redeemed + total_adjusted
  ```

### Task 10: Commit Phase 7.6

```bash
git add backend/app/api/admin.py backend/app/schemas/admin.py frontend/src/lib/hooks/useAdminLogs.ts frontend/src/lib/hooks/useSystemPoints.ts frontend/src/app/\(admin\)/admin/logs/ frontend/src/app/\(admin\)/admin/system-points/
git commit -m "feat(admin): login logs + point adjustments + points summary endpoints + UI"
```

---

## Phase 7.7: Partner staff CRUD + `require_staff_in_partner` dep

### Task 1: Tạo `require_staff_in_partner` dep

**Files:**
- Modify: `backend/app/core/deps.py`

- [ ] **Step 1: Thêm dep**

```python
async def require_staff_in_partner(
    user: User = Depends(get_current_user),
    partner_id: int = Depends(get_partner_id),
    db: AsyncSession = Depends(get_db),
):
    """Yêu cầu user là owner OR active staff của partner. Dùng cho /partner/* + POS."""
    from app.models.partner import Partner
    from app.models.partner_staff import PartnerStaff

    partner = await db.get(Partner, partner_id)
    if partner is None:
        raise HTTPException(404, "Partner not found")

    if partner.owner_user_id == user.id:
        return partner

    staff_row = await db.scalar(
        select(PartnerStaff).where(
            PartnerStaff.partner_id == partner_id,
            PartnerStaff.user_id == user.id,
            PartnerStaff.is_active.is_(True),
        )
    )
    if staff_row is None:
        raise HTTPException(403, "Bạn không có quyền truy cập shop này.")
    return partner
```

### Task 2: `StaffService` (TDD)

**Files:**
- Create: `backend/app/services/staff_service.py`
- Create: `backend/tests/unit/test_staff_service.py`

- [ ] **Step 1: Failing test add_staff guard**

> **Note**: `add_staff` **TẠO MỚI** user từ email/phone/password (không nhận `target_user`). Pre-check chỉ guard trường hợp email đã tồn tại với role khác `regular` (super_admin/admin) — block tái sử dụng. UNIQUE constraint trên User + UNIQUE(partner_id,user_id) trên PartnerStaff bắt race-safe.

```python
@pytest.mark.asyncio
async def test_add_staff_rejects_existing_super_admin_email(db_session, partner_factory, user_factory):
    partner = await partner_factory()
    # User super_admin đã tồn tại
    await user_factory(email="admin@x.com", system_role="super_admin")
    svc = StaffService(db_session)
    with pytest.raises(InvalidStaffError, match="không hợp lệ"):
        await svc.add_staff(
            partner_id=partner.id,
            email="admin@x.com", phone=None, full_name="Test",
            password="abc12345",
        )


@pytest.mark.asyncio
async def test_add_staff_rejects_duplicate_email(db_session, partner_factory, user_factory):
    """User regular đã tồn tại với email này → INSERT new User vi phạm UNIQUE."""
    partner = await partner_factory()
    await user_factory(email="dup@x.com", system_role="regular")
    svc = StaffService(db_session)
    with pytest.raises(InvalidStaffError, match="đã tồn tại"):
        await svc.add_staff(
            partner_id=partner.id,
            email="dup@x.com", phone=None, full_name="x",
            password="abc12345",
        )


@pytest.mark.asyncio
async def test_add_staff_success_creates_user_and_link(db_session, partner_factory):
    partner = await partner_factory()
    svc = StaffService(db_session)
    staff = await svc.add_staff(
        partner_id=partner.id,
        email="new@x.com", phone="0900000001", full_name="Mới",
        password="abc12345",
    )
    assert staff.partner_id == partner.id
    assert staff.is_active is True
```

- [ ] **Step 2: Implement service**

```python
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, gen_temp_password
from app.models.partner_staff import PartnerStaff
from app.models.user import User


class InvalidStaffError(Exception):
    pass


class StaffService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_staff(self, partner_id: int, *, is_active: bool | None = None) -> list[PartnerStaff]:
        stmt = select(PartnerStaff).where(PartnerStaff.partner_id == partner_id)
        if is_active is not None:
            stmt = stmt.where(PartnerStaff.is_active == is_active)
        return list((await self.db.scalars(stmt.order_by(PartnerStaff.id))).all())

    async def add_staff(
        self,
        *,
        partner_id: int,
        email: str | None,
        phone: str | None,
        full_name: str,
        password: str,
    ) -> PartnerStaff:
        # Pre-check: chỉ cho regular user (UX hint, race-safe ở UNIQUE)
        if email:
            existing = await self.db.scalar(select(User).where(User.email == email))
            if existing and existing.system_role != "regular":
                raise InvalidStaffError("Email này không hợp lệ làm nhân viên.")

        # Atomic: tạo user + insert partner_staff trong cùng transaction
        try:
            new_user = User(
                email=email, phone=phone, full_name=full_name,
                password_hash=hash_password(password),
                system_role="regular", is_active=True,
            )
            self.db.add(new_user)
            await self.db.flush()
            staff = PartnerStaff(
                partner_id=partner_id, user_id=new_user.id, is_active=True
            )
            self.db.add(staff)
            await self.db.flush()
            return staff
        except IntegrityError as e:
            await self.db.rollback()
            # UNIQUE(user_id) hoặc UNIQUE email/phone bị vi phạm
            raise InvalidStaffError("Tài khoản đã tồn tại hoặc đã thuộc shop khác.") from e

    async def toggle_active(self, partner_id: int, user_id: int, is_active: bool) -> PartnerStaff:
        staff = await self.db.scalar(
            select(PartnerStaff).where(
                PartnerStaff.partner_id == partner_id,
                PartnerStaff.user_id == user_id,
            )
        )
        if staff is None:
            raise InvalidStaffError("Không tìm thấy nhân viên.")
        staff.is_active = is_active
        await self.db.flush()
        return staff

    async def reset_staff_password(
        self, partner_id: int, user_id: int
    ) -> tuple[str, str | None]:
        """Return (temp_password, target_email)."""
        staff = await self.db.scalar(
            select(PartnerStaff).where(
                PartnerStaff.partner_id == partner_id,
                PartnerStaff.user_id == user_id,
            )
        )
        if staff is None:
            raise InvalidStaffError("Không tìm thấy nhân viên.")
        user = await self.db.get(User, user_id)
        temp_pwd = gen_temp_password(12)
        user.password_hash = hash_password(temp_pwd)
        await self.db.flush()
        return temp_pwd, user.email
```

> **Helper note**: `gen_temp_password` chưa có ở `core/security.py`. Trước khi import, tạo nó:
>
> ```python
> # backend/app/core/security.py
> import secrets
> import string
>
> def gen_temp_password(length: int = 12) -> str:
>     """Sinh mật khẩu ngẫu nhiên dễ đọc (chữ + số, không ký tự đặc biệt)."""
>     alphabet = string.ascii_letters + string.digits
>     return "".join(secrets.choice(alphabet) for _ in range(length))
> ```
>
> Helper này có thể tái sử dụng cho `api/admin.py` reset (thay `_generate_temp_password` private hiện tại) — refactor optional, không bắt buộc trong MVP.

- [ ] **Step 3: Run tests → PASS**

### Task 3: Routes — GET `/partner/staff`

**Files:**
- Modify: `backend/app/api/partner.py` (hoặc tạo `app/api/partner_staff_routes.py`)

- [ ] **Step 1: Add route**

```python
@partner_router.get("/staff", response_model=StaffListResponse)
async def list_partner_staff(
    is_active_filter: str = Query(default="all", alias="is_active", regex="^(true|false|all)$"),
    db: AsyncSession = Depends(get_db),
    partner = Depends(require_owner_in_partner),
):
    is_active = None if is_active_filter == "all" else (is_active_filter == "true")
    svc = StaffService(db)
    rows = await svc.list_staff(partner.id, is_active=is_active)
    items = []
    for s in rows:
        u = await db.get(User, s.user_id)
        items.append(StaffResponse(
            id=s.id, user_id=s.user_id,
            email=u.email if u else None, phone=u.phone if u else None,
            full_name=u.full_name if u else None,
            is_active=s.is_active, created_at=s.created_at,
        ))
    return StaffListResponse(items=items, total=len(items))
```

### Task 4: POST `/partner/staff`

```python
@partner_router.post("/staff", response_model=StaffResponse, status_code=201)
async def create_partner_staff(
    body: StaffCreateRequest,
    db: AsyncSession = Depends(get_db),
    partner = Depends(require_owner_in_partner),
):
    if not body.email and not body.phone:
        raise HTTPException(400, "Phải có email hoặc phone.")
    svc = StaffService(db)
    try:
        staff = await svc.add_staff(
            partner_id=partner.id, email=body.email, phone=body.phone,
            full_name=body.full_name, password=body.password,
        )
        await db.commit()
    except InvalidStaffError as e:
        # Service đã rollback ở IntegrityError path (xem add_staff)
        raise HTTPException(409, str(e))
    user = await db.get(User, staff.user_id)
    return StaffResponse(
        id=staff.id, user_id=staff.user_id, email=user.email,
        phone=user.phone, full_name=user.full_name,
        is_active=staff.is_active, created_at=staff.created_at,
    )
```

### Task 5: PATCH `/partner/staff/{user_id}`

```python
@partner_router.patch("/staff/{user_id}", response_model=StaffResponse)
async def patch_partner_staff(
    user_id: int,
    body: StaffPatchRequest,
    db: AsyncSession = Depends(get_db),
    partner = Depends(require_owner_in_partner),
):
    svc = StaffService(db)
    try:
        staff = await svc.toggle_active(partner.id, user_id, body.is_active)
    except InvalidStaffError as e:
        raise HTTPException(404, str(e))
    await db.commit()
    user = await db.get(User, staff.user_id)
    return StaffResponse(
        id=staff.id, user_id=staff.user_id, email=user.email,
        phone=user.phone, full_name=user.full_name,
        is_active=staff.is_active, created_at=staff.created_at,
    )
```

### Task 6: POST `/partner/staff/{user_id}/reset-password`

```python
@partner_router.post("/staff/{user_id}/reset-password", response_model=StaffResetResponse)
async def reset_partner_staff_password(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    partner = Depends(require_owner_in_partner),
):
    svc = StaffService(db)
    try:
        temp_pwd, target_email = await svc.reset_staff_password(partner.id, user_id)
    except InvalidStaffError as e:
        raise HTTPException(404, str(e))
    await db.commit()

    email_sent = False
    if target_email:
        try:
            await EmailService().send_email(
                to=target_email,
                subject="[Loyalty] Mật khẩu mới (do quản lý shop reset)",
                body=(
                    f"Mật khẩu tạm thời: {temp_pwd}\n"
                    f"Vui lòng đăng nhập và đổi mật khẩu ngay."
                ),
            )
            email_sent = True
        except EmailDeliveryError:
            logger.warning("staff.reset.SMTP_FAIL", extra={"user_id": user_id})

    return StaffResetResponse(
        email_sent=email_sent, temp_password=temp_pwd,
        message="Đã reset mật khẩu." + ("" if email_sent else " (Gửi email lỗi, vui lòng cấp tay.)"),
    )
```

### Task 7: Update POS routes dùng `require_staff_in_partner`

- [ ] **Step 1: Tìm POS routes hiện tại**

```bash
grep -rn "require_owner_in_partner\|require_staff_in_partner" backend/app/api/
```

- [ ] **Step 2: Đổi POS routes** (`/partner/transactions/qr`, `/partner/redemptions/use`, ...) từ `require_owner_in_partner` sang `require_staff_in_partner` để staff cũng dùng được. Owner-only routes (CRUD reward/staff/settings) giữ `require_owner_in_partner`.

### Task 8: FE — clean stale + add new staff API

**Files:**
- Modify: `frontend/src/lib/api-partner.ts`

> **BREAKING CHANGE — báo cho consumer**: `staffApi.list()` đổi return type từ `Staff[]` (array) sang `{items: Staff[]; total: number}` (object). Mọi page/component đang `.map(s => ...)` trên `staffApi.list()` phải cập nhật sang `data.items.map(...)`. Sửa Phase 7.7 Task 10 page consumer luôn.

- [ ] **Step 1: Tìm staffApi hiện tại**

```bash
grep -n "staffApi" frontend/src/lib/api-partner.ts
```

- [ ] **Step 2: Replace staffApi block**

```ts
export const staffApi = {
  list: async (params?: {is_active?: "true" | "false" | "all"}) => {
    const res = await api.get("/partner/staff", {params});
    return res.data as {items: Staff[]; total: number};
  },
  add: async (body: {email?: string; phone?: string; full_name: string; password: string}) => {
    const res = await api.post("/partner/staff", body);
    return res.data as Staff;
  },
  toggleActive: async (user_id: number, is_active: boolean) => {
    const res = await api.patch(`/partner/staff/${user_id}`, {is_active});
    return res.data as Staff;
  },
  resetPassword: async (user_id: number) => {
    const res = await api.post(`/partner/staff/${user_id}/reset-password`);
    return res.data as {email_sent: boolean; temp_password: string; message: string};
  },
};
```

XOÁ `updateRole` và `remove` cũ.

### Task 9: FE — `use-partner.ts` clean stale + add new hooks

**Files:**
- Modify: `frontend/src/lib/hooks/use-partner.ts`

- [ ] **Step 1: XOÁ `useUpdateStaffRole`, `useRemoveStaff`**

- [ ] **Step 2: Thêm new hooks**

```ts
export function useToggleStaffActive() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({user_id, is_active}: {user_id: number; is_active: boolean}) =>
      staffApi.toggleActive(user_id, is_active),
    onSuccess: () => qc.invalidateQueries({queryKey: ["partner-staff"]}),
  });
}

export function useResetStaffPassword() {
  return useMutation({
    mutationFn: (user_id: number) => staffApi.resetPassword(user_id),
  });
}
```

### Task 10: FE — `/partner/staff/page.tsx` (REWRITE — file đã tồn tại)

**Files:**
- Modify: `frontend/src/app/(partner)/partner/staff/page.tsx` (file CŨ đang dùng `useUpdateStaffRole` + `useRemoveStaff` + array shape — phải rewrite hoàn toàn)

> **CRITICAL**: File này đã tồn tại từ Phase 3 (partner-staff version cũ với role + remove). Sau khi xoá `useUpdateStaffRole` + `useRemoveStaff` ở Task 9 và đổi shape `staffApi.list` ở Task 8 → page CŨ sẽ break compile. Phải rewrite, không tạo file mới.

- [ ] **Step 1: Rewrite hoàn toàn page** với:
  - Bảng list staff đọc từ `data.items` (object shape mới)
  - Cột: tên / email / phone / trạng thái / ngày tạo / actions
  - Button "Thêm nhân viên" → mở Dialog form (email, phone, full_name, password)
  - Mỗi row có 2 button: "Reset mật khẩu" (show modal chứa `temporary_password` sau khi gọi API), "Tắt"/"Bật" (toggle)
  - Filter Select `is_active` (Tất cả / Đang làm / Đã nghỉ)
  - **KHÔNG** import `useUpdateStaffRole` / `useRemoveStaff` (đã xoá ở Task 9)

### Task 11: Smoke test full CRUD

- [ ] **Step 1: Login owner Cafe Cộng**

- [ ] **Step 2: Tạo staff mới**: vào `/partner/staff` → thêm `staffnew@cafe.vn / 0900000099 / Tên Mới / abc12345`. Expect: list xuất hiện row mới.

- [ ] **Step 3: Login staff vừa tạo**: trong tab ẩn danh → đăng nhập với email + password vừa nhập. Expect: vào được staff dashboard, scan QR thử OK.

- [ ] **Step 4: Reset password**: owner → click "Reset mật khẩu" cho staff → modal hiện temp_password + check email staffnew@cafe.vn nhận được mail.

- [ ] **Step 5: Disable**: owner → toggle is_active=false. Staff đăng nhập lần kế tiếp gọi API → 403.

- [ ] **Step 6: Re-enable**: toggle lại true → staff lại dùng được.

- [ ] **Step 7: Add super_admin → expect 409**:

```bash
curl -X POST https://loyalty.ecom-bill.com/partner/staff \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OWNER_TOKEN" \
  -H "X-Partner-Id: 1" \
  -d '{"email":"admin@loyalty.vn","full_name":"x","password":"abc12345"}'
```

Expected: 409.

### Task 12: Commit Phase 7.7

```bash
git add backend/app/core/deps.py backend/app/services/staff_service.py backend/tests/unit/test_staff_service.py backend/app/api/partner.py backend/app/schemas/partner_staff.py frontend/src/lib/api-partner.ts frontend/src/lib/hooks/use-partner.ts frontend/src/app/\(partner\)/partner/staff/page.tsx
git commit -m "feat(partner): staff CRUD (add/reset-pwd/toggle is_active) + require_staff_in_partner dep"
```

---

## Phase 7.8: Smoke test E2E + final commit

### Task 1: Run full acceptance checklist

Chạy 18 items từ spec section 6 trong order:

- [ ] Pre: TRUNCATE login_log
- [ ] Forgot password gửi email thật
- [ ] Login sai 5 lần → lần 6 trả 423 + Retry-After
- [ ] FE login form show countdown
- [ ] Đăng nhập đúng → login_log success=True
- [ ] Đăng nhập sai → login_log success=False, reason=wrong_password
- [ ] /member/qr render QR `"5"` không call BE
- [ ] Staff scan QR → POST /partner/transactions/qr 200
- [ ] /users/me/redemptions?status=pending trả pending (lowercase)
- [ ] /users/me/redemptions/{id} trả redemption_code
- [ ] Owner tạo staff mới → staff login OK
- [ ] Owner reset pwd staff → staff nhận email
- [ ] Owner disable staff → staff API 403
- [ ] Owner enable lại → staff dùng OK
- [ ] Tạo super_admin thành staff → 409
- [ ] Tạo owner shop khác thành staff → 409
- [ ] Admin /admin/logs filter success=false thấy attempts
- [ ] Admin tạo manual ADJUST → ledger có actor_user_id
- [ ] Admin /admin/logs tab adjustments thấy actor email
- [ ] Admin /admin/system-points circulating ≈ earned - redeemed + adjusted

### Task 2: Document deviations (nếu có)

- [ ] Nếu test nào fail / spec phải điều chỉnh → ghi note vào `docs/superpowers/specs/2026-04-26-mvp-features-completion-design.md` section 8 Changelog v3.

### Task 3: Final commit

```bash
git add docs/
git commit -m "docs(spec): MVP features completion smoke test passed (Phase 7.8)"
```

### Task 4: Run code-reviewer opus cho toàn bộ Phase 7

```bash
# Dispatch superpowers:code-reviewer với model opus, scope = phạm vi 8 phases.
```

Fix Critical/Important phát hiện được, commit fix riêng.

---

## Self-Review (post-write checklist)

- [x] **Spec coverage**: mỗi mục trong spec section 2.1-2.8 + invariants section 4 → có task tương ứng (2.1 SMTP→7.2, 2.2 QR→7.3, 2.3 schema→7.1, 2.4 lock→7.5, 2.5 staff→7.7, 2.6 voucher→7.4, 2.7 admin→7.6, 2.8 SQL definitions→7.6 Task 3).
- [x] **Placeholder scan**: không có "TBD/TODO/implement later" trong steps.
- [x] **Type consistency**: `StaffResponse` dùng cùng tên field xuyên suốt (id, user_id, email, phone, full_name, is_active, created_at). `PointAdjustmentResponse` field nhất quán giữa BE schema và FE hook.
- [x] **Spec Critical fixes mapping**: C1 (deps mismatch) → 7.7 Task 1. C2 (super_admin guard) → 7.7 Task 2 test. C3 (lock self-perpetuate) → 7.5 Task 2 ("KHÔNG ghi log row khi reject"). C4 (race) → 7.7 Task 4 IntegrityError catch. C5 (QR signature change) → 7.3 Task 5+6. C6 (FE staff stale) → 7.7 Task 8+9.
- [x] **Important fixes**: I1 (actor_user_id) → 7.1 Task 4. I2 (limit+offset) → all endpoints. I3 (SMTP timeout) → 7.2 Task 3 `asyncio.wait_for`. I4 (423+Retry-After) → 7.5 Task 2. I5 (require_staff_in_partner) → 7.7 Task 1+7. I6 (asymmetric leak) → 7.2 Task 5+ 7.7 Task 6. I7 (drop /qr) → 7.3 Task 2. I8 (keep shop_token) → 7.3 Task 1. I9 (default no filter) → 7.4 Task 1. I10 (SQL definitions) → 7.6 Task 3.

---

## Execution choice

**Plan complete and saved to `docs/superpowers/plans/2026-04-26-mvp-features-completion.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — Dispatch fresh subagent per phase (Sonnet model), review giữa mỗi phase, batch commit + tag.

**2. Inline Execution** — Execute tasks trong session này với checkpoint sau mỗi phase.

**Chọn approach nào?**
