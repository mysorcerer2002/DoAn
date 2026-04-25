# Sơ đồ class — MVP "Cân bằng" 2026-04-25

> Sơ đồ class SQLAlchemy theo **state target sau pivot** (xem spec canonical: `docs/spec-mvp-2026-04-25.md`).
> KHÔNG phản ánh state code hiện tại — code sẽ migrate qua revision `d4e5f6a7b8c9_pivot_to_mvp_balanced`.

## Tổng quan 4 cụm domain

| Cụm | Class | Vai trò |
|---|---|---|
| Identity | `User`, `VerificationCode` | Tài khoản + OTP forgot-password |
| Partner | `Partner`, `Membership`, `Tier`, `PointRule` | Shop + cấu hình tier per-partner + rule earn |
| Loyalty Ops | `Transaction`, `PointLedger`, `Redemption` | POS earn / append-only ledger / đổi quà |
| Reward | `Reward`, `VoucherTemplate` | Quà + design template (Hybrid C+i) |

## Sơ đồ

```mermaid
classDiagram
    direction LR

    %% ========================
    %% Base & Mixin
    %% ========================
    class Base {
        <<abstract>>
        +int id PK
    }
    class TimestampMixin {
        <<mixin>>
        +datetime created_at
        +datetime updated_at
    }

    %% ========================
    %% Identity Context
    %% ========================
    class User {
        +str email UK
        +str phone UK
        +str password_hash
        +str full_name
        +date birthday
        +int points_balance "ví global"
        +str system_role "regular/admin/super_admin"
        +bool is_active
        +bool is_shadow
        +datetime last_login_at
        +datetime password_changed_at
    }

    class VerificationCode {
        +int user_id FK
        +str code "6-digit OTP"
        +VerificationPurpose purpose "RESET_PASSWORD"
        +datetime expires_at
        +datetime used_at
    }

    %% ========================
    %% Partner Context
    %% ========================
    class Partner {
        +str slug UK
        +str name
        +str address
        +str description
        +PartnerCategory category
        +PartnerStatus status "PENDING/ACTIVE/SUSPENDED"
        +int owner_user_id FK
        +bigint points_wallet_balance "seed 1.000.000"
    }

    class Membership {
        +int partner_id FK
        +int user_id FK
        +int current_tier_id FK "nullable"
        +int lifetime_earned "monotonic"
        +datetime joined_at
        +datetime last_activity_at
    }

    class Tier {
        +int partner_id FK
        +str name "Bronze/Silver/Gold"
        +int min_points
        +Decimal earn_multiplier "0.5–5.0"
        +int sort_order
        +bool is_active
        +datetime deleted_at
    }

    class PointRule {
        +int partner_id FK
        +Decimal points_per_unit
        +int unit_amount "default 10.000"
        +bool use_tiers "default false"
        +bool is_active
    }

    %% ========================
    %% Loyalty Operations
    %% ========================
    class Transaction {
        +int partner_id FK
        +int membership_id FK
        +int staff_id FK
        +int gross_amount
        +int net_amount
        +int points_earned
        +str method
        +str note
        +str receipt_code
    }

    class PointLedger {
        +int user_id FK
        +int partner_id FK "trace source"
        +int delta "+EARN / -REDEEM"
        +LedgerReason reason "EARN/REDEEM/ADJUST"
        +str ref_type
        +int ref_id
        +int balance_after
        +str description
        %% append-only trigger
    }

    class Redemption {
        +int user_id FK
        +int partner_id FK
        +int reward_id FK
        +str redemption_code UK
        +int points_spent
        +RedemptionStatus status "PENDING/USED/EXPIRED"
        +datetime redeemed_at
        +datetime expires_at "+14 days"
        +datetime used_at
        +int used_by_staff_id FK
        +str snapshot_image_url "Hybrid lazy cache"
    }

    %% ========================
    %% Reward / Voucher Template
    %% ========================
    class Reward {
        +int partner_id FK
        +int template_id FK "nullable"
        +str name
        +str description
        +str image_url
        +int points_cost
        +int stock "nullable = unlimited"
        +OfferType offer_type "PERCENT/FIXED/ITEM_GIFT"
        +int offer_value "nullable cho ITEM_GIFT"
        +str offer_label
        +date valid_until
        +str terms
        +bool is_active
        +datetime deleted_at
    }

    class VoucherTemplate {
        +str name
        +TemplateCategory category "CAFE/FOOD/RETAIL/BEAUTY/SEASONAL/OTHER"
        +str frame_image_url
        +dict text_layout_config "JSONB"
        +bool is_active
    }

    %% ========================
    %% Inheritance
    %% ========================
    Base <|-- User
    Base <|-- VerificationCode
    Base <|-- Partner
    Base <|-- Membership
    Base <|-- Tier
    Base <|-- PointRule
    Base <|-- Transaction
    Base <|-- PointLedger
    Base <|-- Redemption
    Base <|-- Reward
    Base <|-- VoucherTemplate

    TimestampMixin <|.. User
    TimestampMixin <|.. VerificationCode
    TimestampMixin <|.. Partner
    TimestampMixin <|.. Membership
    TimestampMixin <|.. Tier
    TimestampMixin <|.. PointRule
    TimestampMixin <|.. Transaction
    TimestampMixin <|.. Redemption
    TimestampMixin <|.. Reward
    TimestampMixin <|.. VoucherTemplate

    %% ========================
    %% Associations
    %% ========================
    User "1" --> "*" Membership : joins
    User "1" --> "*" PointLedger : owns_balance
    User "1" --> "*" Redemption : claims
    User "1" --> "*" Partner : owns_shop
    User "1" --> "*" VerificationCode : requests

    Partner "1" --> "*" Membership : has_members
    Partner "1" --> "*" Tier : configures
    Partner "1" --> "0..1" PointRule : earn_config
    Partner "1" --> "*" Reward : offers
    Partner "1" --> "*" Redemption : redeemed_at
    Partner "1" --> "*" Transaction : happens_at
    Partner "1" --> "*" PointLedger : trace_source

    Membership "*" --> "0..1" Tier : current_tier
    Membership "1" --> "*" Transaction : scoped_by

    VoucherTemplate "1" --> "*" Reward : designs
    Reward "1" --> "*" Redemption : redeemed_as
```

