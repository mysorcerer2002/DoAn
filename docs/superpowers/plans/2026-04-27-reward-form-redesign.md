# Reward Form Redesign — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Lấp gap chức năng tạo/sửa quà — BE schema thiếu `offer_type`/`offer_value`/`offer_label` (đang rớt CHECK constraint, API broken), thêm cột `min_purchase_amount` cho voucher, FE form cho phép chọn loại quà với conditional fields.

**Architecture:** BE — Alembic migration thêm cột + 2 CHECK constraint, model + schema mới (Pydantic `model_validator` cho create, service post-merge validation cho update vì `offer_type` immutable), service `_validate_reward_consistency` helper. FE — types fix `tenant_id`→`partner_id` + thêm 6 field, form modal redesign với conditional rendering theo `offer_type` + auto-suggest `offer_label` + accessibility attrs, card list chip hiển thị loại + min_purchase.

**Tech Stack:** FastAPI + SQLAlchemy 2.0 async + Alembic + Pydantic v2 + asyncpg + Next.js 14 App Router + react-hook-form + TanStack Query + Tailwind v4.

**Spec ref:** `docs/superpowers/specs/2026-04-27-reward-form-redesign-design.md`

**Alembic head hiện tại:** `e2f3a4b5c6d7` (verify lại bằng `alembic current` trước khi viết migration).

---

## Task 1: BE — Migration thêm `min_purchase_amount` + CHECK constraints

**Files:**
- Create: `backend/alembic/versions/a1b2c3d4e5f6_add_reward_min_purchase_amount.py` (revision id 12 hex tự sinh, KHÔNG copy từ plan này)

- [ ] **Step 1: Generate revision skeleton**

```bash
docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend \
  alembic revision -m "add reward min purchase amount"
```

Verify file mới có `down_revision = "e2f3a4b5c6d7"`. Nếu không, sửa thủ công.

- [ ] **Step 2: Viết upgrade + downgrade**

```python
"""add reward min_purchase_amount

Revision ID: <auto>
Revises: e2f3a4b5c6d7
Create Date: 2026-04-27 ...
"""

from alembic import op
import sqlalchemy as sa


revision = "<auto>"
down_revision = "e2f3a4b5c6d7"
branch_labels = None
depends_on = None


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
    op.create_check_constraint(
        "min_purchase_only_for_voucher",
        "rewards",
        "offer_type IN ('PERCENT_DISCOUNT','FIXED_DISCOUNT') OR min_purchase_amount IS NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_rewards_min_purchase_only_for_voucher", "rewards", type_="check"
    )
    op.drop_constraint(
        "ck_rewards_min_purchase_nonneg_or_null", "rewards", type_="check"
    )
    op.drop_column("rewards", "min_purchase_amount")
```

- [ ] **Step 3: Apply + verify**

```bash
docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend \
  alembic upgrade head
docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend \
  alembic current
```

Expected: head trỏ về revision mới.

- [ ] **Step 4: Verify CHECK constraint apply**

```bash
docker exec loyalty-postgres-prod psql -U loyalty -d loyalty -c \
  "\d+ rewards" | grep -i min_purchase
```

Expected: thấy column `min_purchase_amount integer` + 2 CHECK với prefix `ck_rewards_`.

- [ ] **Step 5: Test downgrade**

```bash
docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend \
  alembic downgrade -1
docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend \
  alembic upgrade head
```

Expected: cả 2 chạy không lỗi. Sau khi `upgrade head` xong, head lại về revision mới.

- [ ] **Step 6: Commit**

```bash
git add backend/alembic/versions/<file>.py
git commit -m "feat(reward,db): thêm cột min_purchase_amount + 2 CHECK ràng buộc theo loại quà"
```

---

## Task 2: BE — Model `Reward` thêm `min_purchase_amount` + 2 CheckConstraint

**Files:**
- Modify: `backend/app/models/reward.py`

- [ ] **Step 1: Đọc model hiện tại để xác định pattern**

`backend/app/models/reward.py` đã có `__table_args__` với suffix-only naming. Thêm 2 constraint mới và 1 column.

- [ ] **Step 2: Sửa file**

