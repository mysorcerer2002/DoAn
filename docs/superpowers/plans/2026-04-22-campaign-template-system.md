# Campaign Template System — Admin-managed Templates + Approval Workflow

> **Ngày lập:** 2026-04-22
> **Scope:** Backend + Frontend (admin + merchant), migration, seed, smoke test.
> **Dự kiến LOC:** ~1400 backend · ~1700 frontend · ~10 test mới.

## 1. Goal

Thay đổi mô hình tạo campaign:

- **Trước:** shop (merchant) tạo campaign tự do (`POST /merchant/campaigns`) — không kiểm soát mức giảm, thời gian, chi phí, tuân thủ pháp lý.
- **Sau:**
  1. **Admin (công ty)** quản lý **kho template** — định nghĩa sẵn loại campaign (welcome / birthday / manual), `discount_type`, `default_usage_guide`, và các **cap** (trần discount, trần số lượng phát hành).
  2. **Shop** chọn template → điền: thời gian, `discount_value`, `max_issuances`, điều lệ (`description`), điều khoản (`terms`) → hệ thống **tính chi phí dự kiến** → quyết định `auto_approved` hoặc **`pending_approval`** (nếu cost vượt ngưỡng thuế / pháp lý).
  3. **Admin review** campaign trong mục "chờ duyệt" với hồ sơ thông báo Sở Công Thương đính kèm.

## 2. Cơ sở pháp lý (tóm lược để justify threshold)

| Văn bản | Điểm đáng chú ý |
|---|---|
| Luật Thương mại 2005 (Điều 88-101) | Mức giảm giá tối đa **50%** giá bán thông thường (Điều 94). |
| Nghị định 81/2018/NĐ-CP | Khuyến mại giảm giá / tặng phiếu → **thông báo Sở Công Thương** trước ≥3 ngày làm việc (Điều 17). Khuyến mại mang tính may rủi hoặc phạm vi ≥2 tỉnh → **đăng ký Cục XTTM** (Điều 19). |
| NĐ 81/2018 Điều 6 | Tổng giá trị hàng hoá khuyến mại trong 1 chương trình **≤50%** giá trị hàng hoá thực tế (trừ đợt tập trung). |
| Luật thuế TNDN sửa đổi 2014 | Bỏ trần 15% cho chi phí khuyến mại; chi phí được trừ **nếu có chứng từ hợp lệ & chương trình đã thông báo/đăng ký với Sở CT**. |
| Thông tư 07/2019/TT-BCT | Biểu mẫu thông báo/đăng ký khuyến mại. |
| NĐ 81/2018 Điều 21 | Báo cáo kết thúc chương trình trong **45 ngày** sau khi kết thúc. |

**Kết luận cho system:**
- Hard-cap kỹ thuật: `discount_value ≤ 50%` (percent) — enforce ở Pydantic.
- Ngưỡng approval dựa trên `estimated_cost` để bảo đảm shop có hồ sơ thuế hợp lệ khi chi phí lớn.
- Scope đồ án: giữ 1-tỉnh, không làm đăng ký may rủi / multi-tỉnh; khi vượt ngưỡng chỉ yêu cầu shop confirm đã thông báo Sở CT + upload text/URL chứng từ.

## 3. Assumptions & defaults (do user chưa trả lời 6 câu hỏi confirm — ghi rõ để reviewer/user ack)

