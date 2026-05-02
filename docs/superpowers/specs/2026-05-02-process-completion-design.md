# Hoàn thiện 8 quy trình nghiệp vụ (Mục 2.3.1) — Design

**Ngày:** 2026-05-02
**Status:** Đã chốt scope. Chờ user duyệt spec trước khi viết plan.
**Mục tiêu:** Đưa code hiện tại khớp với 8 quy trình nghiệp vụ trong báo cáo (Mục 2.3.1, bản cập nhật 2026-05-02 giữ phân hạng thành viên ở QT3).

## Bối cảnh

Báo cáo đồ án mục 2.3.1 mô tả 8 quy trình nghiệp vụ chính. Audit code (commit `5ecb798`, 2026-05-02) cho thấy:

- **Đầy đủ:** QT3 (cấu hình point rule + tier + reward), QT6 (sử dụng voucher tại quầy).
- **Gần đủ — thiếu chi tiết:** QT1 (thiếu phone bắt buộc + bắt buộc đổi mật khẩu sau temp), QT2 (thiếu giấy phép + đồng ý điều khoản + reason approve/reject), QT4 (ledger EARN không lưu nhân viên + QR scan lần đầu fail), QT5 (không kiểm `valid_until` lúc đổi quà), QT8 (không lưu lý do khoá + không có audit trail).
- **Chưa làm:** QT7 (phát hành voucher có giới hạn số lượng) — đã từng cố ý cắt khỏi MVP, nay quyết định làm lại theo phương án nhỏ.

Spec này lấp toàn bộ các gap trên.

## Phạm vi

### IN SCOPE

| # | Quy trình | Gap |
|---|---|---|
| QT1 | Đăng ký + xác thực khách hàng | Phone bắt buộc, must_change_password sau temp password |
| QT2 | Đăng ký đối tác + phê duyệt | Upload giấy phép, đồng ý điều khoản, persist reason approve/reject |
| QT4 | Tích điểm tại quầy | Ghi nhân viên thực hiện vào ledger, auto-enroll khi quét QR lần đầu |
| QT5 | Đổi quà | Kiểm `valid_until` lúc đổi |
| QT7 | Phát hành voucher giới hạn số lượng | Mở rộng `Reward` thành "voucher miễn phí" với `valid_from` + claim atomic |
| QT8 | Giám sát + xử lý vi phạm | Bảng `audit_logs` + lý do khoá user/partner + endpoint admin xem |

### OUT OF SCOPE

- T&C versioning system động (FE render markdown tĩnh; chỉ lưu `terms_version` string trên Partner để truy vết).
- Generic audit cho mọi thay đổi data (chỉ log các action admin: lock/unlock user, approve/suspend partner). Các thay đổi khác (POS earn, redeem) đã có ledger riêng.
- Logic notification riêng cho admin khi có partner pending (đã có `audit-feed` query trên-demand).
- Email gửi cho user khi bị admin khoá (có thể thêm sau, không bắt buộc theo spec).

## QT3 — Đã đủ, không thay đổi

PointRule, Tier per-partner, Reward CRUD đã đầy đủ. Spec 2.3.1 v2 (giữ phân hạng) khớp 100% code hiện tại. Cần đảm bảo Chương 1 (Phạm vi) bỏ "Hệ thống phân hạng thành viên" khỏi danh sách out-of-scope (việc trên báo cáo, không phải code).

---

## QT1 — Auth completion

### Schema

**`users` table** thêm 1 cột:

```python
must_change_password: Mapped[bool] = mapped_column(
    Boolean, default=False, nullable=False, server_default="false"
)
```

Alembic migration: `ADD COLUMN must_change_password BOOLEAN NOT NULL DEFAULT FALSE`.

### Schema thay đổi

**`RegisterRequest`** (`schemas/auth.py`):

```python
class RegisterRequest(BaseModel):
    email: EmailStr
    phone: str = Field(min_length=10, max_length=11)  # NEW: bắt buộc
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=255)
    birthday: date | None = None

    @field_validator("phone")
    @classmethod
    def _normalize_phone(cls, v: str) -> str:
        # Reuse existing normalize_phone from app.core.phone
        ...
```

### Service

**`AuthService.register`**: kiểm tra trùng phone trước khi insert; bắt `IntegrityError` cả phone lẫn email → 409.

**`AuthService.reset_password_send_temp`**: sau khi set `password_hash = bcrypt(temp)`, set `user.must_change_password = True`.