```python
class Reward(Base, TimestampMixin):
    __tablename__ = "rewards"
    __table_args__ = (
        CheckConstraint("stock IS NULL OR stock >= 0", name="stock_nonneg_or_null"),
        CheckConstraint("points_cost > 0", name="points_cost_positive"),
        CheckConstraint(
            "(offer_type = 'PERCENT_DISCOUNT' AND offer_value BETWEEN 1 AND 100) OR "
            "(offer_type = 'FIXED_DISCOUNT'   AND offer_value > 0) OR "
            "(offer_type = 'ITEM_GIFT'        AND offer_value IS NULL)",
            name="offer_value_matches_type",
        ),
        CheckConstraint(
            "min_purchase_amount IS NULL OR min_purchase_amount > 0",
            name="min_purchase_nonneg_or_null",
        ),
        CheckConstraint(
            "offer_type IN ('PERCENT_DISCOUNT','FIXED_DISCOUNT') "
            "OR min_purchase_amount IS NULL",
            name="min_purchase_only_for_voucher",
        ),
    )

    # ... các field hiện có giữ nguyên ...

    min_purchase_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
```

Đặt `min_purchase_amount` sau `terms` để giữ thứ tự logic (offer_*-related ở cuối).

- [ ] **Step 3: Sanity check — model load không lỗi**

```bash
docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend \
  python -c "from app.models.reward import Reward; print(Reward.__table__.columns.keys())"
```

Expected: list columns có `min_purchase_amount`.

- [ ] **Step 4: Commit**

```bash
git add backend/app/models/reward.py
git commit -m "feat(reward): thêm min_purchase_amount + 2 CheckConstraint vào ORM"
```

---

## Task 3: BE — Schema `RewardCreateRequest`/`RewardUpdateRequest`/`RewardResponse`

**Files:**
- Modify: `backend/app/schemas/reward.py`

- [ ] **Step 1: Viết schema mới**

```python
"""Pydantic schemas cho Reward CRUD."""

from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.reward import RewardOfferType


class RewardCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    image_url: str | None = Field(default=None, max_length=500)
    points_cost: int = Field(gt=0)
    stock: int | None = Field(default=None, ge=0)
    is_active: bool = True

    offer_type: RewardOfferType
    offer_value: int | None = None
    offer_label: str = Field(min_length=1, max_length=120)
    min_purchase_amount: int | None = Field(default=None, gt=0)
    valid_until: date | None = None
    terms: str | None = None

    @field_validator("offer_label")
    @classmethod
    def _label_required(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Nhãn quà bắt buộc")
        return v.strip()

    @model_validator(mode="after")
    def _validate_offer_consistency(self) -> "RewardCreateRequest":
        ot = self.offer_type
        if ot == RewardOfferType.PERCENT_DISCOUNT:
            if self.offer_value is None or not (1 <= self.offer_value <= 100):
                raise ValueError("Phần trăm giảm phải từ 1 đến 100")
        elif ot == RewardOfferType.FIXED_DISCOUNT:
            if self.offer_value is None or self.offer_value <= 0:
                raise ValueError("Số tiền giảm phải lớn hơn 0")
        elif ot == RewardOfferType.ITEM_GIFT:
            if self.offer_value is not None:
                raise ValueError("Quà tặng hiện vật không được nhập giá trị giảm")
            if self.min_purchase_amount is not None:
                raise ValueError("Quà tặng hiện vật không được đặt hoá đơn tối thiểu")
        return self


class RewardUpdateRequest(BaseModel):
    """offer_type IMMUTABLE — schema reject explicit thay vì silent ignore (UX rõ hơn)."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    image_url: str | None = Field(default=None, max_length=500)
    points_cost: int | None = Field(default=None, gt=0)
    stock: int | None = Field(default=None, ge=0)
    is_active: bool | None = None

    offer_value: int | None = None
    offer_label: str | None = Field(default=None, min_length=1, max_length=120)
    min_purchase_amount: int | None = Field(default=None, gt=0)
    valid_until: date | None = None
    terms: str | None = None

    # Cho phép field offer_type pass qua schema để raise 422 rõ ràng (không silent ignore).
    offer_type: RewardOfferType | None = None

    @model_validator(mode="after")
    def _reject_offer_type_change(self) -> "RewardUpdateRequest":
        if self.offer_type is not None:
            raise ValueError(
                "Loại quà không thể đổi sau khi tạo. Cần đổi → tạo quà mới."
            )
        return self


class RewardResponse(BaseModel):
    id: int
    partner_id: int
    name: str
    description: str | None
    image_url: str | None
    points_cost: int
    stock: int | None
    is_active: bool
    deleted_at: datetime | None = None
    created_at: datetime

    offer_type: RewardOfferType
    offer_value: int | None
    offer_label: str
    min_purchase_amount: int | None
    valid_until: date | None
    terms: str | None

    model_config = {"from_attributes": True}


class RewardStatsResponse(BaseModel):
    reward_id: int
    offer_type: str
    issued: int
    redeemed: int
    used: int
    expired: int
    total_discount_cost: int | None = None
```