| # | Quyết định | Giá trị chọn | Có thể user thay đổi |
|---|---|---|---|
| A1 | Approval threshold | 3 tier: `≤ 1 triệu` auto; `1M–10M` notify_dct (phải confirm đã thông báo Sở CT); `>10M` full_dossier (phải upload chứng từ) | Config qua `admin_settings` bảng mới hoặc `.env` — phase 1 hardcode, phase 8 cho admin đổi |
| A2 | Mapping field shop điền | "điều lệ" → `campaigns.description`; "điều khoản" → `campaigns.terms` | Không đổi (DB đã có sẵn 2 cột) |
| A3 | Legacy campaigns (đã tạo bằng API cũ) | Giữ nguyên; `template_id=NULL`, `approval_status='auto_approved'` (backfill migration); flow merchant CRUD tự do **bị xoá** không migrate dữ liệu cũ | User có thể chọn giữ endpoint cũ cho admin override |
| A4 | Template delete-policy | Soft delete (`deleted_at`); campaign đang dereference vẫn chạy; admin không thấy template bị soft-deleted trong dropdown | — |
| A5 | Upload chứng từ `pending_approval` | Phase 1: lưu URL text (shop paste link Google Drive / công văn số). Phase rộng hơn (ngoài scope): upload file thực tới S3. | Sau phase 1 quyết |
| A6 | Estimated cost cho percent + không có `max_discount` | Bắt buộc template set `max_discount_value_cap`; nếu shop nhập `max_discount > cap` → reject validation | — |
| A7 | Birthday campaign | Vẫn tồn tại cơ chế `tenants.settings.birthday_campaign_id` — sau khi có template system, shop enroll template `source=birthday` sẽ set luôn field này nếu chưa có | User ack |

**Nếu user muốn thay đổi** → update plan trước khi execute phase 1.

## 4. Architecture

### 4.1 DB shape

**Bảng mới:** `campaign_templates`

| Cột | Type | Null | Ghi chú |
|---|---|---|---|
| id | INT PK | | |
| code | VARCHAR(40) UNIQUE | | slug admin-facing (vd `welcome-10pct-20k`) |
| name | VARCHAR(120) | | Vietnamese display |
| description | TEXT | ✓ | admin note |
| source | ENUM(manual, birthday, signup) | | map trực tiếp sang `Campaign.source` |
| discount_type | ENUM(percent, fixed) | | |
| default_usage_guide | TEXT | | shop không sửa khi enroll — lấy từ đây chép sang `campaigns.usage_guide` |
| default_support_contact | VARCHAR(200) | ✓ | |
| max_discount_percent_cap | INT | ✓ | Trần `discount_value` khi type=percent (1-50) |
| max_discount_value_cap | INT | ✓ | Trần `max_discount/voucher` khi type=percent (VND) |
| max_discount_fixed_cap | INT | ✓ | Trần `discount_value` khi type=fixed (VND) |
| min_order_floor | INT | ✓ | Sàn `min_order` shop bắt buộc (bảo vệ tỉ lệ ≤50%) |
| max_issuances_cap | INT | ✓ | Trần số voucher shop được phát (NULL=unlimited) |
| max_duration_days | INT | ✓ | Trần độ dài campaign (NULL=unlimited) |
| is_active | BOOL | | admin ẩn/hiện template |
| created_at, deleted_at | TIMESTAMP | | soft delete |

**Alter bảng `campaigns`:**

| Cột mới | Type | Null | Ghi chú |
|---|---|---|---|
| template_id | INT FK → campaign_templates.id | ✓ | NULL cho legacy |
| approval_status | ENUM(auto_approved, pending_approval, approved, rejected) | | default `auto_approved` cho backfill |
| approval_tier | ENUM(none, notify_dct, full_dossier) | | default `none` |
| estimated_cost | BIGINT | | snapshot tại lúc enroll (VND) |
| submitted_docs | JSONB | ✓ | `[{type, url, note, submitted_at}]` |
| reviewed_by_user_id | INT FK → users.id | ✓ | |
| reviewed_at | TIMESTAMP | ✓ | |
| rejection_reason | TEXT | ✓ | |

**Hiển thị / hiệu lực:** campaign chỉ được query public/voucher-claimable khi `approval_status IN ('auto_approved', 'approved')` — thêm filter này vào mọi SELECT hiện có trong `VoucherService`, `CampaignService.list`.

### 4.2 Approval logic

```
estimated_cost = calc_cost(discount_type, discount_value, max_discount, max_issuances)

if discount_type == 'fixed':
    per_voucher = discount_value
else:  # percent
    per_voucher = max_discount  # bắt buộc set khi percent
estimated_cost = per_voucher * max_issuances

if estimated_cost <= AUTO_APPROVE_THRESHOLD:          # 1_000_000
    approval_status = 'auto_approved'
    approval_tier = 'none'
elif estimated_cost <= NOTIFY_DCT_THRESHOLD:          # 10_000_000
    approval_status = 'pending_approval'
    approval_tier = 'notify_dct'
else:
    approval_status = 'pending_approval'
    approval_tier = 'full_dossier'
```

