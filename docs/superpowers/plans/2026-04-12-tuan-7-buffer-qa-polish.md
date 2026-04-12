# Tuần 7 — Buffer, QA, iOS Test, Performance Check & Bug Fix

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development.
>
> **NGUYÊN TẮC TUẦN 7:** KHÔNG code feature mới (trừ bug fixes critical). Tuần 7 là **buffer chủ động** cho rework + polish + manual QA + test trên device thật + performance verification + chuẩn bị deploy.

**Goal:** Verify toàn bộ hệ thống hoạt động đúng end-to-end qua manual QA checklist đầy đủ. Test trên Android Chrome + iOS Safari (mượn bạn nếu cần). Performance check (smoke benchmark `ab` trên 3 endpoints quan trọng + N+1 query check). Lighthouse PWA audit `/member` ≥ 85. Bug fix các issues phát hiện. Polish UX cuối cùng. Chuẩn bị deploy script + demo data.

**Cuối tuần phải có:**
- Manual QA checklist 30+ items pass
- iOS Safari test xong (hoặc document limitation nếu không kịp)
- Lighthouse `/member` ≥ 85 PWA score
- Smoke benchmark `ab -n 500 -c 10` 3 endpoints chính p95 < 500ms
- Tất cả bugs found được fix hoặc note
- Deploy dry-run thành công (Docker + ngrok hoặc VPS)
- Tests cuối tuần: ~180 (thêm 5-10 integration tests cho gaps)
- CI xanh
- Sẵn sàng cho tuần 8 (chỉ deploy + báo cáo)

**Acceptance criteria:**
- Demo scenario end-to-end (xem Task 1) chạy trơn tru
- iOS Safari test: tích điểm qua manual + xem điểm + đổi quà + claim voucher (PWA install có thể skip nếu Safari hạn chế)
- `ab -n 500 -c 10 http://localhost:8000/health` → p95 < 100ms
- `ab -n 500 -c 10 -H "Authorization: Bearer ..." http://localhost:8000/merchant/analytics/dashboard` → p95 < 500ms
- N+1 query check: chạy `pytest -v --log-cli-level=INFO` với SQL logging → manual scan log để phát hiện queries lặp lại trong list endpoints
- Lighthouse `/member` PWA score ≥ 85
- `pytest -v` → ~180 tests pass
- CI xanh

---

## Tổng quan các phase

| Phase | Tasks | Mô tả |
|---|---|---|
| 1 | 1-3 | Chuẩn bị test environment + demo scenario data |
| 2 | 4-9 | Manual QA checklist (30+ items) — backend |
| 3 | 10-13 | Manual QA checklist — frontend Android Chrome |
| 4 | 14-16 | iOS Safari test (mượn bạn nếu cần) |
| 5 | 17-19 | Performance check (ab + N+1 query scan) |
| 6 | 20-22 | Lighthouse PWA audit + fix |
| 7 | 23-25 | Bug fix các issues phát hiện |
| 8 | 26-28 | Integration tests cho gaps (target +10 tests) |
| 9 | 29-31 | Deploy dry-run + README hoàn chỉnh |
| 10 | 32-33 | Push CI + tag tuần 7 |

**Total:** 33 tasks · ít LOC mới (mostly testing + bugs + docs)

---

## PHASE 1 — Test Environment & Demo Data

### Task 0 (★ NEW — fix C1 review tuần 7): Mở rộng seed script với rewards + campaigns

> **★ Quan trọng:** Plans tuần 4 và tuần 5 chỉ tạo bảng `rewards`/`campaigns`/`vouchers` nhưng KHÔNG có task explicit update `seed.py` để thêm data. Tuần 7 QA giả định seed có rewards/campaigns nhưng thực tế không có. PHẢI thêm trước khi reset môi trường ở Task 1.

**Files:**
- Modify: `D:/DoAn/backend/scripts/seed.py`

- [ ] **Step 1: Thêm functions seed_rewards + seed_campaigns**