## Schema invariants (kiểm tra ở test layer)

- `point_ledger` append-only — Postgres trigger `prevent_point_ledger_mutation` block UPDATE/DELETE
- `UNIQUE (partner_id, user_id)` trên `memberships`
- `UNIQUE (partner_id, name)` + `UNIQUE (partner_id, sort_order)` trên `tiers`
- Partial unique 1 active rule/shop trên `point_rules` (`WHERE is_active=true`)
- `lifetime_earned` chỉ tăng (monotonic), không giảm khi redeem
- `SUM(point_ledger.delta WHERE user_id=u) == users.points_balance`
- `partners.points_wallet_balance + SUM(EARN ledger WHERE partner_id=p) == 1.000.000` (wallet seed invariant)

## Cách render & export

- **Online**: paste khối Mermaid vào https://mermaid.live → tải PNG/SVG
- **VS Code**: extension *Markdown Preview Mermaid Support*
- **CLI**: `mmdc -i class-diagram-mvp-2026-04-25.mmd -o class-diagram-mvp-2026-04-25.png -t neutral -b white`

## Files đính kèm

- `class-diagram-mvp-2026-04-25.mmd` — source Mermaid thuần (cho `mmdc`)
- `class-diagram-mvp-2026-04-25.png` — bitmap (paste vào Word/PDF báo cáo)
- `class-diagram-mvp-2026-04-25.svg` — vector (zoom không vỡ nét)