Lưu ý:
- `RewardUpdateRequest` có `model_config["extra"] = "ignore"` — nếu client gửi `offer_type`, schema bỏ qua (không lỗi 422 noisy). Service không thấy field nên không update.
- `RewardCreateRequest.is_active` default True (đồng bộ DB default).

- [ ] **Step 2: Type-check imports**

```bash
docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend \
  python -c "from app.schemas.reward import RewardCreateRequest, RewardUpdateRequest, RewardResponse; print('ok')"
```

Expected: in `ok` không trace.

- [ ] **Step 3: Commit**

```bash
git add backend/app/schemas/reward.py
git commit -m "feat(reward,api): expose offer_type/value/label + min_purchase + valid_until + terms; offer_type immutable ở update"
```

---

## Task 4: BE — Service `create_reward` + `update_reward` + `_validate_reward_consistency` helper

**Files:**
- Modify: `backend/app/services/reward_service.py`

- [ ] **Step 1: Thêm exception class + helper validation (validate STATE, không validate ORM object đã dirty)**

```python
"""RewardService — CRUD + soft delete cho rewards."""

from datetime import datetime, timezone

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.redemption import Redemption, RedemptionStatus
from app.models.reward import Reward, RewardOfferType
from app.schemas.reward import (
    RewardCreateRequest,
    RewardStatsResponse,
    RewardUpdateRequest,
)


class RewardNotFoundError(Exception):
    pass


class RewardValidationError(Exception):
    """Domain validation fail post-merge cho update — API map 422."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def _validate_reward_state(
    offer_type: str | RewardOfferType,
    offer_value: int | None,
    min_purchase_amount: int | None,
) -> None:
    """Kiểm hypothetical state hợp lệ — gọi TRƯỚC setattr để tránh dirty session."""
    ot = RewardOfferType(offer_type) if isinstance(offer_type, str) else offer_type
    if ot == RewardOfferType.PERCENT_DISCOUNT:
        if offer_value is None or not (1 <= offer_value <= 100):
            raise RewardValidationError("Phần trăm giảm phải từ 1 đến 100")
    elif ot == RewardOfferType.FIXED_DISCOUNT:
        if offer_value is None or offer_value <= 0:
            raise RewardValidationError("Số tiền giảm phải lớn hơn 0")
    elif ot == RewardOfferType.ITEM_GIFT:
        if offer_value is not None:
            raise RewardValidationError(
                "Quà tặng hiện vật không được có giá trị giảm"
            )
        if min_purchase_amount is not None:
            raise RewardValidationError(
                "Quà tặng hiện vật không được đặt hoá đơn tối thiểu"
            )
    if min_purchase_amount is not None and min_purchase_amount <= 0:
        raise RewardValidationError("Hoá đơn tối thiểu phải lớn hơn 0")
```

- [ ] **Step 2: Sửa `create_reward`**

```python
    async def create_reward(
        self, *, partner_id: int, request: RewardCreateRequest
    ) -> Reward:
        reward = Reward(
            partner_id=partner_id,
            name=request.name,
            description=request.description,
            image_url=request.image_url,
            points_cost=request.points_cost,
            stock=request.stock,
            is_active=request.is_active,
            offer_type=request.offer_type.value,
            offer_value=request.offer_value,
            offer_label=request.offer_label,
            min_purchase_amount=request.min_purchase_amount,
            valid_until=request.valid_until,
            terms=request.terms,
        )
        self.db.add(reward)
        await self.db.flush()
        return reward
```

- [ ] **Step 3: Sửa `update_reward` — validate TRƯỚC setattr (không dirty session khi fail)**

```python
    async def update_reward(
        self, *, partner_id: int, reward_id: int, request: RewardUpdateRequest
    ) -> Reward:
        reward = await self.get_reward(partner_id=partner_id, reward_id=reward_id)
        update_data = request.model_dump(exclude_unset=True)
        # offer_type immutable — schema đã reject, defensive check thêm.
        update_data.pop("offer_type", None)

        # Build hypothetical state (merge update_data với reward hiện tại)
        new_offer_value = update_data.get("offer_value", reward.offer_value)
        new_min_purchase = update_data.get(
            "min_purchase_amount", reward.min_purchase_amount
        )
        _validate_reward_state(
            offer_type=reward.offer_type,
            offer_value=new_offer_value,
            min_purchase_amount=new_min_purchase,
        )

        # Validation pass → mới setattr, session sạch nếu raise.
        for field, value in update_data.items():
            setattr(reward, field, value)
        await self.db.flush()
        return reward
```