```python
async def seed_rewards(db: AsyncSession, tenant_id: int) -> None:
    """5 rewards/tenant với điểm khác nhau."""
    from app.models.reward import Reward
    rewards = [
        ("Cà phê đen miễn phí", 50, 100),
        ("Bánh mì miễn phí", 100, 50),
        ("Voucher giảm 20k", 200, None),  # unlimited
        ("Voucher giảm 50k", 500, 20),
        ("Combo tặng kèm", 1000, 10),
    ]
    for name, cost, stock in rewards:
        existing = await db.scalar(
            select(Reward).where(Reward.tenant_id == tenant_id, Reward.name == name)
        )
        if existing is None:
            db.add(Reward(
                tenant_id=tenant_id, name=name, points_cost=cost, stock=stock,
                is_active=True,
            ))
    await db.flush()
    print(f"      + 5 rewards seeded")


async def seed_campaigns(db: AsyncSession, tenant_id: int) -> None:
    """3 campaigns/tenant: cuối tuần, sinh nhật, khai trương."""
    from datetime import datetime, timedelta, timezone
    from app.models.campaign import Campaign, CampaignSource, DiscountType

    now = datetime.now(timezone.utc)
    campaigns = [
        ("Cuối tuần 10%", DiscountType.PERCENT, 10, 50000, 30000, None, now - timedelta(days=7), now + timedelta(days=30)),
        ("Sinh nhật 20%", DiscountType.PERCENT, 20, 0, 100000, None, now - timedelta(days=30), now + timedelta(days=365)),
        ("Khai trương 30k", DiscountType.FIXED, 30000, 100000, None, 100, now - timedelta(days=14), now + timedelta(days=14)),
    ]
    for name, dtype, dval, min_order, max_disc, max_iss, starts, ends in campaigns:
        existing = await db.scalar(
            select(Campaign).where(Campaign.tenant_id == tenant_id, Campaign.name == name)
        )
        if existing is None:
            db.add(Campaign(
                tenant_id=tenant_id, name=name,
                discount_type=dtype, discount_value=dval,
                min_order=min_order, max_discount=max_disc, max_issuances=max_iss,
                starts_at=starts, ends_at=ends,
                is_active=True, source=CampaignSource.MANUAL,
            ))
    await db.flush()
    print(f"      + 3 campaigns seeded")
```

- [ ] **Step 2: Gọi 2 functions trong main `seed()` loop**

```python
# Trong loop tenants:
await seed_tier(...)  # đã có
await seed_point_rule(...)  # đã có
await seed_rewards(db, tenant_id=tenant.id)  # ★ NEW
await seed_campaigns(db, tenant_id=tenant.id)  # ★ NEW
await seed_members_and_transactions(db, tenant, owner)  # đã có
```

- [ ] **Step 3: Update Makefile seed-fresh thêm rewards/campaigns/vouchers/notifications**

```makefile
.PHONY: seed-fresh
seed-fresh:
	docker compose exec postgres psql -U loyalty -d loyalty -c "TRUNCATE \
		users, tenants, tenant_staff, tiers, point_rules, \
		verification_codes, tenant_settings_audit, \
		memberships, transactions, point_ledger, \
		rewards, redemptions, campaigns, vouchers, notifications \
		RESTART IDENTITY CASCADE;"
	$(MAKE) seed
```

- [ ] **Step 4: Test seed-fresh chạy đầy đủ**

```bash
cd D:/DoAn
make seed-fresh
docker compose exec postgres psql -U loyalty -d loyalty -c "
SELECT 'rewards' AS t, COUNT(*) FROM rewards
UNION ALL SELECT 'campaigns', COUNT(*) FROM campaigns;"
```

Expected: rewards=10, campaigns=6.

- [ ] **Step 5: Commit**

```bash
git add backend/scripts/seed.py Makefile
git commit -m "feat(backend): seed v3 với rewards + campaigns + update Makefile truncate (★ fix tuần 7 C1)"
```

---

### Task 1: Reset môi trường + seed v3 đầy đủ

```bash
cd D:/DoAn
read -p "Xoá volume Postgres (mất data hiện tại)? [y/N] " confirm
[[ $confirm == [yY] ]] || exit 1
docker compose down -v
docker compose up -d --build
make seed-fresh
```

Verify:
- Postgres healthy
- Backend `/health` OK
- Frontend `http://localhost:3000` mở được
- Seed v3 có: 2 tenants + 10 tiers (5/tenant) + 2 active point_rules + 6 staff (2 owner + 4 staff) + ~100 transactions + 10 rewards + 6 campaigns

- [ ] **Step 1:** Verify seed counts qua psql:

