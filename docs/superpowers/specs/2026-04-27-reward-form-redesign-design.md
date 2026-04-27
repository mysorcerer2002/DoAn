# Reward Form Redesign — Design Spec

**Ngày:** 2026-04-27
**Trang đích:** `/partner/rewards` (modal Thêm/Sửa quà)
**Status:** Đã chốt scope với user.

## Bối cảnh & vấn đề

Hiện trạng audit:

- **`Reward` model** có `offer_type` (`PERCENT_DISCOUNT` / `FIXED_DISCOUNT` / `ITEM_GIFT`), `offer_value`, `offer_label`, `valid_until`, `terms` — tất cả NOT NULL hoặc nullable đúng theo CHECK constraint `offer_value_matches_type`.
- **`RewardCreateRequest` schema** chỉ có 5 field: `name`, `description`, `image_url`, `points_cost`, `stock` → **bỏ qua hoàn toàn** offer_type & friends.
- **`RewardService.create_reward`** không set offer_type/value/label → INSERT hiện tại **rớt CHECK constraint**, tạo quà mới qua API API là broken.
- **FE form** cũng chỉ có 5 field tương ứng, không cho user chọn loại quà.
- **DB chưa có cột `min_purchase_amount`** — user yêu cầu thêm để hỗ trợ "voucher chỉ áp dụng khi hoá đơn ≥ X đ".

Quà tặng đang chỉ tạo được qua `seed_demo.py` (set ORM trực tiếp). Đây là gap chức năng nghiêm trọng.

## Quyết định đã chốt

1. **3 loại quà** (giữ enum `RewardOfferType` đang có): `PERCENT_DISCOUNT`, `FIXED_DISCOUNT`, `ITEM_GIFT`.
2. **`min_purchase_amount`**: cột mới, nullable. Chỉ áp dụng cho `PERCENT_DISCOUNT` + `FIXED_DISCOUNT`. Optional — user bật/tắt được, null = không yêu cầu hoá đơn min. ITEM_GIFT phải null (validate cứng).
3. **`valid_until` + `terms`** expose ra form (cả 2 nullable, ai cần thì điền).
4. **Validation chéo (Pydantic + DB CHECK):**
   - `PERCENT_DISCOUNT`: `offer_value` ∈ [1, 100] (đơn vị %).
   - `FIXED_DISCOUNT`: `offer_value` > 0 (đơn vị VND).
   - `ITEM_GIFT`: `offer_value` phải null + `min_purchase_amount` phải null.
   - `offer_label` luôn bắt buộc (≤ 120 ký tự, đồng bộ DB schema hiện tại).

## Backend changes

### Migration mới

Alembic file: revision id verify bằng `alembic current` trên prod trước khi viết, không pin trong spec. Down_revision = head hiện tại.

```python
def upgrade() -> None:
    op.add_column(
        "rewards",
        sa.Column("min_purchase_amount", sa.Integer(), nullable=True),
    )
    op.create_check_constraint(
        "min_purchase_nonneg_or_null",
        "rewards",
        "min_purchase_amount IS NULL OR min_purchase_amount > 0",
    )
    # ITEM_GIFT không được có min_purchase
    op.create_check_constraint(
        "min_purchase_only_for_voucher",
        "rewards",
        "offer_type IN ('PERCENT_DISCOUNT','FIXED_DISCOUNT') OR min_purchase_amount IS NULL",
    )


def downgrade() -> None:
    # drop_constraint KHÔNG apply naming convention → phải dùng full name đã prefix
    op.drop_constraint(
        "ck_rewards_min_purchase_only_for_voucher", "rewards", type_="check"
    )
    op.drop_constraint(
        "ck_rewards_min_purchase_nonneg_or_null", "rewards", type_="check"
    )
    op.drop_column("rewards", "min_purchase_amount")
```

### `app/models/reward.py`

- Thêm `min_purchase_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)`.
- Thêm 2 `CheckConstraint` tương ứng (suffix-only theo naming convention).

### `app/schemas/reward.py`