Với `pending_approval` + `notify_dct`: shop phải gửi URL văn bản thông báo Sở CT (textarea) khi enroll.
Với `full_dossier`: shop phải gửi tối thiểu 2 link (thông báo + điều lệ chi tiết).

### 4.3 Backend service boundaries

```
CampaignTemplateService (admin-only):
    - list(include_deleted, is_active_filter)
    - get(id)
    - create(payload)
    - update(id, payload)
    - soft_delete(id)

CampaignEnrollmentService (merchant):
    - enroll(tenant_id, user_id, payload) -> Campaign
        · validate payload vs template cap
        · calculate estimated_cost
        · determine approval_status/tier
        · create Campaign (copy usage_guide/support_contact from template)
        · raise CampaignCapExceededError, CampaignValidationError

CampaignApprovalService (admin-only):
    - list_pending()
    - approve(campaign_id, admin_user_id)
    - reject(campaign_id, admin_user_id, reason)
```

Chỉnh `CampaignService.list`: filter `approval_status` cho non-admin view.
**Xoá** endpoint `POST /merchant/campaigns` (tạo tự do), thay bằng `POST /merchant/campaigns/enroll`. Giữ `GET /merchant/campaigns` + `PATCH/DELETE` (shop vẫn cần xem/tắt).

### 4.4 Frontend routing

```
/admin/campaign-templates         — CRUD list
/admin/campaign-templates/new     — create
/admin/campaign-templates/[id]    — edit + soft delete
/admin/campaigns/pending          — approval queue (list + detail + approve/reject)
/merchant/campaigns               — list (giữ nguyên)
/merchant/campaigns/enroll        — chọn template + form điền
/merchant/campaigns/[id]          — detail (giữ nguyên, bổ sung approval badge)
```

## 5. Phases & task breakdown

| Phase | Task | Commit |
|---|---|---|
| 1 | Migration `019_campaign_templates.py` + alter campaigns | `feat(campaign-tpl): schema + migration` |
| 2 | Model `CampaignTemplate` + alter `Campaign` + schemas | (cùng commit phase 1) |
| 3 | `CampaignTemplateService` + admin API `/admin/campaign-templates` CRUD | `feat(admin): campaign template CRUD API` |
| 4 | `CampaignEnrollmentService.enroll` + API `/merchant/campaigns/enroll` + cost calc + approval determination | `feat(merchant): enroll campaign từ template` |
| 5 | Xoá endpoint tạo tự do; update `CampaignService.list` filter approval_status; update `VoucherService.claim` filter | (cùng commit phase 4) |
| 6 | `CampaignApprovalService` + API `/admin/campaigns/pending`, `POST /admin/campaigns/{id}/approve`, `.../reject` | `feat(admin): approval queue campaign` |
| 7 | Seed `scripts/seed_campaign_templates.py` (3 template: welcome-10pct / birthday-50k-fixed / manual-flash-20pct) + chạy docker seed | `chore(seed): 3 campaign template mặc định` |
| 8 | Frontend `/admin/campaign-templates` (list + form) | `feat(admin-ui): trang quản lý campaign template` |
| 9 | Frontend `/merchant/campaigns/enroll` (template picker + form + cost preview live) | `feat(merchant-ui): enroll campaign từ template` |
| 10 | Frontend `/admin/campaigns/pending` (approval queue) + badge trên `/merchant/campaigns` | `feat(admin-ui): queue duyệt campaign + badge pending` |
| 11 | Smoke test E2E qua `docker exec`: admin tạo template → shop enroll auto-approve → shop enroll vượt ngưỡng → admin approve → voucher claim | `chore(smoke): E2E campaign template system` |
| 12 | Test: unit cho cost calc + threshold; integration cho enroll cap validation | `test(campaign-tpl): cost calc + cap validation` |