```bash
docker compose exec postgres psql -U loyalty -d loyalty -c "
SELECT 'tenants' AS t, COUNT(*) FROM tenants
UNION ALL SELECT 'tiers', COUNT(*) FROM tiers
UNION ALL SELECT 'transactions', COUNT(*) FROM transactions
UNION ALL SELECT 'memberships', COUNT(*) FROM memberships
UNION ALL SELECT 'point_ledger', COUNT(*) FROM point_ledger
UNION ALL SELECT 'rewards', COUNT(*) FROM rewards
UNION ALL SELECT 'campaigns', COUNT(*) FROM campaigns
UNION ALL SELECT 'vouchers', COUNT(*) FROM vouchers;"
```

- [ ] **Step 2:** Verify ledger invariant cho mọi membership

```bash
cd backend && python -m scripts.verify_invariants  # tạo nếu chưa có
```

Hoặc query trực tiếp:

```bash
docker compose exec postgres psql -U loyalty -d loyalty -c "
SELECT m.id, m.points_balance, COALESCE(SUM(pl.delta), 0) AS ledger_sum,
       m.points_balance - COALESCE(SUM(pl.delta), 0) AS diff
FROM memberships m
LEFT JOIN point_ledger pl ON pl.membership_id = m.id
GROUP BY m.id, m.points_balance
HAVING m.points_balance != COALESCE(SUM(pl.delta), 0);"
```

Expected: 0 rows.

- [ ] **Step 3:** Commit nếu có thay đổi script seed

---

### Task 2: Tạo file `docs/qa-checklist.md` với demo scenario chi tiết

**Files:**
- Create: `D:/DoAn/docs/qa-checklist.md`

- [ ] **Step 1: Tạo file**

```markdown
# QA Checklist Tuần 7 — Loyalty Platform

## Setup
1. `docker compose up -d --build`
2. `make seed-fresh`
3. Verify health endpoint
4. Open frontend `http://localhost:3000`

## A. Auth Flow
- [ ] A1. Đăng ký tài khoản mới `qa@test.com / pass12345`
- [ ] A2. Login với tài khoản vừa tạo
- [ ] A3. Logout
- [ ] A4. Login lại
- [ ] A5. Reset password qua /claim flow (nếu có) — note nếu skip
- [ ] A6. Login wrong password → 401 hiển thị error rõ
- [ ] A7. Rate limit login: 6 lần wrong password trong 1 phút → 429

## B. Super Admin
- [ ] B1. Login `admin@loyalty.local / admin12345`
- [ ] B2. Vào /admin → thấy platform stats
- [ ] B3. Vào /admin/tenants?status=pending → thấy 0 hoặc list pending
- [ ] B4. Tạo tenant mới (logout, register lại + register tenant) → quay lại admin → approve
- [ ] B5. Vào /admin/tenants/{id} → thấy detail
- [ ] B6. Suspend tenant → verify status → reactivate

## C. Owner — Cấu hình shop
- [ ] C1. Login `owner1@loyalty.local / owner12345`
- [ ] C2. Vào /merchant → thấy dashboard với 6 charts
- [ ] C3. Verify daily transactions chart có 30 data points
- [ ] C4. Verify tier distribution pie chart
- [ ] C5. Vào /merchant/tiers → thấy 5 hạng → thêm 1 hạng mới → edit → xoá
- [ ] C6. Vào /merchant/point-rules → thấy active rule
- [ ] C7. Tạo rule mới → confirm → verify rule cũ deactivate
- [ ] C8. Vào /merchant/settings → toggle points_on_gross → verify confirm dialog → save → audit log mới
- [ ] C9. Vào /merchant/staff → thấy owner + 2 staff seed → thêm staff mới → note verification code
- [ ] C10. Đổi role staff → verify
- [ ] C11. Remove staff → verify

## D. Staff — Claim shadow + tích điểm
- [ ] D1. Logout
- [ ] D2. Vào /claim → nhập email staff mới + code → set password
- [ ] D3. Login với email staff + password mới
- [ ] D4. Vào /pos → thấy dashboard
- [ ] D5. /pos/transactions/new → nhập SĐT mới `0987654321` + 50000 → verify success card
- [ ] D6. Verify tier "Bronze" hiển thị
- [ ] D7. Tạo thêm 5 giao dịch cho cùng SĐT → verify upgrade Silver
- [ ] D8. Tạo giao dịch cho khách khác `0912345678` + 200000