- `RewardCreateRequest`: thêm `offer_type`, `offer_value`, `offer_label`, `min_purchase_amount`, `valid_until`, `terms`. Tất cả Vietnamese error messages qua `@field_validator` raise `ValueError("Nhãn quà bắt buộc")` v.v.
- `RewardUpdateRequest`: tất cả optional. **`offer_type` ở update KHÔNG cho phép đổi** (chốt cứng — xem dưới).
- `RewardResponse`: thêm 6 field này để FE hiển thị.
- `model_validator(mode="after")` cho `RewardCreateRequest`:
  - PERCENT: `offer_value` ∈ [1, 100] (int).
  - FIXED: `offer_value` > 0 (int).
  - ITEM_GIFT: `offer_value is None` AND `min_purchase_amount is None`.
  - `offer_label` required (≥ 1, ≤ 120 ký tự).

**Quyết định: `offer_type` immutable sau khi tạo.**
Lý do: `RewardUpdateRequest.exclude_unset=True` + Pydantic chỉ thấy field client gửi lên → không validate được cross-field với DB state hiện tại. 3 option đã cân nhắc (yêu cầu PATCH gửi đầy đủ / merge ở service / cấm đổi loại). Chọn **cấm đổi loại** vì đơn giản, an toàn, đồng bộ với constraint "đã có redemption không nên đổi". Shop muốn đổi → tạo reward mới, soft-delete reward cũ.

`RewardUpdateRequest`: KHÔNG có field `offer_type`. Cho phép đổi `offer_value`, `offer_label`, `min_purchase_amount` (cùng loại quà). `model_validator` của UpdateRequest cần nhận thêm `current_reward` qua context HOẶC validate ở service. **Chốt: validate ở service** (đọc `reward.offer_type` từ DB, kiểm `offer_value`/`min_purchase_amount` mới có hợp lệ với loại đó). Schema chỉ kiểm range cơ bản (`min_purchase_amount > 0` nếu set).

### `app/services/reward_service.py`