**`AuthService.change_password`**: sau khi set new hash, set `user.must_change_password = False`.

### Dependency

**`get_current_user`** (`core/deps.py`) thêm logic: sau khi load user, nếu `must_change_password=True` → raise `HTTPException(423, detail="password_change_required")`.

**Tách dependency riêng** `get_current_user_unrestricted` (chỉ load user, KHÔNG kiểm `must_change_password`) cho 2 endpoint:
- `GET /auth/me`
- `PATCH /auth/me/password`

`POST /auth/login` và `POST /auth/refresh` **KHÔNG cần whitelist** vì cả hai không gọi `get_current_user` (login dùng identifier+password, refresh decode JWT trực tiếp).

`get_optional_user` (dùng cho preview/public route nếu có) — KHÔNG sửa, để route public không block oan. User `must_change_password=True` truy cập route public → treat as anonymous (an toàn cho read-only preview).

Mọi route dùng `get_current_user` (admin, partner, member endpoints khác) — bị block 423 cho tới khi user đổi mật khẩu.

**Super_admin SKIP**: trong `AuthService.reset_password_send_temp` và `admin.reset_user_password`, KHÔNG set `must_change_password=True` nếu `user.system_role == "super_admin"`. Tránh khoá hệ thống nếu super_admin cuối cùng quên mật khẩu rồi reset → bị 423 ở mọi route admin → không vào lại được. Super_admin tự đổi qua endpoint trực tiếp `/auth/me/password`.

**FE error branching (lưu ý)**: backend đã có 423 khác cho "tài khoản tạm khoá do đăng nhập sai" (`/auth/login` failure threshold). FE phải branch theo `detail`:
- `detail == "password_change_required"` → redirect `/auth/change-password`.
- `detail` chứa "tạm khoá" + có header `Retry-After` → hiển thị toast "thử lại sau X phút".

### Frontend

- Login page: catch 423 trên login (sau redirect /me) hoặc bất kỳ API call nào → redirect sang `/auth/change-password` với label "Bạn cần đổi mật khẩu trước khi tiếp tục".
- Form đổi mật khẩu hiện có (`PATCH /auth/me/password`) — không cần thay đổi backend.
- Trang đăng ký: thêm field SĐT trong form, validate VN phone format.

### Test

- Unit: register với phone trùng → 409 (cả prefix và full match).
- Integration: forgot-password flow → login với temp → call API khác → 423; call `/auth/me/password` → 200; sau đó call API khác → 200.
- FE manual: login bằng temp password sau forgot-password → bị redirect sang đổi mật khẩu.

---

## QT2 — Partner registration completion

### Schema

**`partners` table** thêm 6 cột:

```python
business_license_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
terms_accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
terms_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
last_status_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
last_status_changed_by: Mapped[int | None] = mapped_column(
    ForeignKey("users.id", ondelete="SET NULL"), nullable=True
)
last_status_changed_at: Mapped[datetime | None] = mapped_column(
    DateTime(timezone=True), nullable=True
)
```

Backfill cho row cũ: NULL hết — chấp nhận, partner cũ chưa từng accept terms theo flow mới.

### Schema thay đổi

**`PartnerCreateRequest`**:

```python
class PartnerCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    # ... fields cũ giữ nguyên ...
    business_license_url: str = Field(min_length=1, max_length=500)  # NEW required
    accept_terms: bool  # NEW required
    terms_version: str = Field(min_length=1, max_length=20)  # NEW required (ví dụ "v1.0")

    @field_validator("accept_terms")
    @classmethod
    def _must_accept(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Phải đồng ý điều khoản hợp đồng dịch vụ")
        return v
```

### Service

**`PartnerService.create_partner`** nhận thêm `terms_version` từ request, set `partner.terms_accepted_at = datetime.now(UTC)`, `partner.terms_version = request.terms_version`, `partner.business_license_url = request.business_license_url`.

**`PartnerService.approve_partner(partner_id, *, reason: str | None, actor_user_id: int)`** — nhận thêm 2 param. Set 3 cột `last_status_*`.

**`PartnerService.suspend_partner(partner_id, *, reason: str | None, actor_user_id: int)`** — same.

### API

**`POST /admin/partners/{partner_id}/approve`**: pass `body.reason` + `_admin.id` xuống service. Hiện tại đang vứt bỏ `body.reason` — sửa.