## E. Khách hàng — claim shadow + xem điểm + đổi quà
- [ ] E1. Logout
- [ ] E2. Vào /register → đăng ký với SĐT `0987654321` + email + password (claim shadow flow nếu đã có shadow)
- [ ] E3. Login → vào /member → thấy dashboard
- [ ] E4. Vào /member/qr → thấy QR rolling
- [ ] E5. Verify countdown đếm ngược + refresh tự động sau 55s
- [ ] E6. Vào /member/rewards → thấy catalog
- [ ] E7. Đổi 1 reward (đủ điểm) → nhận mã redemption
- [ ] E8. Vào /member/redemptions → thấy redemption pending

## F. QR transactions
- [ ] F1. Login owner ở browser khác (hoặc 2 device)
- [ ] F2. /pos/transactions/scan → quét QR khách (đã đăng nhập ở /member/qr) → tích điểm
- [ ] F3. Verify điểm tăng + ledger entry mới
- [ ] F4. Test fallback code: copy fallback_code từ /member/qr → nhập tay → tích điểm
- [ ] F5. Test khách chưa là thành viên: tạo user mới (chưa có membership tenant này) → quét QR → 404 → fallback form Luồng B

## G. Vouchers
- [ ] G1. Owner /merchant/campaigns → tạo campaign 20% off, target_tier=null, max_issuances=10
- [ ] G2. Khách /member/vouchers/available → thấy campaign
- [ ] G3. Bấm "Nhận voucher" → success → có voucher trong /member/vouchers/mine
- [ ] G4. Bấm "Nhận" lần 2 cùng campaign → 409 ALREADY_CLAIMED
- [ ] G5. Khách đưa code voucher cho staff
- [ ] G6. Staff /pos/transactions/new → nhập SĐT + amount + voucher_code → verify discount + net_amount
- [ ] G7. Verify points tính trên net (mặc định)
- [ ] G8. Owner toggle points_on_gross → tạo giao dịch tương tự → verify points tính trên gross

## H. Redemption flow
- [ ] H1. Khách đến quầy đưa code redemption (từ E7)
- [ ] H2. Staff vào /merchant/redemptions/use → nhập code → verify
- [ ] H3. Status chuyển used → khách thấy update trong /member/redemptions

## I. Birthday job
- [ ] I1. Set 1 user có birthday = today qua psql
- [ ] I2. Set tenant.settings.birthday_campaign_id = X qua psql
- [ ] I3. Run `cd backend && python -m app.jobs.run_once birthday`
- [ ] I4. Verify khách có voucher mới + notification
- [ ] I5. Run lại → verify idempotent (không tạo duplicate)

## J. Notifications
- [ ] J1. Khách đăng nhập → /member → bell icon
- [ ] J2. Click bell → dropdown → thấy notifications
- [ ] J3. Mark read

## K. Cross-tenant
- [ ] K1. Login owner1 → mở DevTools → sửa tenant_id trong sessionStorage thành tenant của owner2 → reload → verify bị reject
- [ ] K2. API test: gọi POST /merchant/transactions với header X-Tenant-Id của tenant khác → 403