**Tổng:** 12 phase → **12 commits** (một số gộp cùng PR logic như ghi chú).

## 6. File structure

```
backend/alembic/versions/
└── 019_campaign_templates.py             # new

backend/app/
├── models/
│   ├── campaign_template.py              # new
│   └── campaign.py                       # +template_id, +approval_*, +estimated_cost, +submitted_docs, +reviewed_*
├── schemas/
│   ├── campaign_template.py              # new — CreateReq, UpdateReq, Response
│   └── campaign.py                       # +EnrollRequest, +ApprovalAction, +field approval_* trong Response
├── services/
│   ├── campaign_template_service.py      # new
│   ├── campaign_enrollment_service.py    # new (enroll + cost calc)
│   ├── campaign_approval_service.py      # new
│   └── campaign_service.py               # +filter approval_status
├── api/
│   ├── admin_campaign_templates.py       # new (admin-only)
│   ├── admin_campaign_approval.py        # new (admin-only)
│   └── merchant_campaigns.py             # xoá POST tạo tự do, thêm POST /enroll
├── core/
│   └── config.py                         # +CAMPAIGN_AUTO_APPROVE_THRESHOLD, +CAMPAIGN_NOTIFY_DCT_THRESHOLD
└── jobs/
    └── birthday_voucher.py               # không đổi, nhưng doc note: yêu cầu template.source=birthday khi set tenants.settings.birthday_campaign_id

backend/scripts/
└── seed_campaign_templates.py            # new

backend/tests/
├── unit/
│   └── test_cost_calc.py                 # new
└── integration/
    ├── test_campaign_template_admin.py   # new
    ├── test_campaign_enrollment.py       # new
    └── test_campaign_approval.py         # new

frontend/src/
├── types/merchant.ts                     # +CampaignTemplate*, +CampaignEnrollRequest, +approval fields
├── lib/
│   ├── api-admin.ts                      # +adminCampaignTemplateApi, +adminCampaignApprovalApi
│   ├── api-merchant.ts                   # update merchantCampaignApi: remove create-free, add enroll
│   └── hooks/
│       ├── use-admin-campaign-templates.ts  # new
│       ├── use-admin-campaign-approval.ts   # new
│       └── use-merchant-campaigns.ts        # update
├── app/(admin)/admin/
│   ├── campaign-templates/page.tsx       # new — list
│   ├── campaign-templates/new/page.tsx   # new
│   ├── campaign-templates/[id]/page.tsx  # new — edit
│   └── campaigns/pending/page.tsx        # new — approval queue
└── app/(merchant)/merchant/campaigns/
    ├── page.tsx                          # update: thay nút "Tạo mới" → "Đăng ký từ kho mẫu"; thêm badge approval
    └── enroll/page.tsx                   # new — template picker + form + cost preview
```

## 7. Acceptance criteria

1. **Migration** chạy `alembic upgrade head` sạch trên prod DB; backfill tất cả `campaigns` hiện có → `approval_status='auto_approved'`, `template_id=NULL`.
2. **Admin CRUD template** hoạt động: POST/PATCH/DELETE `/admin/campaign-templates` cần `require_super_admin`; soft-delete không xoá template có campaign dereference.
3. **Merchant enroll**:
   - `POST /merchant/campaigns/enroll` với `{template_id, starts_at, ends_at, discount_value, max_discount, min_order, max_issuances, description, terms, submitted_docs}` → tạo campaign.
   - Vi phạm cap (discount_value > cap, max_issuances > cap, duration > cap, min_order < floor) → 422 với message Vietnamese rõ field nào vi phạm.
   - `estimated_cost` trả về trong response.
4. **Approval threshold**:
   - Cost ≤ 1M → `auto_approved` ngay, voucher claimable.
   - 1M < Cost ≤ 10M → `pending_approval`, tier `notify_dct`, bắt buộc `submitted_docs` có ≥1 entry; voucher **không** claimable.
   - Cost > 10M → `pending_approval`, tier `full_dossier`, bắt buộc `submitted_docs` có ≥2 entry.