**`POST /admin/partners/{partner_id}/suspend`** (đã tồn tại nhưng không nhận body): thêm body `{reason: str | None}`.

### Upload giấy phép

`app/api/uploads.py` hiện chỉ phục vụ logo/banner **sau khi user đã là owner** (`require_owner_in_partner`). Không tái dùng được vì lúc đăng ký partner user chưa là owner.

Endpoint mới `POST /partner/uploads/license` (cùng file `uploads.py`):
- Auth: chỉ cần `get_current_user` (authenticated user, không yêu cầu owner role).
- Whitelist: `.jpg`, `.jpeg`, `.png`, `.webp` (đồng nhất pattern hiện có).
- Max size: 5MB.
- Path: `uploads/licenses/<user_id>/<uuid>.<ext>`.
- Trả `{url: "/api/uploads/licenses/<user_id>/<filename>"}`.
- Rate limit: 10/minute để tránh spam.

Frontend luồng:
1. User authenticate → vào trang `/register/partner`.
2. Chọn file giấy phép → POST `/partner/uploads/license` → lấy URL.
3. Submit form đăng ký với `business_license_url = <url>`.

PDF không hỗ trợ — user scan/chụp giấy phép sang ảnh. Đồng nhất với existing pattern (logo/banner cũng chỉ image).

### T&C content

Trang static FE `/legal/terms` (markdown render) — không lưu trong DB. Phiên bản hiển thị trong UI dưới dạng "Terms v1.0 (cập nhật 2026-05-02)". Thay đổi nội dung → bump `terms_version` trong code FE và backend constant.

Backend constant `app/core/legal.py`:
```python
CURRENT_TERMS_VERSION = "v1.0"
```

Validate `request.terms_version == CURRENT_TERMS_VERSION` trong `create_partner` — nếu không match raise 422 ("Phiên bản điều khoản đã thay đổi, vui lòng đọc lại").

### Frontend

Trang `/register/partner` thêm 2 field:
- File upload giấy phép (preview ảnh sau upload)
- Checkbox "Tôi đồng ý với [Điều khoản dịch vụ]" (link mở `/legal/terms` trong tab mới) — checkbox bắt buộc check.

Trang admin `/admin/partners/{id}/detail` hiển thị:
- Ảnh giấy phép (link mở full-size)
- Thông tin terms (version + accepted_at)
- Nút "Phê duyệt" / "Từ chối" mở dialog nhập reason.
- Lịch sử status (last_status_reason + by + at).

### Test

- Unit: register partner thiếu `accept_terms` hoặc `terms_version` sai → 422.
- Integration: approve_partner with reason → DB cột `last_status_reason` set; query lại thấy.
- FE manual: full flow từ upload giấy phép → submit → admin duyệt với reason → owner login.

---

## QT4 — POS earn completion

**KHÔNG có schema change.** `point_ledger.actor_user_id` đã có sẵn (`models/point_ledger.py`), `LedgerService.log_entry` đã chấp nhận param. Gap nằm ở caller chain — chỉ cần plumb `actor_user_id` từ API layer xuống service rồi vào ledger.

### Service

**`TransactionService.create_manual` / `create_qr_customer` / `_create_transaction_for_membership`**:
- Nhận thêm param `actor_user_id: int` (staff hoặc owner thực hiện POS).
- Truyền xuống `LedgerService.log_entry` cho EARN entry: `actor_user_id=actor_user_id`.

**`api/transactions.py`** routes — pass `current_user.id` qua service. Hiện đã có `Depends(require_staff_in_partner)` nhưng không capture user; thêm `current_user: User = Depends(get_current_user)` rồi pass.

### QR auto-enroll

**`QrService.decode_qr_payload`**:
- Bỏ logic raise `QrUserNotMemberError` khi không có membership.
- Thay bằng: nếu không có membership → tạo membership mới `(partner_id, user_id, current_tier_id=None, lifetime_earned=0)` qua `INSERT ... ON CONFLICT DO NOTHING`, sau đó SELECT FOR UPDATE.
- Trả về `(user, membership)` như cũ.

Hàm `_auto_enroll_membership` ở `transaction_service.py` đã có sẵn — di chuyển sang `QrService` hoặc gọi từ `decode_qr_payload`.

`api/transactions.py:lookup_customer_by_qr` (GET endpoint preview): cũng bỏ check 404 "chưa là thành viên" — trả `is_member=False, lifetime_earned=null` để FE hiển thị khách mới.