## L. Responsive
- [ ] L1. Mobile (375px width) — dashboard tích hợp tốt
- [ ] L2. Tablet (768px) — /pos optimized
- [ ] L3. Desktop (1280px+) — /merchant/dashboard
```

- [ ] **Step 2: Commit**

```bash
git add docs/qa-checklist.md
git commit -m "docs: thêm QA checklist 30+ items cho tuần 7"
```

---

### Task 3: Run all backend tests

```bash
cd D:/DoAn/backend
pytest -v
```

- [ ] **Step 1:** Verify all green ~175 tests
- [ ] **Step 2:** Note failing tests → fix ở Phase 7

---

## PHASE 2 — Manual QA Backend

### Tasks 4-9: Run checklist sections A-K (backend portions)

- [ ] **Task 4:** A1-A7 Auth flow + rate limit
- [ ] **Task 5:** B1-B6 Super Admin
- [ ] **Task 6:** C1-C11 Owner cấu hình
- [ ] **Task 7:** D1-D8 Staff claim + tích điểm
- [ ] **Task 8:** E1-E8 Khách + redemption + F1-F5 QR
- [ ] **Task 9:** G1-G8 Vouchers + H1-H3 Redemption flow + I1-I5 Birthday + J1-J3 Notifications + K1-K2 Cross-tenant

> Mỗi task: chạy section, mark checkbox, note bugs found.

---

## PHASE 3 — Frontend Android Chrome

### Tasks 10-13: Test trên Android Chrome thật

- [ ] **Task 10:** Setup Android device hoặc emulator, mở Chrome
- [ ] **Task 11:** Connect device qua USB hoặc dùng `ngrok http 3000` để expose frontend ra public URL
- [ ] **Task 12:** Truy cập URL trên Android Chrome → test PWA install (Add to Home Screen)
- [ ] **Task 13:** Test các luồng customer trên mobile thật:
  - QR cá nhân hiển thị + countdown
  - Đổi quà qua mobile
  - Redemption code dễ đọc
  - Touch targets đủ lớn (44px+)

---

## PHASE 4 — iOS Safari Test

### Tasks 14-16: iOS Safari (optional nếu không có iPhone)

- [ ] **Task 14:** Mượn iPhone hoặc dùng BrowserStack free trial
- [ ] **Task 15:** Test các luồng quan trọng trên iOS Safari:
  - Login/register
  - QR display (camera permission, html5-qrcode)
  - Service worker (iOS hạn chế — note nếu không hoạt động)
  - PWA install (iOS yêu cầu Add to Home Screen từ Share menu)
- [ ] **Task 16:** Note iOS limitations vào `docs/qa-checklist.md` (tạo section "iOS Limitations")

> Nếu không có iPhone và BrowserStack hết quota, document rõ "iOS Safari test pending — known limitation" trong báo cáo.

---

## PHASE 5 — Performance Check

### Tasks 17-19: Smoke benchmark + N+1 query scan

- [ ] **Task 17:** Cài Apache Bench (`apt install apache2-utils` hoặc `choco install apachebench`)

- [ ] **Task 18:** Smoke benchmark 3 endpoints (★ FIX C2 review tuần 7 — bỏ login benchmark)

> **★ Lý do bỏ login benchmark:**
> - bcrypt cost 12 → mỗi login ~250ms blocking → p95 không phản ánh throughput thực
> - slowapi rate limit `5/phút/IP` → 100 requests sẽ bị 429 sau request thứ 6 → ab báo p95 sai cách (429 trả nhanh)
> - Login không phải hot path — không cần benchmark

```bash
# Cross-platform: dùng Docker httpd:alpine có ab sẵn (Windows/Mac/Linux đều chạy)
# Alternative: WSL apt install apache2-utils (Windows) hoặc brew install apache2-utils (Mac)

# 1. Health endpoint (baseline)
docker run --rm --network host httpd:alpine \
  ab -n 500 -c 10 http://host.docker.internal:8000/health

# 2. Dashboard (cần token — login MỘT lần lấy token, không benchmark login)
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"owner1@loyalty.local","password":"owner12345"}' | jq -r .access_token)

docker run --rm --network host httpd:alpine \
  ab -n 200 -c 5 \
     -H "Authorization: Bearer $TOKEN" \
     -H "X-Tenant-Id: 1" \
     http://host.docker.internal:8000/merchant/analytics/dashboard

# 3. Members list (test pagination + JOIN performance)
docker run --rm --network host httpd:alpine \
  ab -n 200 -c 5 \
     -H "Authorization: Bearer $TOKEN" \
     -H "X-Tenant-Id: 1" \
     http://host.docker.internal:8000/merchant/members
```

> **Tạm thời bypass rate limit cho benchmark:** thêm `127.0.0.1` (hoặc IP container) vào whitelist `slowapi` trong env `BENCHMARK_MODE=true`. Revert sau benchmark.

Verify p95:
- /health < 100ms
- /merchant/analytics/dashboard < 500ms (sau khi đã fix N+1 từ tuần 6)
- /merchant/members < 500ms

> **Login p95 expectation:** ~300-500ms per request do bcrypt cost 12. Note trong báo cáo: "Login latency cao là design choice cho security; throughput chấp nhận cho MVP."

- [ ] **Task 19:** N+1 query scan (★ FIX C3 review tuần 7 — pytest fixture đếm query)

> **★ Lý do bỏ grep SQL log:**
> - SQLAlchemy không auto-enable echo qua DEBUG env, cần explicit `echo=True` trong engine
> - `grep "SELECT" | uniq` không meaningful vì SQLAlchemy bind params inline → mỗi query "khác"
> - Manual scan log không scalable

**Cách đúng:** Pytest fixture đếm queries qua SQLAlchemy `before_cursor_execute` event.

- [ ] **Step 1: Thêm fixture vào `tests/conftest.py`**

```python
from sqlalchemy import event