- [ ] **Step 4: Sanity import**

```bash
docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend \
  python -c "from app.services.reward_service import RewardService, RewardValidationError; print('ok')"
```

Expected: `ok`.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/reward_service.py
git commit -m "feat(reward,service): set 6 field offer_* khi create + post-merge validate khi update"
```

---

## Task 5: BE — API route map `RewardValidationError` → 422

**Files:**
- Modify: `backend/app/api/rewards.py` (verify route file path qua glob trước)

- [ ] **Step 1: Tìm file API**

```bash
ls backend/app/api/ | grep -i reward
```

- [ ] **Step 2: Đọc current handler PATCH/PUT**

Xác định endpoint update reward gọi `RewardService.update_reward`. Hiện tại đang catch `RewardNotFoundError` → 404.

- [ ] **Step 3: Thêm catch `RewardValidationError`**

```python
from app.services.reward_service import (
    RewardNotFoundError,
    RewardService,
    RewardValidationError,
)

# ... trong handler update:
try:
    reward = await service.update_reward(
        partner_id=partner_id, reward_id=reward_id, request=payload
    )
except RewardNotFoundError:
    raise HTTPException(status_code=404, detail="Không tìm thấy quà")
except RewardValidationError as exc:
    raise HTTPException(status_code=422, detail=exc.message)
```

Pattern y hệt cho create nếu service create cũng có thể raise (hiện không, nhưng prophylactic).

- [ ] **Step 4: Smoke route**

```bash
# Mở swagger /docs hoặc curl với JWT partner owner
curl -X POST http://localhost:8000/api/partner/rewards \
  -H "Authorization: Bearer <token>" \
  -H "X-Partner-Id: 1" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","points_cost":100,"offer_type":"PERCENT_DISCOUNT","offer_value":20,"offer_label":"Giảm 20%"}'
```

Expected: 201 + JSON với 6 field mới đầy đủ.

```bash
# Test missing offer_type → 422
curl -X POST http://localhost:8000/api/partner/rewards \
  -H "Authorization: Bearer <token>" \
  -H "X-Partner-Id: 1" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","points_cost":100,"offer_label":"X"}'
```

Expected: 422 với `detail` nhắc `offer_type` required.

```bash
# Test ITEM_GIFT + min_purchase → 422
curl -X POST http://localhost:8000/api/partner/rewards \
  -H "Authorization: Bearer <token>" \
  -H "X-Partner-Id: 1" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","points_cost":100,"offer_type":"ITEM_GIFT","offer_label":"Quà","min_purchase_amount":50000}'
```

Expected: 422 message Vietnamese.

```bash
# Test PATCH PERCENT đặt offer_value=200 → 422 (post-merge service validate)
curl -X PATCH http://localhost:8000/api/partner/rewards/<id> \
  -H "Authorization: Bearer <token>" \
  -H "X-Partner-Id: 1" \
  -H "Content-Type: application/json" \
  -d '{"offer_value":200}'
```

Expected: 422 với "Phần trăm giảm phải từ 1 đến 100".

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/rewards.py
git commit -m "feat(reward,api): catch RewardValidationError → 422 Vietnamese"
```

---

## Task 6: BE — Verify existing rewards (seed) không bị vỡ

**Files:** không sửa — chỉ verify.

- [ ] **Step 1: Query seed rewards**

```bash
docker exec loyalty-postgres-prod psql -U loyalty -d loyalty -c \
  "SELECT id, name, offer_type, offer_value, offer_label, min_purchase_amount FROM rewards LIMIT 10"
```

Expected: tất cả row có `offer_type`/`offer_label` set, `min_purchase_amount` NULL.

- [ ] **Step 2: GET via API**

```bash
curl http://localhost:8000/api/partner/rewards \
  -H "Authorization: Bearer <token>" \
  -H "X-Partner-Id: 1"
```

Expected: response array có 6 field mới đầy đủ, `min_purchase_amount: null`.

Không commit (chỉ verify).

---

## Task 7: FE — Sửa types `partner.ts` (fix tenant_id + thêm 6 field)

**Files:**
- Modify: `frontend/src/types/partner.ts`

- [ ] **Step 1: Tìm consumer của `tenant_id` hiện tại trên Reward**

```bash
# Dùng GitNexus query trước, fallback grep nếu offline
```

Run:
```
gitnexus_query({query: "Reward tenant_id", repo: "frontend"})
```

Hoặc grep dự phòng:
```bash
grep -rn "reward.*tenant_id\|RewardResponse.*tenant_id" frontend/src
```