### Test

- Unit: `QrService.decode_qr_payload` với user chưa member → tạo mới + return (user, fresh_membership).
- Integration: POS QR scan của user mới → earn 1000đ → query DB thấy membership mới + ledger entry với `actor_user_id` của staff.
- FE manual: POS staff quét QR khách lần đầu → tích điểm thành công, không bị block "khách chưa là thành viên".

---

## QT5 — Reward expiry check

### Service

**`RedemptionService.redeem`** — thêm filter `valid_from`/`valid_until`:

```python
from datetime import date

today = date.today()
reward = await self.db.scalar(
    select(Reward)
    .where(
        Reward.id == reward_id,
        Reward.partner_id == partner_id,
        Reward.is_active.is_(True),
        Reward.deleted_at.is_(None),
        # NEW: kiểm hạn dùng
        ((Reward.valid_from.is_(None)) | (Reward.valid_from <= today)),
        ((Reward.valid_until.is_(None)) | (Reward.valid_until >= today)),
    )
    .with_for_update()
)
```

Reward không match → vẫn raise `ValueError(...)` → 404 (giữ pattern cũ). Frontend hiển thị "Phần thưởng không tồn tại hoặc đã hết hạn" (giữ generic — không leak thông tin chi tiết để tránh enumeration).

`RedemptionService.claim_free` (mới ở QT7) cùng check.

### Frontend

Trang `/users/me/rewards` + `/users/me/partners/{slug}/rewards`: backend đã filter ra rewards out-of-window, FE không cần thay đổi.

### Test

- Unit: `redeem` với reward `valid_until = yesterday` → ValueError "Reward not found".
- Unit: `redeem` với reward `valid_from = tomorrow` → ValueError.
- Unit: `redeem` với reward `valid_until = today` → success (inclusive).

---

## QT7 — Free voucher (option A)

### Schema

**`rewards` table**:
- Relax CheckConstraint: `points_cost > 0` → `points_cost >= 0`.
- Thêm cột `valid_from: Mapped[date | None] = mapped_column(Date, nullable=True)`.

Alembic (chú ý: tên CK thực tế trong DB là **`ck_rewards_ck_rewards_points_cost_positive`** do double-prefix vì model dùng `name="points_cost_positive"` rồi convention `ck_<table>_` prepend tiếp — verified với prod `pg_constraint`):

```python
op.drop_constraint("ck_rewards_ck_rewards_points_cost_positive", "rewards", type_="check")
op.create_check_constraint(
    "points_cost_nonneg",  # SQLAlchemy convention sẽ prepend `ck_rewards_` → final: ck_rewards_points_cost_nonneg
    "rewards", "points_cost >= 0",
)
op.add_column("rewards", sa.Column("valid_from", sa.Date(), nullable=True))
```

CK mới gọi từ `op.create_check_constraint` với `name=` thuần (không tự prepend) — alembic dùng literal name. Tuy nhiên model declaration `__table_args__` của Reward dùng convention nên khi SQLAlchemy đọc lại metadata sẽ resolve về `ck_rewards_<name>`. Để alembic và model align, dùng tên ngắn `points_cost_nonneg` ở alembic + `points_cost_nonneg` ở model — runtime cả hai đều thành `ck_rewards_points_cost_nonneg` (single-prefix). CK mới NOT bị double-prefix bug; rebuild các CK cũ ngoài scope spec này.

Cập nhật `Reward.__table_args__`:
```python
CheckConstraint("points_cost >= 0", name="points_cost_nonneg"),  # thay positive
```

### Schema (Pydantic)

**`RewardCreateRequest` / `RewardUpdateRequest` / `RewardResponse`** (`schemas/reward.py`) — đầy đủ 3 schema cùng update để FE đọc/ghi `valid_from`:

```python
class RewardCreateRequest(BaseModel):
    name: str
    description: str | None = None
    points_cost: int = Field(ge=0)  # thay gt=0 → ge=0 (cho phép 0 = free voucher)
    stock: int | None = None
    image_url: str | None = None
    template_id: int | None = None
    offer_type: RewardOfferType
    offer_value: int | None = None
    offer_label: str
    valid_from: date | None = None  # NEW
    valid_until: date | None = None
    terms: str | None = None
    min_purchase_amount: int | None = None

    @model_validator(mode="after")
    def _check_date_range(self) -> "RewardCreateRequest":
        if self.valid_from and self.valid_until and self.valid_from > self.valid_until:
            raise ValueError("valid_from phải <= valid_until")
        return self


class RewardUpdateRequest(BaseModel):
    # ... fields cũ giữ nguyên ...
    points_cost: int | None = Field(default=None, ge=0)  # ge=0 thay gt=0
    valid_from: date | None = None  # NEW
    # validator tương tự


class RewardResponse(BaseModel):
    id: int
    partner_id: int
    name: str
    description: str | None
    points_cost: int
    stock: int | None
    image_url: str | None
    is_active: bool
    template_id: int | None
    offer_type: RewardOfferType
    offer_value: int | None
    offer_label: str
    valid_from: date | None  # NEW
    valid_until: date | None
    terms: str | None
    min_purchase_amount: int | None
    created_at: datetime
    updated_at: datetime
```

Tất cả 3 schema phải có `valid_from` đồng thời — thiếu một trong 3 → FE form không POST được hoặc edit page không hiển thị giá trị cũ.

### Service

**`RedemptionService.claim_free(*, partner_id, user_id, reward_id, ttl_days=14)` — hàm mới:**

```python
async def claim_free(self, *, partner_id, user_id, reward_id, ttl_days=14):
    today = date.today()
    # Lock reward (KHÔNG filter points_cost ở WHERE — guard sau fetch để error rõ ràng)
    reward = await self.db.scalar(
        select(Reward).where(
            Reward.id == reward_id,
            Reward.partner_id == partner_id,
            Reward.is_active.is_(True),
            Reward.deleted_at.is_(None),
            ((Reward.valid_from.is_(None)) | (Reward.valid_from <= today)),
            ((Reward.valid_until.is_(None)) | (Reward.valid_until >= today)),
        ).with_for_update()
    )
    if reward is None:
        raise ValueError("Reward không tồn tại hoặc đã hết hạn")
    if reward.points_cost > 0:
        raise WrongClaimMethodError(
            "Reward này yêu cầu đổi bằng điểm, dùng /redemptions thay vì /claim"
        )

    # Atomic decrement stock (per-shop cap)
    if reward.stock is not None:
        result = await self.db.execute(
            update(Reward).where(Reward.id == reward_id, Reward.stock > 0)
            .values(stock=Reward.stock - 1)
        )
        if result.rowcount == 0:
            raise OutOfStockError(...)

    # Generate code (tái dùng _generate_code)
    # ...

    redemption = Redemption(
        partner_id=partner_id, user_id=user_id, reward_id=reward_id,
        points_spent=0,  # free
        redemption_code=code,
        status=RedemptionStatus.PENDING,
        redeemed_at=now(), expires_at=now() + ttl_days,
    )
    self.db.add(redemption)
    try:
        await self.db.flush()
    except IntegrityError as e:
        # Trường hợp duy nhất còn lại: collision redemption_code (uq_redemptions_partner_code)
        if reward.stock is not None:
            # Rollback stock đã trừ
            await self.db.execute(
                update(Reward).where(Reward.id == reward_id)
                .values(stock=Reward.stock + 1)
            )
        raise AlreadyClaimedError(
            "Bạn đã nhận voucher này rồi"
        ) from e
    # KHÔNG ghi point_ledger (delta=0 vô nghĩa, giữ semantic ledger sạch)
    return redemption
```

**Per-user uniqueness — service-layer pre-check** (chỉ áp cho `claim_free`, KHÔNG có DB index):

Trước khi insert redemption mới trong `claim_free`, service truy vấn:
```python
existing = await db.scalar(
    select(Redemption.id).where(
        Redemption.user_id == user_id,
        Redemption.reward_id == reward_id,
        Redemption.status == RedemptionStatus.PENDING,
    )
)
if existing is not None:
    raise AlreadyClaimedError("Bạn đã nhận voucher này rồi")
```

`Reward.with_for_update()` ở Bước 1 của `claim_free` serialise các call cùng `reward_id` (cùng user hoặc khác user), nên không có race giữa pre-check và insert. Chỉ áp cho free voucher để tránh chặn nhầm khi user có đủ điểm muốn đổi cùng quà nhiều lần qua luồng `redeem`. Khi voucher cũ chuyển sang `used` hoặc `expired`, user có thể claim free voucher mới.

**`RedemptionService.redeem`** — thêm guard sau fetch:
```python
if reward.points_cost == 0:
    raise WrongClaimMethodError(
        "Reward này là voucher miễn phí, dùng /claim thay vì /redemptions"
    )
```