- `create_reward`: truyền 6 field mới vào `Reward(...)`.
- `update_reward`: sau khi `setattr`, gọi helper `_validate_reward_consistency(reward)` để kiểm post-merge (cùng logic create's `model_validator`, nhưng đọc từ ORM object). Nếu fail → raise `RewardValidationError` (mới), API map → 422 với Vietnamese message.

## Frontend changes

### `src/types/partner.ts`

Cập nhật 3 interface:

```ts
export type RewardOfferType = "PERCENT_DISCOUNT" | "FIXED_DISCOUNT" | "ITEM_GIFT"; // đã có

export interface RewardResponse {
  id: number;
  partner_id: number;       // rename từ tenant_id (đã rename ở BE)
  name: string;
  description: string | null;
  points_cost: number;
  stock: number | null;
  is_active: boolean;
  image_url: string | null;
  offer_type: RewardOfferType;
  offer_value: number | null;
  offer_label: string;
  min_purchase_amount: number | null;
  valid_until: string | null; // ISO date
  terms: string | null;
  created_at: string;
  deleted_at: string | null;
}

export interface RewardCreateRequest {
  name: string;
  description?: string | null;
  points_cost: number;
  stock?: number | null;
  is_active?: boolean;
  image_url?: string | null;
  offer_type: RewardOfferType;
  offer_value?: number | null;
  offer_label: string;
  min_purchase_amount?: number | null;
  valid_until?: string | null;
  terms?: string | null;
}

export interface RewardUpdateRequest {
  // tất cả optional
  ...
}
```

**Bắt buộc fix kèm:** `frontend/src/types/partner.ts` `RewardResponse` đang là `tenant_id: number` nhưng BE trả `partner_id` (đã rename ở `backend/app/schemas/reward.py`). Đây là silent type-mismatch — phải sửa thẳng trong cùng task này, không defer.

### `src/app/(partner)/partner/rewards/page.tsx` — modal Thêm/Sửa

**Layout mới:**

```
┌─ Thêm/Sửa quà ───────────────────────────┐
│ Loại quà *  [▼ Phần trăm giảm           ]│  ← Select (disabled khi Sửa)
│ Tên quà *   [_______________________]   │
│ Mô tả       [_______________________]   │
│                                          │
│ ┌── Conditional theo loại ────────────┐ │
│ │ % giảm * (1-100)  [___]              │ │  ← khi PERCENT
│ │ Số tiền giảm * (đ)[_______]          │ │  ← khi FIXED
│ │ (không hiện gì)                      │ │  ← khi ITEM_GIFT
│ └──────────────────────────────────────┘ │
│                                          │
│ Nhãn ngắn * [_______________________]   │  ← offer_label, auto-suggest theo loại+value
│                                          │
│ ☐ Yêu cầu hoá đơn tối thiểu              │  ← chỉ hiện khi PERCENT/FIXED
│   [_______ đ]                            │  ← chỉ enable khi tick
│                                          │
│ Điểm cần *  [____]  Tồn kho [____]       │
│ Hạn dùng    [____-__-__]                 │  ← date picker (date local của partner)
│ Điều khoản  [textarea]                   │
│ ☑ Đang bán                                │
│                                          │
│              [Huỷ]  [Lưu]                │
└──────────────────────────────────────────┘
```

**Behaviour:**

- **Sửa quà**: select "Loại quà" disabled (immutable theo quyết định BE). Hiện text "Loại quà không thể đổi sau khi tạo. Cần đổi → tạo quà mới."
- **Thêm quà**: select "Loại quà" đổi → reset `offer_value` + `min_purchase_amount` về null/empty.
- Khi loại = ITEM_GIFT → ẩn checkbox "Yêu cầu hoá đơn tối thiểu" + ô input.
- Khi user uncheck "Yêu cầu hoá đơn tối thiểu" → set `min_purchase_amount = null` (không giữ giá trị cũ).
- **Auto-suggest `offer_label`**: nếu user chưa sửa offer_label tay, tự fill khi `offer_type`+`offer_value` đổi:
  - PERCENT 20 → `"Giảm 20%"`
  - FIXED 50000 → `"Giảm 50.000đ"`
  - ITEM_GIFT → `"Quà tặng"` (default, user nên sửa thành tên cụ thể vd "Ly cafe")
  Khi user gõ vào ô offer_label → ngừng auto-fill (track `userEditedLabel` flag).
- Validation FE đồng bộ Pydantic. Submit fail → hiện inline error theo từng field.
- **Accessibility**: ô `min_purchase_amount` input có `disabled` + `aria-disabled` khi checkbox uncheck. Inline error message link qua `aria-describedby`.

**Card list quà** (không phải modal):

Thêm hiển thị nhãn loại quà bên cạnh tên, vd:
- `Giảm 20%` (chip indigo)
- `Giảm 50.000 đ` (chip indigo)
- `Quà tặng` (chip orange)

Hiển thị `min_purchase` khi có: "đơn từ X đ".

## Edge cases

- **Đổi loại quà sau khi tạo:** CẤM. Update schema không có field `offer_type`. Shop muốn đổi → tạo quà mới + soft-delete quà cũ.
- **Reward đã có redemption (issued):** vẫn cho phép edit `name`, `description`, `points_cost`, `stock`, `is_active`, `offer_value`, `offer_label`, `min_purchase_amount`, `valid_until`, `terms`. **Verify trước impl:** `Redemption.discount_amount` snapshot tại issue time (không reference live `reward.offer_value`) — nếu giả định sai thì đổi `offer_value` của reward đã issue sẽ vỡ data cũ.
- **valid_until = null** → quà không có hạn (forever).
- **PATCH với null explicit để clear**: spec chốt `model_dump(exclude_unset=True)` — nếu client gửi `{"valid_until": null}` thì SET null; nếu không gửi field đó thì giữ nguyên. FE date picker clear → gửi `null`, không gửi `""`.
- **timezone `valid_until`**: model là `Date` (không `DateTime`). FE gửi ISO date (`YYYY-MM-DD`) đại diện local date của partner. Backend không convert tz.
- **FIXED_DISCOUNT với `min_purchase_amount < offer_value`**: VD voucher giảm 100k với min 50k → sau giảm hoá đơn âm. Spec **không cấm** ở data layer (defer cho UX warning sau). Logic redeem khi áp voucher phải clamp `discount = min(offer_value, total)`. **Verify trước impl** redeem flow đã clamp; nếu chưa, mở task riêng.
- **Quà ITEM_GIFT có points_cost rất lớn** + ngưỡng hoá đơn → user mong đợi "đổi 500 điểm lấy 1 ly cafe khi hoá đơn ≥ 100k". Theo quyết định, ITEM_GIFT KHÔNG có min_purchase. Nếu shop muốn ngưỡng → tạo voucher `FIXED_DISCOUNT` value = giá ly cafe + min_purchase.
- **`offer_value` đơn vị**: PERCENT là int 1-100 (không decimal). FIXED là int VND (tròn đồng). Tương lai muốn 7.5% hoặc 1.5đ → migration `ALTER COLUMN offer_value TYPE NUMERIC(10,2)` + relax CHECK. Out of scope đồ án.

## Out of scope

- Cảnh báo khi đổi offer_type của quà đã issued (deferred).
- Bulk edit quà.
- Image upload form (giữ nguyên field `image_url` hiện tại).

## Acceptance

- [ ] BE: migration apply clean trên prod DB hiện hữu (đã có quà với offer_type set sẵn từ seed).
- [ ] BE: migration downgrade chạy được sạch (rollback test).
- [ ] BE: `POST /api/partner/rewards` với body có `offer_type=PERCENT_DISCOUNT` + `offer_value=20` + `offer_label="Giảm 20%"` → 201 Created, DB có row đúng.
- [ ] BE: `POST` thiếu `offer_type` → 422 (Pydantic Required), KHÔNG 500 IntegrityError.
- [ ] BE: `POST` thiếu `offer_label` → 422 với Vietnamese message.
- [ ] BE: `POST` `offer_type=PERCENT_DISCOUNT` + `offer_value=150` → 422 (out of range).
- [ ] BE: `POST` `offer_type=ITEM_GIFT` + `min_purchase_amount=50000` → 422.
- [ ] BE: `POST` `offer_type=ITEM_GIFT` + `offer_value=10` → 422 (ITEM_GIFT phải có offer_value null).
- [ ] BE: `PATCH` reward với `{"offer_type": "ITEM_GIFT"}` → 422 (immutable, schema không có field này — Pydantic extra='ignore' hoặc 'forbid' tuỳ config; phải explicit ignore field này).
- [ ] BE: `PATCH` reward PERCENT đặt `offer_value=200` → 422 (service post-merge validation).
- [ ] BE: `PATCH` reward ITEM_GIFT đặt `min_purchase_amount=50000` → 422 (service post-merge validation).
- [ ] BE: existing reward (seed Free Coffee/Cake/...) sau migration `GET /api/partner/rewards/{id}` trả `min_purchase_amount: null` đúng.
- [ ] FE: `npx tsc --noEmit` clean.
- [ ] FE: `RewardResponse` type sửa từ `tenant_id` → `partner_id`, no other consumer breaks.
- [ ] FE: form thêm quà cho phép chọn 3 loại; conditional fields hiển thị đúng; submit thành công cả 3 loại.
- [ ] FE: form sửa quà — select "Loại quà" disabled, hiện text giải thích.
- [ ] FE: auto-suggest `offer_label` chạy đúng cho PERCENT/FIXED, ngừng khi user gõ tay.
- [ ] FE: checkbox min_purchase uncheck → input disabled + value reset null.
- [ ] FE: card list hiển thị chip loại + "đơn từ X đ" nếu có min_purchase.
- [ ] Smoke: tạo 1 reward mỗi loại qua UI, đổi quà thành công ở `/member/partners/{id}` (không vỡ flow redeem).