Expected: 0 hoặc rất ít hit (do field này có vẻ không được FE dùng — chỉ tồn tại trong type def).

- [ ] **Step 2: Sửa 3 interface**

```ts
// frontend/src/types/partner.ts

export type RewardOfferType = "PERCENT_DISCOUNT" | "FIXED_DISCOUNT" | "ITEM_GIFT";

export interface RewardResponse {
  id: number;
  partner_id: number;
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
  valid_until: string | null;  // ISO date YYYY-MM-DD
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
  name?: string;
  description?: string | null;
  points_cost?: number;
  stock?: number | null;
  is_active?: boolean;
  image_url?: string | null;
  // offer_type IMMUTABLE — không có ở đây.
  offer_value?: number | null;
  offer_label?: string;
  min_purchase_amount?: number | null;
  valid_until?: string | null;
  terms?: string | null;
}
```

Đặt `RewardOfferType` lên TRƯỚC `RewardResponse` (hiện đang ở dưới line 97 — di chuyển lên).

- [ ] **Step 3: tsc**

```bash
cd frontend && npx tsc --noEmit
```

Expected: 0 error. Nếu có error vì consumer dùng `tenant_id` thì sửa consumer ngay (chắc không có theo Step 1).

- [ ] **Step 4: Commit**

```bash
git add frontend/src/types/partner.ts
git commit -m "fix(partner,types): RewardResponse partner_id (sửa silent type mismatch) + thêm 6 field offer_*"
```

---

## Task 8: FE — Form modal `/partner/rewards` redesign

**Files:**
- Modify: `frontend/src/app/(partner)/partner/rewards/page.tsx`

- [ ] **Step 1: Đọc form hiện tại để identify state shape**

```bash
# Xem section form modal (khoảng line 300-380 theo summary)
```

Form state hiện tại có: name, description, points_cost, stock, image_url, is_active.

Cần thêm: `offer_type`, `offer_value`, `offer_label`, `min_purchase_amount`, `min_purchase_enabled` (FE-only toggle), `valid_until`, `terms`, `userEditedLabel` (FE-only flag).

- [ ] **Step 2: Sửa form state default + reset**

```tsx
// Default cho create
const defaultFormValues = {
  name: "",
  description: "",
  points_cost: 100,
  stock: null as number | null,
  image_url: "",
  is_active: true,
  offer_type: "PERCENT_DISCOUNT" as RewardOfferType,
  offer_value: 10,
  offer_label: "Giảm 10%",
  min_purchase_enabled: false,
  min_purchase_amount: null as number | null,
  valid_until: "" as string,
  terms: "",
};

// Khi mở edit: map từ RewardResponse → form
const fromReward = (r: RewardResponse) => ({
  name: r.name,
  description: r.description ?? "",
  points_cost: r.points_cost,
  stock: r.stock,
  image_url: r.image_url ?? "",
  is_active: r.is_active,
  offer_type: r.offer_type,
  offer_value: r.offer_value ?? null,
  offer_label: r.offer_label,
  min_purchase_enabled: r.min_purchase_amount != null,
  min_purchase_amount: r.min_purchase_amount,
  valid_until: r.valid_until ?? "",
  terms: r.terms ?? "",
});
```

- [ ] **Step 3: Auto-suggest `offer_label` — dùng useWatch (deps stable)**

```tsx
import { useWatch } from "react-hook-form";

const [userEditedLabel, setUserEditedLabel] = useState(false);
const offerType = useWatch({ control: form.control, name: "offer_type" });
const offerValue = useWatch({ control: form.control, name: "offer_value" });
const minPurchaseEnabled = useWatch({
  control: form.control,
  name: "min_purchase_enabled",
});

useEffect(() => {
  if (userEditedLabel) return;
  let label = "";
  if (offerType === "PERCENT_DISCOUNT" && offerValue) {
    label = `Giảm ${offerValue}%`;
  } else if (offerType === "FIXED_DISCOUNT" && offerValue) {
    label = `Giảm ${offerValue.toLocaleString("vi-VN")}đ`;
  } else if (offerType === "ITEM_GIFT") {
    label = "Quà tặng";
  }
  form.setValue("offer_label", label);
}, [offerType, offerValue, userEditedLabel, form]);

// Trên input offer_label
<Input
  value={form.watch("offer_label")}
  onChange={(e) => {
    setUserEditedLabel(true);
    form.setValue("offer_label", e.target.value);
  }}
  maxLength={120}
/>
```

Trong JSX form (Step 5), dùng `offerType`/`offerValue`/`minPurchaseEnabled` thay vì `form.watch(...)` lặp lại nhiều lần.