5. **Admin approve/reject**:
   - `POST /admin/campaigns/{id}/approve` → `approval_status='approved'`, ghi `reviewed_by`, `reviewed_at`.
   - `POST /admin/campaigns/{id}/reject` với `reason` → `approval_status='rejected'`, voucher **không** claimable; shop thấy lý do.
6. **Voucher claim lọc approval**: `VoucherService.claim` với campaign `pending_approval` / `rejected` → 404 `CAMPAIGN_NOT_ELIGIBLE`.
7. **Frontend**:
   - `/admin/campaign-templates` hiển thị bảng, modal tạo, edit, soft-delete.
   - `/merchant/campaigns/enroll` — chọn template (grid card) → form các field → **cost preview live** khi user gõ (không chờ submit).
   - `/admin/campaigns/pending` — bảng chờ duyệt + detail modal với submitted_docs + nút Approve / Reject.
   - `/merchant/campaigns` — badge theo approval_status (xanh/vàng/đỏ).
8. **Smoke test** (docker exec script):
   - Admin tạo template "welcome-10pct-20k" — percent cap 10%, value_cap 20k, issuances_cap 500.
   - Shop enroll: 100 issuances × 20k = 2M → `notify_dct` (pending). Enroll thiếu submitted_docs → 422.
   - Shop enroll với submitted_docs → tạo OK, pending.
   - Khách claim → 404 (not eligible).
   - Admin approve → khách claim OK.
   - Shop enroll: 50 issuances × 20k = 1M → auto_approved.
9. **Test pytest**: ≥10 test mới pass; CI xanh.

## 8. Rollout / migration plan

1. **Backfill** trong migration `019`:
   ```sql
   UPDATE campaigns
   SET approval_status = 'auto_approved',
       approval_tier   = 'none',
       estimated_cost  = 0
   WHERE approval_status IS NULL;
   ```
2. **Seed 3 template** bắt buộc chạy trước khi merchant dùng UI mới:
   - `welcome-10pct-20k` (source=signup)
   - `birthday-50k-fixed` (source=birthday)
   - `manual-flash-20pct` (source=manual)
3. **Xoá endpoint merchant tạo tự do** → frontend build sẽ fail nếu còn chỗ dùng → sửa luôn.
4. **Tài liệu** (optional, ngoài scope code): update `docs/danh-sach-tinh-nang.md` ghi chú feature mới.
5. **Không cần downtime**: migration thuần alter + add, không drop cột.

## 9. Rủi ro & mitigation

| Rủi ro | Mitigation |
|---|---|
| Legacy campaigns có `discount_value` vượt cap của template tương lai → không validate lại | Backfill `template_id=NULL` không bị enforce cap; chấp nhận technical debt |
| Shop enroll sai threshold vì cost calc nhầm cho percent (dùng `max_discount` chưa nhập) | Require `max_discount` khi template type=percent; validate ở schema |
| Admin quên duyệt → shop mất khách | Phase 10 UI hiển thị badge số lượng pending ở sidebar admin |
| Legal research chưa đủ (luật VN có thể đã cập nhật 2024-2026) | Ghi ngưỡng vào `settings` bảng admin để sau update không sửa code; note trong plan là "tham khảo, không tư vấn pháp lý" |
| Sửa `VoucherService.claim` phá test cũ | Chạy full `pytest -v` sau phase 4 |

## 10. Open questions (cần user confirm trước phase 1)

1. **Threshold số tiền** (1M auto / 10M notify_dct / >10M full) — OK cho scope đồ án, hay dùng con số khác để dễ demo (ví dụ 100k / 500k)?
2. **Upload chứng từ** — phase 1 chỉ lưu URL text có đủ cho demo không?
3. **Có cần giữ API tạo tự do cho admin override** (ví dụ tạo campaign đặc biệt không qua template) không? Mặc định plan **xoá hẳn**.
4. **Birthday campaign legacy** — shop nào đang dùng thì có cần bắt họ re-enroll qua template system không? Plan mặc định **không bắt** (legacy vẫn chạy).

---

## Next steps

Plan này chờ user confirm 4 open questions + 7 assumptions → sau đó code-reviewer review → execute từ phase 1.