Hai exception class mới:
```python
class WrongClaimMethodError(Exception): pass
class AlreadyClaimedError(Exception): pass
```

API layer map → 409 cho cả hai.

### API

**Endpoint mới**: `POST /users/me/rewards/{reward_id}/claim` — thêm vào `partners.users_router`:

```python
@users_router.post("/me/rewards/{reward_id}/claim", response_model=RedemptionResponse, status_code=201)
@limiter.limit("10/minute")
async def claim_free_reward(
    request: Request,
    reward_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RedemptionResponse:
    # Resolve partner_id từ reward
    reward = await db.scalar(select(Reward).where(Reward.id == reward_id, ...))
    if reward is None:
        raise HTTPException(404, ...)
    # Yêu cầu user là member (như redeem)
    is_member = await db.scalar(...)
    if is_member is None:
        raise HTTPException(403, "Bạn cần là thành viên của shop để nhận voucher")

    service = RedemptionService(db)
    try:
        return await service.claim_free(
            partner_id=reward.partner_id, user_id=user.id, reward_id=reward_id
        )
    except OutOfStockError as e:
        raise HTTPException(409, str(e)) from e
    except ValueError as e:
        raise HTTPException(404, str(e)) from e
```

Endpoint redeem cũ (`POST /users/me/redemptions`) giữ nguyên — chỉ phục vụ reward `points_cost > 0`.

### Frontend

Card reward (`/member/rewards`):
- `points_cost === 0` → button label "Nhận voucher miễn phí", call `POST /users/me/rewards/{id}/claim`, không show "200 điểm".
- `points_cost > 0` → button "Đổi {points_cost} điểm", call `POST /users/me/redemptions`.
- Disable nếu `stock === 0` ("Hết voucher") hoặc out-of-window.

Form tạo Reward (`/partner/rewards/new`):
- Field "Số điểm cần đổi" — cho phép nhập 0 (tooltip "Để 0 = voucher miễn phí, khách nhấn nhận trực tiếp").
- Thêm field "Ngày bắt đầu hiệu lực" (`valid_from`) bên cạnh `valid_until`.

### Test

- Unit: `claim_free` với reward `points_cost=5` → ValueError.
- Unit: `claim_free` 100 lần concurrent với `stock=10` → đúng 10 success, 90 OutOfStockError.
- Integration: tạo reward `points_cost=0`, `stock=5`, `valid_from = tomorrow` → claim hôm nay → 404.
- FE manual: customer thấy 2 loại button (đổi điểm vs nhận free), claim free voucher xuất hiện trong ví voucher.

---

## QT8 — Audit log + lock reason

### Schema

**Table `audit_logs`** (mới):

```python
class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    target_type: Mapped[str] = mapped_column(String(30), nullable=False)
    target_id: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    before_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    after_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "action IN ("
            "'user_lock','user_unlock','user_role_change',"
            "'partner_approve','partner_suspend','partner_unsuspend'"
            ")",
            name="audit_logs_action_valid",
        ),
        CheckConstraint(
            "target_type IN ('user','partner')",
            name="audit_logs_target_type_valid",
        ),
        Index("ix_audit_logs_target", "target_type", "target_id"),
        Index("ix_audit_logs_created_at", "created_at"),
    )
```

Action vocabulary (constant `app/core/audit_actions.py`):
- `user_lock`, `user_unlock`, `user_role_change`
- `partner_approve`, `partner_suspend`, `partner_unsuspend`
- (Có thể mở rộng sau bằng cách bổ sung constant + cập nhật CK; MVP 6 action này.)

Target types: `user`, `partner`. CK enforce ở DB level — typo trong code → fail-fast.

### Service

**`AuditLogService`** (`app/services/audit_log_service.py`):

```python
class AuditLogService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(
        self, *,
        actor_user_id: int,
        action: str,
        target_type: str,
        target_id: int,
        reason: str | None = None,
        before: dict | None = None,
        after: dict | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            actor_user_id=actor_user_id, action=action,
            target_type=target_type, target_id=target_id,
            reason=reason, before_snapshot=before, after_snapshot=after,
        )
        self.db.add(entry)
        await self.db.flush()
        return entry
```

### Hooks