- [ ] **Step 4: Reset offer_value/min_purchase khi đổi offer_type (chỉ Create)**

```tsx
const isEdit = Boolean(editingReward);
const onTypeChange = (newType: RewardOfferType) => {
  form.setValue("offer_type", newType);
  if (!isEdit) {
    form.setValue("offer_value", newType === "ITEM_GIFT" ? null : 10);
    form.setValue("min_purchase_enabled", false);
    form.setValue("min_purchase_amount", null);
    setUserEditedLabel(false);  // bật lại auto-suggest
  }
};
```

- [ ] **Step 5: Render form layout (theo spec)**

```tsx
<Dialog open={open} onOpenChange={setOpen}>
  <DialogContent className="max-w-lg">
    <DialogHeader>
      <DialogTitle>{isEdit ? "Sửa quà" : "Thêm quà mới"}</DialogTitle>
    </DialogHeader>

    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
      {/* Loại quà */}
      <div>
        <Label htmlFor="offer_type">Loại quà *</Label>
        <Select
          value={form.watch("offer_type")}
          onValueChange={onTypeChange}
          disabled={isEdit}
        >
          <SelectTrigger id="offer_type">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="PERCENT_DISCOUNT">Voucher giảm phần trăm</SelectItem>
            <SelectItem value="FIXED_DISCOUNT">Voucher giảm số tiền</SelectItem>
            <SelectItem value="ITEM_GIFT">Quà tặng hiện vật</SelectItem>
          </SelectContent>
        </Select>
        {isEdit && (
          <p className="text-xs text-slate-500 mt-1">
            Loại quà không thể đổi sau khi tạo. Cần đổi → tạo quà mới.
          </p>
        )}
      </div>

      {/* Tên */}
      <div>
        <Label htmlFor="name">Tên quà *</Label>
        <Input id="name" {...form.register("name")} />
        {form.formState.errors.name && (
          <p className="text-xs text-rose-600 mt-1">
            {form.formState.errors.name.message}
          </p>
        )}
      </div>

      {/* Mô tả */}
      <div>
        <Label htmlFor="description">Mô tả</Label>
        <Textarea id="description" {...form.register("description")} />
      </div>

      {/* Conditional: % | VND | (none) */}
      {form.watch("offer_type") === "PERCENT_DISCOUNT" && (
        <div>
          <Label htmlFor="offer_value_pct">% giảm * (1-100)</Label>
          <Input
            id="offer_value_pct"
            type="number"
            min={1}
            max={100}
            {...form.register("offer_value", { valueAsNumber: true })}
          />
        </div>
      )}
      {form.watch("offer_type") === "FIXED_DISCOUNT" && (
        <div>
          <Label htmlFor="offer_value_fixed">Số tiền giảm * (đ)</Label>
          <Input
            id="offer_value_fixed"
            type="number"
            min={1}
            {...form.register("offer_value", { valueAsNumber: true })}
          />
        </div>
      )}

      {/* Nhãn ngắn */}
      <div>
        <Label htmlFor="offer_label">Nhãn ngắn *</Label>
        <Input
          id="offer_label"
          value={form.watch("offer_label")}
          onChange={(e) => {
            setUserEditedLabel(true);
            form.setValue("offer_label", e.target.value);
          }}
          maxLength={120}
        />
        <p className="text-xs text-slate-500 mt-1">
          Hiển thị trên thẻ quà, vd "Giảm 20%", "Quà tặng".
        </p>
      </div>

      {/* min_purchase — chỉ voucher */}
      {form.watch("offer_type") !== "ITEM_GIFT" && (
        <div>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={form.watch("min_purchase_enabled")}
              onChange={(e) => {
                form.setValue("min_purchase_enabled", e.target.checked);
                if (!e.target.checked) {
                  form.setValue("min_purchase_amount", null);
                }
              }}
            />
            <span>Yêu cầu hoá đơn tối thiểu</span>
          </label>
          <Input
            type="number"
            min={1}
            placeholder="đ"
            disabled={!form.watch("min_purchase_enabled")}
            aria-disabled={!form.watch("min_purchase_enabled")}
            value={form.watch("min_purchase_amount") ?? ""}
            onChange={(e) =>
              form.setValue(
                "min_purchase_amount",
                e.target.value ? Number(e.target.value) : null
              )
            }
            className="mt-2"
          />
        </div>
      )}

      {/* Điểm + tồn kho row */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <Label htmlFor="points_cost">Điểm cần *</Label>
          <Input
            id="points_cost"
            type="number"
            min={1}
            {...form.register("points_cost", { valueAsNumber: true })}
          />
        </div>
        <div>
          <Label htmlFor="stock">Tồn kho</Label>
          <Input
            id="stock"
            type="number"
            min={0}
            placeholder="Không giới hạn"
            value={form.watch("stock") ?? ""}
            onChange={(e) =>
              form.setValue(
                "stock",
                e.target.value ? Number(e.target.value) : null
              )
            }
          />
        </div>
      </div>

      {/* Hạn dùng */}
      <div>
        <Label htmlFor="valid_until">Hạn dùng</Label>
        <Input
          id="valid_until"
          type="date"
          {...form.register("valid_until")}
        />
      </div>

      {/* Điều khoản */}
      <div>
        <Label htmlFor="terms">Điều khoản</Label>
        <Textarea id="terms" rows={3} {...form.register("terms")} />
      </div>

      {/* Active */}
      <label className="flex items-center gap-2">
        <input type="checkbox" {...form.register("is_active")} />
        <span>Đang bán</span>
      </label>

      <DialogFooter>
        <Button type="button" variant="ghost" onClick={() => setOpen(false)}>
          Huỷ
        </Button>
        <Button type="submit">Lưu</Button>
      </DialogFooter>
    </form>
  </DialogContent>
</Dialog>
```