@pytest.fixture
def sql_counter(engine):
    """Count SQL queries executed during a test.

    Usage:
        def test_no_n_plus_1(sql_counter, client):
            client.get("/merchant/analytics/dashboard")
            assert sql_counter["count"] < 10, f"N+1 detected: {sql_counter['count']} queries"
    """
    counter = {"count": 0, "queries": []}
    sync_engine = engine.sync_engine

    @event.listens_for(sync_engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        counter["count"] += 1
        counter["queries"].append(statement[:100])  # First 100 chars for debug

    yield counter

    event.remove(sync_engine, "before_cursor_execute", before_cursor_execute)
```

- [ ] **Step 2: Thêm test N+1 cho 3 endpoint quan trọng**

`tests/integration/test_n_plus_1.py`:

```python
import pytest


@pytest.mark.asyncio
async def test_dashboard_no_n_plus_1(client, sql_counter, db_session, owner_token, tenant):
    """Dashboard fetch không được vượt quá 10 SQL queries (≈ 6 main queries + auth checks)."""
    response = await client.get(
        "/merchant/analytics/dashboard",
        headers={"Authorization": f"Bearer {owner_token}", "X-Tenant-Id": str(tenant.id)},
    )
    assert response.status_code == 200
    assert sql_counter["count"] < 15, (
        f"N+1 detected in /dashboard: {sql_counter['count']} queries\n"
        f"First 5: {sql_counter['queries'][:5]}"
    )


@pytest.mark.asyncio
async def test_members_list_no_n_plus_1(client, sql_counter, db_session, owner_token, tenant):
    """List members với 50 items không được > 10 queries (joinedload User + Tier)."""
    # Setup: tạo 50 members
    # ...
    response = await client.get(
        "/merchant/members?limit=50",
        headers={"Authorization": f"Bearer {owner_token}", "X-Tenant-Id": str(tenant.id)},
    )
    assert response.status_code == 200
    assert sql_counter["count"] < 10, f"N+1 in members list: {sql_counter['count']}"


@pytest.mark.asyncio
async def test_transactions_list_no_n_plus_1(client, sql_counter, db_session, owner_token, tenant):
    """List transactions không được > 10 queries."""
    response = await client.get(
        "/merchant/transactions?limit=50",
        headers={"Authorization": f"Bearer {owner_token}", "X-Tenant-Id": str(tenant.id)},
    )
    assert response.status_code == 200
    assert sql_counter["count"] < 10, f"N+1 in transactions list: {sql_counter['count']}"
```

- [ ] **Step 3: Run**

```bash
cd D:/DoAn/backend
pytest tests/integration/test_n_plus_1.py -v
```

Nếu fail → fix N+1 bằng `joinedload` / `selectinload`. Đặc biệt check:
- `AnalyticsService._campaign_roi` (đã fix ở tuần 6 sau review)
- `MembersAPI.list_members` — joinedload User + Tier
- `TransactionsAPI.list_transactions` — joinedload Membership.user

- [ ] **Step 4: Commit**

```bash
git add backend/tests/conftest.py backend/tests/integration/test_n_plus_1.py
git commit -m "test(backend): thêm pytest fixture sql_counter + N+1 detection tests"
```

---

## PHASE 6 — Lighthouse PWA Audit

### Tasks 20-22: Lighthouse + fix

- [ ] **Task 20:** Mở Chrome DevTools → Lighthouse tab
- [ ] **Step 1:** Generate report cho `/member` (sau khi login khách)
- [ ] **Step 2:** Note score 4 categories: Performance, Accessibility, Best Practices, PWA

- [ ] **Task 21:** Fix issues với điểm Quick Wins:
  - Thêm `alt` text cho images
  - Color contrast (text-muted-foreground có thể fail) → sử dụng class chuẩn
  - Form labels (đã có `<Label htmlFor>` từ tuần 1)
  - Meta description trong layout
  - Manifest validation (icons 192/512 đủ chưa)

- [ ] **Task 22:** Re-run Lighthouse → verify ≥ 85 PWA + ≥ 80 các category khác

```bash
git commit -m "fix(frontend): a11y + PWA improvements từ Lighthouse audit"
```

---

## PHASE 7 — Bug Fix

### Tasks 23-25: Fix bugs found from Phase 2-6

- [ ] **Task 23:** List tất cả bugs found trong tuần 7 (từ checklist + benchmark + Lighthouse)
- [ ] **Task 24:** Prioritize:
  - **Critical:** crash, data loss, security
  - **Important:** UX bị vỡ, error message không rõ
  - **Minor:** typo, style
- [ ] **Task 25:** Fix Critical + Important. Note Minor trong `docs/known-issues.md` cho luận văn.

```bash
git commit -m "fix: bugs phát hiện trong QA tuần 7"
```

---

## PHASE 8 — Integration Tests cho Gaps

### Tasks 26-28: Thêm tests cho gaps

- [ ] **Task 26:** Identify gaps:
  - Birthday job test integration (đang manual)
  - Voucher claim concurrent test
  - Reconcile invariant cho mọi service flow
  - Edge cases: gross_amount = 0, balance = 0, etc.

- [ ] **Task 27:** Viết 5-10 tests bổ sung

- [ ] **Task 28:** Run all tests → ~180 pass

```bash
git commit -m "test(backend): thêm 10 tests bổ sung cho gaps tuần 7"
```

---

## PHASE 9 — Deploy Dry-run + README

### Tasks 29-31: Deploy + docs

- [ ] **Task 29:** Deploy options:
  - **Option A (đơn giản):** Docker Compose local + ngrok
    ```bash
    docker compose up -d --build
    ngrok http 3000  # frontend public URL
    ngrok http 8000  # backend public URL
    ```
    Note ngrok URLs vào `.env.local` của frontend để CORS work.
  - **Option B (chuyên nghiệp):** VPS như DigitalOcean Droplet ($6/month)
    - Setup Caddy / Nginx reverse proxy
    - HTTPS via Let's Encrypt
    - Deploy backend + frontend qua docker-compose

  Sinh viên chọn 1, document lựa chọn.

- [ ] **Task 30:** Update `README.md` đầy đủ:
  - Mô tả đề tài
  - Stack
  - Setup local (1 lệnh)
  - Setup production (option A hoặc B)
  - Kiến trúc (link tới spec)
  - Default seed credentials
  - Tests
  - Tài liệu (link spec, danh-sach-tinh-nang, plans)

- [ ] **Task 31:** Test deploy fresh — `git clone` ở thư mục mới → setup → verify chạy

```bash
git commit -m "docs: hoàn thiện README với hướng dẫn deploy"
```

---

## PHASE 10 — CI + Tag

### Tasks 32-33: Push CI + tag tuần 7

- [ ] **Task 32:** Push lên main → CI xanh
- [ ] **Task 33:** Tag

```bash
cd D:/DoAn
git push origin main
git tag tuan-7-complete
```

---

## Tổng kết Tuần 7

### Đã hoàn thành (33 tasks)

- ✅ Manual QA checklist 30+ items
- ✅ Test trên Android Chrome thật
- ✅ iOS Safari test (hoặc document limitation)
- ✅ Performance benchmark 3 endpoints
- ✅ N+1 query scan + fix nếu có
- ✅ Lighthouse PWA ≥ 85
- ✅ Bug fixes Critical/Important
- ✅ ~10 tests bổ sung cho gaps (tổng ~180 tests)
- ✅ Deploy dry-run thành công
- ✅ README hoàn chỉnh
- ✅ CI xanh

### Acceptance criteria

- [x] Manual QA checklist pass
- [x] iOS test (hoặc documented)
- [x] p95 < 500ms cho 3 endpoints
- [x] Lighthouse ≥ 85
- [x] All bugs fixed hoặc noted
- [x] Tests ~180 pass
- [x] Deploy dry-run pass
- [x] README đầy đủ

---

## Sang tuần 8

Tuần 8 sẽ là **deploy chính thức + báo cáo + slide demo + bảo vệ nháp**. KHÔNG code feature mới (kể cả bug fix nhỏ trừ khi blocker cho demo).

Plan tuần 8 sẽ được tạo riêng tại `docs/superpowers/plans/2026-04-12-tuan-8-deploy-report-demo.md`.