**`admin.update_user`** (`api/admin.py`):
- Trước khi commit, snapshot `{is_active: target.is_active, system_role: target.system_role}`.
- Sau khi update, snapshot mới.
- Nếu `is_active` thay đổi → log action `user_lock` (nếu False) hoặc `user_unlock` (nếu True), với `reason = body.reason`.
- Nếu `system_role` thay đổi → log action `user_role_change` (extension nhỏ — list trong action vocabulary).

**`AdminUserUpdateRequest`** thêm field:
```python
reason: str | None = Field(default=None, max_length=500)
```

**`admin.approve_partner`** + **`admin.suspend_partner`**: gọi `AuditLogService.log` với action tương ứng + reason từ body + actor_user_id từ admin.

### API

**`GET /admin/audit-logs`** (mới):

```python
@router.get("/audit-logs", response_model=AuditLogListResponse)
async def list_audit_logs(
    action: str | None = None,
    target_type: str | None = None,
    target_id: int | None = None,
    actor_user_id: int | None = None,
    from_date: datetime | None = Query(None, alias="from"),
    to_date: datetime | None = Query(None, alias="to"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_super_admin),
) -> AuditLogListResponse:
    ...
```

Response shape:
```python
class AuditLogResponse(BaseModel):
    id: int
    actor_user_id: int | None
    actor_email: str | None  # batch-load
    action: str
    target_type: str
    target_id: int
    target_label: str | None  # name/email của target — batch-load partner.name hoặc user.email
    reason: str | None
    before_snapshot: dict | None
    after_snapshot: dict | None
    created_at: datetime

class AuditLogListResponse(BaseModel):
    items: list[AuditLogResponse]
    total: int
    limit: int
    offset: int
```

### Frontend

**Trang `/admin/audit-logs`** mới:
- Filter sidebar: action (dropdown), target_type, target_id, actor (search), from/to date.
- Table: created_at | actor (email) | action | target_type | target | reason | (expand for snapshots).
- Plain HTML table (đồng nhất với `/admin/logs`).
- Hook `useAdminAuditLogs` (query) trong `lib/hooks/`.

**Trang `/admin/users/{id}/edit`**: thêm field "Lý do thay đổi" (textarea) khi toggle `is_active` hoặc đổi role. Bắt buộc khi `is_active=false`. Truyền vào body PATCH.

**Dialog admin approve/suspend partner**: thêm textarea "Lý do" — bắt buộc khi suspend, optional khi approve.

### Test

- Unit: `AuditLogService.log` insert thành công, đọc lại đúng shape.
- Integration: lock user via `PATCH /admin/users/{id}` → query `audit_logs` thấy 1 entry `action=user_lock`, `reason=...`, `before/after snapshot` đúng.
- Integration: approve partner with reason → 1 entry `partner_approve`.
- FE manual: lock 1 user, mở `/admin/audit-logs` thấy entry mới.

---

## Migration order

**Mỗi phase 1 alembic revision riêng** (đồng bộ với rhythm "code → test → smoke → review → commit" của Sequencing). KHÔNG gộp 1 revision duy nhất — gộp sẽ bắt buộc deploy DDL trước phase 1, vi phạm gradual rollout.

| Phase | Revision file | DDL |
|---|---|---|
| QT5 | (không có DDL) | — |
| QT4 | (không có DDL) | — |
| QT1 | `<hex>_qt1_must_change_password.py` | `users.must_change_password BOOL DEFAULT FALSE NOT NULL` |
| QT8 | `<hex>_qt8_audit_logs.py` | `audit_logs` table + indexes |
| QT2 | `<hex>_qt2_partner_terms_license.py` | 6 cột partners |
| QT7 | `<hex>_qt7_reward_free_voucher.py` | drop CK `ck_rewards_ck_rewards_points_cost_positive` + add CK `ck_rewards_points_cost_nonneg` + drop CK `ck_redemptions_ck_redemptions_points_positive` + add CK `ck_redemptions_points_spent_nonneg` + add `rewards.valid_from`. Ràng buộc 1-voucher-1-user kiểm tại tầng service `claim_free` (KHÔNG partial unique index DB). |

Backfill: rỗng (default values + NULL phù hợp).

`ALTER TABLE users ADD COLUMN must_change_password BOOLEAN NOT NULL DEFAULT FALSE` — PostgreSQL 11+ là metadata-only operation, an toàn ngay cả với table users đông; không cần backfill song song.

## Schema migration impact