- [ ] **Step 6: Sửa `onSubmit` build payload đúng shape**

```tsx
const onSubmit = async (values: FormValues) => {
  const basePayload = {
    name: values.name,
    description: values.description || null,
    points_cost: values.points_cost,
    stock: values.stock,
    image_url: values.image_url || null,
    is_active: values.is_active,
    offer_value: values.offer_type === "ITEM_GIFT" ? null : values.offer_value,
    offer_label: values.offer_label,
    min_purchase_amount: values.min_purchase_enabled
      ? values.min_purchase_amount
      : null,
    valid_until: values.valid_until || null,
    terms: values.terms || null,
  };

  if (isEdit) {
    // KHÔNG gửi offer_type khi update
    await updateReward.mutateAsync({ id: editingReward!.id, ...basePayload });
  } else {
    await createReward.mutateAsync({
      ...basePayload,
      offer_type: values.offer_type,
    });
  }
  setOpen(false);
};
```

- [ ] **Step 7: tsc**

```bash
cd frontend && npx tsc --noEmit
```

Expected: 0 error.

- [ ] **Step 8: Smoke trong browser**

Mở `/partner/rewards`, login partner owner, click "Thêm quà":
- Đổi loại Voucher % → input `% giảm` hiện, nhãn auto fill "Giảm X%".
- Đổi loại Voucher VND → input số tiền hiện, nhãn auto fill "Giảm X.XXXđ".
- Đổi loại Quà tặng → ẩn input value, ẩn checkbox min_purchase, nhãn auto "Quà tặng".
- Tick checkbox "Yêu cầu hoá đơn" → input enable.
- Submit → 201, list refresh có quà mới.

Sửa quà → select Loại disabled, có text giải thích.

- [ ] **Step 9: Commit**

```bash
git add frontend/src/app/(partner)/partner/rewards/page.tsx
git commit -m "feat(partner,reward): form chọn loại quà + conditional fields + auto-suggest nhãn + accessibility"
```

---

## Task 9: FE — Card list reward chip loại + min_purchase

**Files:**
- Modify: `frontend/src/app/(partner)/partner/rewards/page.tsx` (cùng file Task 8, section card list)

- [ ] **Step 1: Helper format**

```tsx
function offerTypeChip(r: RewardResponse) {
  const cls =
    r.offer_type === "ITEM_GIFT"
      ? "bg-orange-100 text-orange-700"
      : "bg-indigo-100 text-indigo-700";
  return (
    <span className={`text-xs px-2 py-0.5 rounded ${cls}`}>
      {r.offer_label}
    </span>
  );
}
```

- [ ] **Step 2: Render trong card**

```tsx
<div className="flex items-center gap-2">
  <h3 className="font-semibold">{reward.name}</h3>
  {offerTypeChip(reward)}
</div>
{reward.min_purchase_amount && (
  <p className="text-xs text-slate-500 mt-1">
    Đơn từ {reward.min_purchase_amount.toLocaleString("vi-VN")}đ
  </p>
)}
```

- [ ] **Step 3: Smoke**

Reload `/partner/rewards`. Existing seed reward (Free Coffee, Cake) hiện chip + (nếu có min_purchase) text "Đơn từ X đ".

- [ ] **Step 4: Commit**

```bash
git add frontend/src/app/(partner)/partner/rewards/page.tsx
git commit -m "feat(partner,reward): card list hiện chip loại quà + ngưỡng hoá đơn"
```