- Existing partners: `terms_accepted_at IS NULL`, `business_license_url IS NULL`. **Chấp nhận** — partner cũ chưa từng accept terms theo flow mới. Không bắt buộc backfill (chỉ áp dụng cho partner mới đăng ký từ thời điểm cutover).
- Existing rewards: `valid_from IS NULL` (không giới hạn ngày bắt đầu).
- Existing users: `must_change_password = false`. Không ai bị locked-in do migration.

## Testing approach

- Pytest unit + integration cho mọi service/API change. Pattern theo `tests/integration/test_auth_api.py`.
- Smoke E2E (Playwright hoặc curl scripts) sau mỗi phase per `feedback_smoke_driven_review_loop.md`:
  - QT1: full forgot-password → login temp → blocked → change → unblocked.
  - QT2: register partner with license + terms → admin approve with reason → audit_logs có entry.
  - QT4: POS scan QR khách mới → tích điểm thành công.
  - QT5: tạo reward `valid_until = yesterday`, redeem → 404.
  - QT7: tạo reward `points_cost=0, stock=5`, claim 10 lần concurrent → đúng 5 success.
  - QT8: lock user with reason → audit_logs entry → unlock → 2nd entry.

## Sequencing

Plan sẽ tách 6 phase, mỗi phase 1 quy trình. Order đề xuất (tăng dần độ rủi ro):

1. **QT5** (~0.2d) — 1 dòng SQL, ít rủi ro nhất, làm warm-up.
2. **QT4** (~0.5d) — service refactor, không có schema change phức tạp.
3. **QT1** (~0.5d) — schema 1 cột + dependency middleware.
4. **QT8** (~1.5d) — schema mới, hooks vào nhiều endpoint.
5. **QT2** (~1d) — schema 6 cột, FE upload flow, T&C UI.
6. **QT7** (~1.5d) — schema constraint + cột mới + endpoint mới + FE phân biệt 2 button.

Mỗi phase: code → test → smoke → code-reviewer → fix critical → commit → next.

## Risks & mitigations

| Risk | Mitigation |
|---|---|
| `must_change_password` middleware block /admin → admin tự khoá khi forgot-password | Whitelist `/admin/users/{me}/reset-password` chỉ áp dụng cho admin. Hoặc: super_admin không bao giờ bị set `must_change_password=True` trong reset flow (skip ở service). Chốt: super_admin SKIP. |
| Migration thêm cột partners có default NULL → existing partners không có `terms_accepted_at` → policy có cần backfill? | Không backfill. Existing partner skip flow mới. Cảnh báo trong báo cáo: "kể từ v1.0 partners mới phải accept terms". |
| QT7 free voucher abuse — 1 user spam claim | Service-layer pre-check trong `claim_free`: query existing PENDING redemption cho `(user_id, reward_id)`, có thì raise `AlreadyClaimedError`. `Reward.with_for_update()` serialise các call concurrent. KHÔNG dùng partial unique index DB để không chặn nhầm luồng `redeem` (đổi điểm) khi user đổi cùng quà nhiều lần. Rate limit `10/minute` defense-in-depth. Stock cap giới hạn tổng phát ra. |
| Audit log table tăng nhanh | Index trên (target_type, target_id) + created_at. MVP không cần partition. Plan thresh: nếu > 100k rows trong 1 năm → partition. |
| Phone bắt buộc khi register breaking existing tests | Update test fixtures + factories thêm phone. |

## Non-goals (rõ ràng tránh scope creep)

- **Không** tạo Campaign model riêng (option B cũ).
- **Không** generic audit cho mọi data change (chỉ admin actions).
- **Không** T&C versioning system động (tĩnh ở FE).
- **Không** notify user qua email khi bị admin khoá (defer).
- **Không** rate limit lock count (defer).
- **Không** UI lịch sử thay đổi mật khẩu cho user.

## Định nghĩa "done"

Hoàn thành khi:
1. 6 phase commit lên main, mỗi phase có test pass + smoke verify.
2. `pytest -v` (ít nhất unit + những integration test khả thi không cần docker testcontainers) green.
3. `npx tsc --noEmit` (FE) green.
4. Smoke E2E full 8 quy trình (curl scripts) pass.
5. Báo cáo đồ án mục 2.3.1 không còn mâu thuẫn với code.
6. CHƯƠNG 1 mục Phạm vi (báo cáo docx) bỏ "Hệ thống phân hạng thành viên" khỏi out-of-scope.