---

## Task 10: Smoke E2E — happy + edge

**Files:** không sửa.

- [ ] **Step 1: Tạo 1 reward mỗi loại qua UI**

- Voucher 20% với min_purchase 100k.
- Voucher 50k với min_purchase 200k.
- Quà tặng "1 ly cafe" (no min_purchase).

Verify DB:
```bash
docker exec loyalty-postgres-prod psql -U loyalty -d loyalty -c \
  "SELECT name, offer_type, offer_value, offer_label, min_purchase_amount FROM rewards ORDER BY id DESC LIMIT 3"
```

Expected: 3 row đúng theo input.

- [ ] **Step 2: Sửa quà — đổi nhãn + min_purchase**

Sửa "Voucher 20%" → đổi nhãn thành "Khuyến mãi đặc biệt 20%", bỏ min_purchase. Save.

Verify:
```bash
docker exec loyalty-postgres-prod psql -U loyalty -d loyalty -c \
  "SELECT name, offer_label, min_purchase_amount FROM rewards WHERE name LIKE '%20%' ORDER BY id DESC LIMIT 1"
```

Expected: `offer_label = 'Khuyến mãi đặc biệt 20%'`, `min_purchase_amount IS NULL`.

- [ ] **Step 3: Member redeem reward (regression check)**

Login `khach1@gmail.com`, vào `/member/partners/<id>` của partner vừa tạo quà, đổi quà.

Expected: redeem thành công, voucher xuất hiện trong ví, không 500.

- [ ] **Step 4: Test edge — đổi loại qua API trực tiếp → 422**

```bash
curl -X PATCH http://localhost:8000/api/partner/rewards/<id> \
  -H "Authorization: Bearer <token>" \
  -H "X-Partner-Id: 1" \
  -H "Content-Type: application/json" \
  -d '{"offer_type":"ITEM_GIFT"}'
```

Expected: **422** với detail Vietnamese "Loại quà không thể đổi sau khi tạo. Cần đổi → tạo quà mới."

Verify DB không đổi:
```bash
docker exec loyalty-postgres-prod psql -U loyalty -d loyalty -c \
  "SELECT offer_type FROM rewards WHERE id = <id>"
```

Expected: vẫn loại cũ.

- [ ] **Step 5: Test edge — boundary `offer_value` lower bound**

```bash
curl -X POST http://localhost:8000/api/partner/rewards \
  -H "Authorization: Bearer <token>" \
  -H "X-Partner-Id: 1" \
  -H "Content-Type: application/json" \
  -d '{"name":"X","points_cost":100,"offer_type":"PERCENT_DISCOUNT","offer_value":0,"offer_label":"X"}'
```

Expected: 422 (offer_value=0 fail [1,100]).

- [ ] **Step 6: Stock 0 vs null trong card list**

Tạo 2 reward: stock=0 (sold out) + stock=null (unlimited). Reload `/partner/rewards`. Expected: card hiển thị đúng cả 2 (0 = "Hết hàng" hoặc số "0", null = "Không giới hạn"). Note: nếu render hiện tại không phân biệt, đây là edge case OUT-OF-SCOPE — không sửa trong task này, ghi nhận.

- [ ] **Step 7: Không có code change → không commit**

**OUT-OF-SCOPE note (đã document để tránh drift):**
- Không test FIXED min_purchase < offer_value (clamp ở redeem flow, defer per spec).
- Không test warning UX khi đổi reward đã có redemption (defer per spec).
- Card list stock=0 vs null nếu hiện tại render giống nhau → ghi nhận, không sửa.

---

## Self-Review Checklist

- [ ] Tất cả task có code thật, không placeholder.
- [ ] Migration revision id KHÔNG hardcode (note "tự sinh").
- [ ] Spec coverage: 6 BE acceptance + 6 FE acceptance + 2 smoke đã có task tương ứng.
- [ ] Type consistency: `RewardOfferType` enum dùng đồng nhất BE str value, FE string literal.
- [ ] Vietnamese error messages đầy đủ qua `field_validator` + `model_validator`.
- [ ] Naming convention CHECK: suffix-only ở `__table_args__`, full-prefixed ở `drop_constraint`.
- [ ] PATCH với `offer_type` bị silent ignore (không lỗi noisy 422) → `extra="ignore"`.
- [ ] FE auto-suggest có flag `userEditedLabel` chống ghi đè input user.
- [ ] FE accessibility: `disabled` + `aria-disabled` cho min_purchase input.
- [ ] Card list chip + min_purchase text Vietnamese format.
