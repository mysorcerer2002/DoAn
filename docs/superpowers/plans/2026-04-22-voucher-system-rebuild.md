# Rebuild Hệ thống Voucher & Phát hành — Tuân thủ luật VN (v2)

> **Ngày lập:** 2026-04-22 · **Bản:** v2 (sau code-reviewer pass 1)
> **Scope:** Review tổng thể + rebuild models + chain nghiệp vụ **template → enroll → authorize → fee → file → approve → issuance → voucher → use** để tuân thủ Luật Thương mại 2005, NĐ 81/2018/NĐ-CP (+ NĐ 17/2020 sửa đổi), Luật Giao dịch điện tử 2023, Luật Kế toán 2015, NĐ 123/2020/NĐ-CP (hoá đơn điện tử).
> **Trạng thái:** Chờ user review v2 trước khi execute. Không code.

---

## 0. Trước khi đọc

Plan này **thay thế** và gộp luôn plan trước (`2026-04-22-campaign-template-system.md`) — không execute song song.

Plan **không phải tư vấn pháp lý** — citations pháp luật chỉ để thiết kế invariant kỹ thuật. Văn bản tham chiếu ở trạng thái hợp nhất **đến 2026-04-22**; luật VN thay đổi nhanh, doanh nghiệp thật khi triển khai cần luật sư kiểm tra lại.

**v2 changelog so với v1** (sau review bởi `superpowers:code-reviewer`):
- Sửa citation: Luật TM Điều 94 → **Điều 96**; bổ sung NĐ 81 Điều 7 (đợt tập trung), Điều 8/13 (hình thức khuyến mại), Điều 17 (thông báo) vs Điều 19 (đăng ký).
- Chọn **Option B**: bỏ `campaigns.issued_count` cache, thay bằng view `v_campaign_stats` (tránh deadlock với atomic UPDATE của `VoucherService.claim`).
- Cancel voucher khi reject: chỉ `status='issued'`, không đụng `status='used'`; warn admin + block ordering.
- Thêm `program_form` enum trên template (giam_gia / tang_kem / may_rui_quay_so / ...) → `approval_tier` tính từ form × cost (không phải chỉ cost).
- Thêm `ops_filing_started_at` trên campaigns → chặn revoke authorization khi ops đã bắt đầu nộp hồ sơ.
- Partial unique `(tenant_id, template_id) WHERE approval_status IN ('draft','pending_approval')` → chặn concurrent enroll.
- `discount_snapshot` JSONB: chỉ giữ field Campaign-owned + `terms_hash` (SHA-256); không duplicate `campaign_name`.
- `signature_payload` JSONB: thêm `consent_text_hash`, `otp_delivery_address`, `otp_attempts_count`, `session_id`, `rendered_pdf_hash`, `signed_at_server_clock`, `signed_at_client_clock`.
- Thêm section 12: retention 10 năm (Luật Kế toán 2015 Điều 41) + block delete-tenant.
- Thêm section 13: VAT/hoá đơn điện tử (NĐ 123/2020) — data model sẵn, tích hợp e-invoice ngoài scope v1.
- Soften claim Luật GDĐT: OTP email là evidence nội bộ shop–công ty, không thay thế chữ ký số VNeID/VNPT eSign.
- Migration safety: rõ ràng hoá thứ tự "add nullable → backfill → alter NOT NULL"; legacy campaign đã kết thúc → `post_report_submitted_at = NOW()` deemed-filed.
- **Scope trim v1**: bỏ framework authorization, multi-issuance batch, ops kanban, fee_schedules CRUD UI → còn ~16 commits / ~10 ngày (realistic).

**v2.2 (user scope decision 2026-04-22):**
- **`SERVICE_FEE_ENABLED = False`** ở đồ án — data model fee (bảng + cột) vẫn tạo cho khoá luận, nhưng UI + flow thu phí bị ẩn / bypass.
- Approve guard ở đồ án chỉ check `approval_status + authorization + regulatory_submissions`; bỏ check `service_fee_status`.
- Reject campaign không trigger refund flow (vì chưa charge).
- Merchant UI không hiển thị màn "Phí dịch vụ"; admin UI ẩn module fee management.
- Seed demo không tạo fee row; campaign demo bypass fee hoàn toàn.
- Authorization (OTP email sign uỷ quyền) **vẫn giữ** ở đồ án — là core compliance story.
- Bật lại ở khoá luận: đổi `SERVICE_FEE_ENABLED=True` + seed `campaign_fee_schedules` + unhide UI component.

**v2.1 (sau user review 2026-04-22):**
- **Fee refund flow** (E1): thêm enum `refunded` + `refund_requested_at/refunded_at/refund_reason` vào `campaign_service_fees`; trên reject campaign đã `paid` → tự động set fee về `refund_requested` + instruction manual cho kế toán (không tự refund tiền thật v1).
- **Atomic claim locking** (E2): nhấn mạnh `SELECT ... FOR NO KEY UPDATE` trên dòng campaign ở đầu transaction, hoặc `pg_advisory_xact_lock(hashtext('claim:'||campaign_id))` — không dựa vào READ COMMITTED snapshot.
- **FK purge safety** (E3): các FK `campaigns.authorization_id`, `campaigns.service_fee_status` (implicit qua `campaign_service_fees.campaign_id`) → khai báo `ON DELETE SET NULL` cho authorization FK; fee rows không hard-delete (Luật Kế toán giữ 10 năm).
- **Config thresholds chốt**: AUTO=500k / NOTIFY=2M (demo-friendly).
- **Post-report 45-day job**: v1 implement.
- **Retention purge job**: defer (cột `retention_until` vẫn tạo).
- **PDF rendering**: defer (HTML + SHA-256 đủ).
- **Notification cancel**: log-only + hiển thị status ở trang chi tiết voucher user.
- **Seed demo**: bắt buộc — `032_seed_demo_data.py` với shop × template × campaign ở nhiều trạng thái.

---

## 1. Gap Analysis — hệ thống hiện tại vs luật VN

Models hiện có (đã đọc):

| File | Cấu trúc hiện tại |
|---|---|
| `backend/app/models/campaign.py` | name, description, terms, usage_guide, support_contact, discount_type, discount_value, min_order, max_discount, target_tier_id, max_issuances, issued_count, starts_at, ends_at, is_active, source, soft delete |
| `backend/app/models/voucher.py` | tenant_id, campaign_id, membership_id, code (8), status (issued/used/expired), issued_at, used_at, expires_at; partial unique `(campaign, membership) WHERE status NOT IN ('used','expired')` |
| `backend/app/models/transaction.py` | gross/net/voucher_id/voucher_discount_amount, method, CHECK `net ≤ gross` |
| `backend/app/models/redemption.py` | đổi điểm lấy quà |

### 1.1 Gaps pháp lý (đã verify citation với reviewer)

| # | Vấn đề | Luật tham chiếu chính xác | Rủi ro |
|---|---|---|---|
| G1 | Không enforce discount percent ≤ 50% | **Luật TM 2005 Điều 96** (hạn mức tối đa) + **NĐ 81/2018 Điều 7** (100% chỉ trong đợt khuyến mại tập trung) | Shop tạo campaign giảm >50% → vi phạm |
| G2 | Không enforce tổng giá trị khuyến mại ≤ 50% giá trị hàng hoá ở transaction | NĐ 81/2018 Điều 6 | Voucher discount có thể > 50% `gross` |
| G3 | Không có cơ chế **approval / hồ sơ thuế** cho campaign chi phí lớn | NĐ 81/2018 + Luật TNDN sửa đổi 2014 | Không có chứng từ → không được khấu trừ thuế |
| G4 | Không có **template admin-managed** | Nghiệp vụ | Shop tự do đặt tên/cap → khó chuẩn hoá |
| G5 | Không phân biệt **thông báo** (Điều 17) và **đăng ký** (Điều 19) | NĐ 81/2018 Điều 17, 19 | Khuyến mại may rủi/đa tỉnh đi nhầm nhánh thông báo |
| G6 | Không có tracker báo cáo kết thúc chương trình | NĐ 81/2018 Điều 21 (45 ngày) | Quá hạn → phạt hành chính |
| G7 | `VoucherService.claim` không lọc `approval_status` | — | Voucher phát từ campaign chưa hợp pháp hoá |
| G8 | Voucher không log `issuance_source` (phát qua flow nào) | Audit | Không trace nguồn phát |
| G9 | `issued_count` cache có thể drift với COUNT(vouchers) | Integrity | Có thể vượt `max_issuances` silent |
| G10 | Voucher `code` 8 ký tự (~40 bit) + không rate-limit redeem | Bảo mật | Brute-force khả thi |
| G11 | Không versioning template | Audit | Admin sửa cap → campaign cũ không reproduce được |
| G12 | Không tách lô phát (issuance) khỏi voucher | Business | Shop không biết lô nào phát cho ai |
| G13 | Không có `program_form` phân loại hình thức khuyến mại | NĐ 81/2018 Điều 8, 13 | Approval tier tính sai nếu chỉ theo cost |
| G14 | Retention pháp lý chưa định nghĩa | Luật Kế toán 2015 Điều 41 (10 năm) | Xoá authorization/service_fee vi phạm lưu trữ |
| G15 | Phí dịch vụ công ty thu — không có VAT/hoá đơn điện tử | NĐ 123/2020/NĐ-CP | Doanh thu không kê khai đúng |

### 1.2 Gaps nghiệp vụ

- **Welcome voucher** `_maybe_issue_welcome_voucher` chọn first campaign source=SIGNUP bất kỳ — không có ràng buộc "1 welcome campaign active / tenant".
- **Birthday job** không re-check `approval_status` tại trigger time.
- **Voucher expire** không có job auto-update `status=expired`.

---

## 2. Mục tiêu rebuild

1. **Tuân thủ khung pháp lý** VN tham chiếu rõ ràng từng luật.
2. **Audit trail đầy đủ**: trace được ai tạo / ký / nộp / duyệt / phát / dùng voucher.
3. **Separation of concerns**: Template (admin-owned) ↔ Campaign (shop-enrolled) ↔ Authorization ↔ Fee ↔ Issuance ↔ Voucher ↔ Transaction.
4. **Integrity invariants ở DB level**: CHECK cap, partial unique index, view cho counting, trigger validate (không mutate).
5. **Reporting hooks**: tracker 45-day, cost realized vs estimated, retention 10 năm.
6. **Managed service model**: shop chỉ ký uỷ quyền + trả phí, công ty làm Sở CT + thu phí dịch vụ + xuất hoá đơn.

---

## 3. Kiến trúc đích — Data model

### 3.1 Bảng mới

**`campaign_templates`** — admin-managed

> **v2.2 adjustment (M1 review pass 1)**: length `code` mở rộng **40→60**, `name` **120→200** — prefix `system-` + VN có dấu dễ dài. `approval_tier_hint` KHÔNG lưu DB (derive ở `determine_tier` service).

| Cột | Type | Null | Ghi chú |
|---|---|---|---|
| id | INT PK | | |
| code | VARCHAR(60) UNIQUE | | vd `system-welcome-5pct-10k` |
| name | VARCHAR(200) | | |
| description | TEXT | ✓ | admin internal |
| source | ENUM(manual, birthday, signup) | | |
| program_form | ENUM(giam_gia, tang_kem, may_rui_quay_so, may_rui_truc_tiep, khach_hang_thuong_xuyen) | | **NEW** — phân loại theo NĐ 81/2018 Điều 8, 13; driver chính cho approval_tier |
| discount_type | ENUM(percent, fixed) | | |
| default_usage_guide | TEXT | | shop không sửa |
| default_support_contact | VARCHAR(200) | ✓ | |
| default_terms | TEXT | ✓ | shop append |
| max_discount_percent_cap | SMALLINT | ✓ | 1-50 (luật ≤50); bắt buộc khi percent |
| max_discount_value_cap | INT | ✓ | trần VND/voucher khi percent (bắt buộc khi percent) |
| max_discount_fixed_cap | INT | ✓ | trần `discount_value` khi fixed |
| min_order_floor | INT | | default 0 |
| max_issuances_cap | INT | ✓ | NULL=unlimited |
| max_duration_days | SMALLINT | ✓ | trần độ dài campaign |
| min_voucher_ttl_days | SMALLINT | | voucher hạn tối thiểu |
| max_voucher_ttl_days | SMALLINT | | voucher hạn tối đa |
| version | INT | | tăng khi sửa cap |
| is_active | BOOL | | |
| created_at, deleted_at | TIMESTAMP | | soft delete |

**CHECK:**
- `discount_type='percent' → max_discount_percent_cap IS NOT NULL AND max_discount_percent_cap <= 50 AND max_discount_value_cap IS NOT NULL`
- `discount_type='fixed' → max_discount_fixed_cap IS NOT NULL`
- `program_form IN ('may_rui_quay_so','may_rui_truc_tiep') → approval_tier_hint='full_dossier'` (enforced ở service, không CHECK)

**`campaign_issuances`** — lô phát voucher (v1 mặc định 1-1 với campaign)

| Cột | Type | Null | Ghi chú |
|---|---|---|---|
| id | INT PK | | |
| tenant_id | INT FK | | |
| campaign_id | INT FK | | |
| source | ENUM(manual_bulk, on_claim, birthday_job, signup_job, admin_grant) | | |
| planned_quantity | INT | | |
| issued_quantity | INT | | cache, tăng atomic cùng voucher insert |
| started_at | TIMESTAMP | | |
| ended_at | TIMESTAMP | ✓ | |
| triggered_by_user_id | INT FK users | ✓ | NULL cho job |
| note | VARCHAR(500) | ✓ | |

Partial unique `(campaign_id, source, DATE(started_at))` để `VoucherService.claim` có thể `INSERT ... ON CONFLICT DO UPDATE RETURNING id` lazy create without race.

**`campaign_regulatory_submissions`** — hồ sơ Sở CT (do ops upload)

| Cột | Type | Null | Ghi chú |
|---|---|---|---|
| id | INT PK | | |
| campaign_id | INT FK | | |
| doc_type | ENUM(notify_so_ct, dang_ky_so_ct, dieu_le, du_toan, xac_nhan_so_ct, bao_cao_ket_thuc) | | `notify_so_ct` cho Điều 17, `dang_ky_so_ct` cho Điều 19 |
| reference_no | VARCHAR(120) | ✓ | số công văn |
| url | VARCHAR(500) | ✓ | |
| note | TEXT | ✓ | |
| submitted_at | TIMESTAMP | | |
| submitted_by_user_id | INT FK users | | ops staff |

**`campaign_approval_events`** — audit log duyệt

| Cột | Type | Null |
|---|---|---|
| id | INT PK | |
| campaign_id | INT FK | |
| event_type | ENUM(submitted, auto_approved, ops_started, approved, rejected, revision_requested, cancelled_by_shop) | |
| actor_user_id | INT FK users | ✓ |
| reason | TEXT | ✓ |
| at | TIMESTAMP | |

### 3.2 Alter `campaigns`

| Cột mới | Type | Null | Ghi chú |
|---|---|---|---|
| template_id | INT FK templates | ✓ | NULL cho legacy |
| template_version_snapshot | INT | ✓ | chép `template.version` tại enroll |
| program_form | ENUM(...) | ✓ | chép từ template tại enroll, NULL cho legacy |
| approval_status | ENUM(draft, pending_approval, auto_approved, approved, rejected, revision_requested) | | default `auto_approved` cho backfill |
| approval_tier | ENUM(none, notify_so_ct, dang_ky_so_ct, full_dossier) | | default `none` |
| estimated_cost | BIGINT | | VND |
| realized_cost | BIGINT | | default 0, update khi voucher dùng |
| ops_filing_started_at | TIMESTAMP | ✓ | **NEW (C4)** — ops click "bắt đầu nộp hồ sơ" → chặn shop revoke authorization |
| post_report_due_at | TIMESTAMP | ✓ | = ends_at + 45 ngày (NĐ 81 Điều 21) |
| post_report_submitted_at | TIMESTAMP | ✓ | |
| created_by_user_id | INT FK users | | |
| reviewed_by_user_id | INT FK users | ✓ | |
| reviewed_at | TIMESTAMP | ✓ | |
| rejection_reason | TEXT | ✓ | |

**CHECK / Index mới:**
- `CHECK (discount_type != 'percent' OR discount_value <= 50)` — G1 cứng
- `CHECK (approval_status != 'rejected' OR rejection_reason IS NOT NULL)`
- Partial index `ix_campaigns_tenant_claimable` `(tenant_id) WHERE approval_status IN ('auto_approved','approved') AND is_active AND deleted_at IS NULL`
- **Partial unique** `ux_campaigns_tenant_template_pending` `(tenant_id, template_id) WHERE approval_status IN ('draft','pending_approval') AND deleted_at IS NULL` — chặn concurrent enroll (C5)

**Thay `issued_count` bằng view `v_campaign_stats`** (Option B, per reviewer):
```sql
CREATE VIEW v_campaign_stats AS
SELECT
  c.id AS campaign_id,
  COUNT(v.id) FILTER (WHERE v.status IN ('issued','used')) AS issued_count,
  COUNT(v.id) FILTER (WHERE v.status = 'used') AS used_count,
  COUNT(v.id) FILTER (WHERE v.status = 'cancelled') AS cancelled_count,
  COALESCE(SUM(CASE WHEN t.id IS NOT NULL THEN t.voucher_discount_amount ELSE 0 END),0) AS realized_cost
FROM campaigns c
LEFT JOIN vouchers v ON v.campaign_id = c.id
LEFT JOIN transactions t ON t.voucher_id = v.id
GROUP BY c.id;
```

**Atomic claim (E2 — bắt buộc lock rõ ràng)**: cache `issued_count` đã bị bỏ → phải lock hàng `campaigns` hoặc advisory-lock theo `campaign_id` để chặn race ở READ COMMITTED:

```sql
BEGIN;
-- Option A: lock dòng campaign trong transaction claim
SELECT id FROM campaigns WHERE id = :campaign_id FOR NO KEY UPDATE;

-- hoặc Option B (khuyến nghị — cheaper, không chạm campaign row):
SELECT pg_advisory_xact_lock(hashtext('claim:' || :campaign_id));

-- Sau khi giữ lock, check capacity + insert trong cùng transaction:
INSERT INTO vouchers (...)
SELECT ... FROM campaigns c
WHERE c.id = :campaign_id
  AND c.approval_status IN ('auto_approved','approved')
  AND c.is_active
  AND (c.max_issuances IS NULL
       OR (SELECT COUNT(*) FROM vouchers WHERE campaign_id = c.id AND status IN ('issued','used')) < c.max_issuances);
-- raise nếu affected_rows = 0 (hết suất hoặc campaign đã inactive)
COMMIT;
```

+ `AFTER INSERT ON vouchers` trigger **chỉ validate** (không mutate): raise nếu `COUNT(*) > max_issuances` — backup defense, không phải source of truth.

**Invariant test**: concurrent 50 request `claim` cùng lúc với `max_issuances=10` → đúng 10 voucher insert, 40 raise `VoucherCampaignFullError` (acceptance #2).

### 3.3 Alter `vouchers`

| Cột mới | Type | Null | Ghi chú |
|---|---|---|---|
| issuance_id | INT FK campaign_issuances | ✓ | NOT NULL cho voucher mới; NULL cho legacy |
| issued_by_user_id | INT FK users | ✓ | NULL cho job |
| issue_source | ENUM(manual_claim, welcome_signup, birthday_auto, admin_grant) | | |
| discount_snapshot | JSONB | ✓ | `{discount_type, discount_value, max_discount, min_order, terms_hash}` — **chỉ field Campaign-owned + SHA-256 hash của terms** (I1). Không duplicate campaign_name/usage_guide |
| cancelled_at | TIMESTAMP | ✓ | |
| cancelled_reason | VARCHAR(500) | ✓ | |

**Thêm `VoucherStatus.CANCELLED`** — cancel chỉ cho voucher `status='issued'`; voucher `status='used'` **không đụng** (đã vào tax record).

Partial unique index voucher (existing) update: `(campaign_id, membership_id) WHERE status NOT IN ('used','expired','cancelled')` — shop có thể re-claim sau cancel.

### 3.4 Alter `transactions`

| Cột mới | Type | Null |
|---|---|---|
| legal_discount_ratio | NUMERIC(5,2) GENERATED ALWAYS AS (voucher_discount_amount::NUMERIC / NULLIF(gross_amount,0) * 100) STORED | ✓ |

Service-layer warn (không CHECK cứng) khi ratio > 50 — đợt tập trung NĐ 81 Điều 7 có thể hợp lệ.

### 3.5 Managed service tables (section riêng — section 4)

Xem bên dưới.

---

## 4. Managed Service Data model

### 4.1 `tenant_authorizations` — giấy uỷ quyền điện tử

| Cột | Type | Null | Ghi chú |
|---|---|---|---|
| id | INT PK | | |
| tenant_id | INT FK tenants | | |
| scope | ENUM(per_campaign) | | **v1 chỉ per_campaign**; framework defer phase sau (I7) |
| campaign_id | INT FK campaigns | | NOT NULL v1 |
| document_content_hash | VARCHAR(64) | | SHA-256 văn bản uỷ quyền render tại thời điểm ký |
| document_url | VARCHAR(500) | ✓ | link PDF (optional v1) |
| signed_by_user_id | INT FK users | | owner shop |
| signed_at | TIMESTAMP | | |
| signature_method | ENUM(click_to_sign, otp_email) | | **v1 chỉ 2 method này**; digital_cert/otp_sms defer |
| signature_payload | JSONB | | **I2** — xem schema dưới |
| valid_from | TIMESTAMP | | = signed_at |
| valid_until | TIMESTAMP | | = campaign.ends_at + 30 ngày (cho báo cáo kết thúc) |
| revoked_at | TIMESTAMP | ✓ | |
| revoked_reason | TEXT | ✓ | |
| retention_until | TIMESTAMP | | = signed_at + 10 năm (Luật Kế toán 2015 Điều 41) — hard delete chỉ sau mốc này |

**`signature_payload` JSONB schema (I2):**
```json
{
  "ip": "x.x.x.x",
  "user_agent": "...",
  "session_id": "req-abc123",
  "otp_delivery_address": "owner@shop.vn",
  "otp_verified_at": "2026-04-22T10:05:12+07:00",
  "otp_attempts_count": 1,
  "consent_text_hash": "sha256-of-exact-bytes-user-saw",
  "consent_text_version": "v1.0-2026-04",
  "rendered_pdf_hash": "sha256-of-pdf-if-generated",
  "signed_at_server_clock": "...",
  "signed_at_client_clock": "..."
}
```

**CHECK:**
- `scope='per_campaign' → campaign_id IS NOT NULL`
- Partial unique `(tenant_id, campaign_id) WHERE scope='per_campaign' AND revoked_at IS NULL`

**Revoke rule:** `UPDATE ... SET revoked_at=NOW()` **chỉ cho phép** khi `campaigns.ops_filing_started_at IS NULL AND campaigns.approval_status != 'approved'` (C4).

### 4.2 `campaign_service_fees`

| Cột | Type | Null | Ghi chú |
|---|---|---|---|
| id | INT PK | | |
| campaign_id | INT FK | | |
| tenant_id | INT FK | | |
| fee_type | ENUM(so_ct_filing, dossier_preparation, multi_province, express, waiver) | | `waiver` cho demo account |
| amount | BIGINT | | VND (pre-VAT) |
| vat_rate | NUMERIC(4,2) | | default 10.00 |
| vat_amount | BIGINT | | computed = amount × vat_rate/100 |
| total_with_vat | BIGINT | | computed = amount + vat_amount |
| description | VARCHAR(500) | | |
| status | ENUM(draft, invoiced, paid, waived, refund_requested, refunded) | | E1: hai status cuối cho refund flow |
| invoiced_at, paid_at | TIMESTAMP | ✓ | |
| invoice_reference | VARCHAR(120) | ✓ | số hoá đơn nội bộ (v1 manual); integration e-invoice VNPT/Viettel **ngoài scope v1** |
| e_invoice_provider | ENUM(manual, vnpt, viettel, misa) | | default `manual` v1 |
| e_invoice_payload | JSONB | ✓ | reserved |
| refund_requested_at | TIMESTAMP | ✓ | set khi admin reject campaign mà fee đã `paid` |
| refunded_at | TIMESTAMP | ✓ | set khi kế toán xác nhận đã hoàn tiền thực tế (manual update) |
| refund_reason | VARCHAR(500) | ✓ | lý do hoàn (reject campaign / shop bổ sung hồ sơ fail / …) |
| retention_until | TIMESTAMP | | = created_at + 10 năm |
| created_by_user_id | INT FK users | | |
| created_at | TIMESTAMP | | |

**Partial unique** `(campaign_id, fee_type) WHERE status NOT IN ('waived','refunded')` — chặn double-charge fee cùng loại cho cùng campaign còn active (C4, mở rộng E1).

**Refund flow v1 (E1):**
```
reject_campaign(campaign_id, reason):
  for fee in campaign_service_fees WHERE status='paid':
    fee.status = 'refund_requested'
    fee.refund_requested_at = NOW()
    fee.refund_reason = reason
  # KHÔNG tự refund tiền — kế toán nhận log, refund manual, rồi
  # admin/ops bấm "confirm refunded" → status='refunded', refunded_at=NOW()
```
v1 **không** tích hợp cổng thanh toán hoàn tiền tự động. Fee row **không hard-delete** (Luật Kế toán Điều 41, giữ 10 năm).

### 4.3 `campaign_fee_schedules` — bảng giá (v1 seed-only, admin CRUD defer phase sau)

| Cột | Type | Null |
|---|---|---|
| id | INT PK | |
| fee_type | ENUM | |
| trigger_rule | JSONB | |
| base_amount | BIGINT | |
| is_active | BOOL | |
| version | INT | |
| created_at | TIMESTAMP | |

Seed 5 row: `so_ct_filing=500k`, `dossier_preparation=1M`, `multi_province=+2M`, `express=+500k`, `waiver=0`.

### 4.4 Alter `campaigns` (service-fee fields)

| Cột mới | Type | Null | Ghi chú |
|---|---|---|---|
| authorization_id | INT FK tenant_authorizations | ✓ | NULL nếu auto_approved không cần uỷ quyền |
| service_fee_total | BIGINT | | snapshot = SUM(campaign_service_fees.total_with_vat) pending |
| service_fee_status | ENUM(none, estimated, invoiced, paid) | | |

**Approve guard (service layer):**
```
approve(campaign_id):
  assert campaign.approval_status == 'pending_approval'
  if settings.SERVICE_FEE_ENABLED:
      assert campaign.service_fee_status IN ('paid','none')  # đồ án bỏ qua
  assert authorization.revoked_at IS NULL AND authorization.valid_until > NOW()
  assert exists(campaign_regulatory_submissions WHERE campaign_id=X AND doc_type IN ('xac_nhan_so_ct'))
  -- đồ án: 3 điều kiện; khoá luận: thêm service_fee_status
```

### 4.5 Alter `tenants` (block delete-tenant)

Service `delete_tenant(id)` phải:
```
assert NOT exists(campaigns WHERE tenant_id=id AND approval_status='approved' AND ends_at > NOW())
-- soft-delete tenant OK; authorizations/fees/transactions survive cho retention
```

---

## 5. Lifecycle end-to-end

```
 SHOP                          COMPANY (admin/ops)         SYSTEM
  │                                  │                        │
  │ 1. Preview: pick template + fill form                     │
  │    (POST /merchant/campaigns/enroll/preview)              │
  │◄─── estimated_cost, approval_tier, fee_preview, auth_doc_text, doc_hash
  │                                  │                        │
  │ 2. Xem phí + nội dung uỷ quyền  │                        │
  │ 3. Request OTP email             │                        │──► notifications.send_otp_email
  │ 4. Nhập OTP → sign               │                        │──► tenant_authorizations (signed)
  │                                  │                        │──► campaign (pending_approval, fee_status=estimated)
  │                                  │                        │──► campaign_service_fees (draft)
  │                                  │                        │──► campaign_approval_events (submitted)
  │                                  │                        │
  │ 5. Nhận invoice (hoặc auto_approved → bỏ qua step 5-6)    │
  │ 6. Thanh toán (v1: admin mark paid manual)                │──► fee_status=paid
  │                                  │                        │
  │                                  │ 7. Ops click "Bắt đầu nộp hồ sơ"
  │                                  │──────────────────────► ops_filing_started_at=NOW
  │                                  │                        │  (shop không thể revoke nữa)
  │                                  │ 8. Chuẩn bị hồ sơ, nộp Sở CT
  │                                  │ 9. Upload xác nhận     │──► campaign_regulatory_submissions (xac_nhan_so_ct)
  │                                  │ 10. Click "Approve"    │──► approval_status=approved
  │                                  │                        │
  │ 11. Voucher claimable            │                        │
  │                                  │                        │
  │ 12. Campaign ends                │                        │──► post_report_due_at set
  │                                  │ 13. Ops upload báo cáo kết thúc (45 ngày)
  │                                  │                        │
  │                                  │ (nếu reject) Cancel vouchers status='issued' (NOT 'used')
```

---

## 6. Backend changes

### 6.1 Migrations (thứ tự + safety)

Mỗi migration theo pattern **add nullable → backfill → alter NOT NULL** (I5). Rollback một-liner kèm file.

| # | Tên | Nội dung | Rollback |
|---|---|---|---|
| M1 | `019_create_campaign_templates.py` | Tạo bảng + seed version=1 | DROP TABLE |
| M2a | `020a_alter_campaigns_add_template_approval_nullable.py` | Thêm tất cả cột mới nullable | DROP COLUMN |
| M2b | `020b_backfill_campaigns_legacy.py` | `UPDATE SET approval_status='auto_approved', approval_tier='none', estimated_cost=COALESCE(max_discount * max_issuances, 0), realized_cost=0`; cho campaign `ends_at < NOW` → `post_report_submitted_at=NOW` (deemed-filed, tránh spam overdue job) | UPDATE lại |
| M2c | `020c_alter_campaigns_not_null_constraints.py` | ALTER NOT NULL các cột; thêm CHECK constraints + partial indexes | DROP CHECK/INDEX |
| M3 | `021_create_campaign_issuances.py` | + partial unique `(campaign_id, source, DATE(started_at))` | DROP |
| M4a | `022a_alter_vouchers_add_audit_nullable.py` | Thêm cột mới nullable, enum `cancelled` | DROP |
| M4b | `022b_backfill_vouchers.py` | Legacy voucher không set issuance_id (giữ NULL); partial unique index update | — |
| M5 | `023_create_campaign_regulatory_submissions.py` | | DROP |
| M6 | `024_create_campaign_approval_events.py` | | DROP |
| M7 | `025_create_v_campaign_stats_view.py` | Tạo view + drop cột `campaigns.issued_count` (nếu còn được đọc ở code, migrate trước) | CREATE lại col + DROP VIEW |
| M8 | `026_create_tenant_authorizations.py` | + partial unique + CHECK | DROP |
| M9 | `027_create_campaign_service_fees.py` | + generated columns vat_amount, total_with_vat; partial unique | DROP |
| M10 | `028_create_campaign_fee_schedules_and_seed.py` | + seed 5 row | DROP |
| M11 | `029_alter_campaigns_add_authorization_fee_fields.py` | `authorization_id FK ON DELETE SET NULL` (E3 — tránh IntegrityError khi retention purge xoá `tenant_authorizations` sau 10 năm), `service_fee_total`, `service_fee_status`, `ops_filing_started_at` | DROP |
| M12 | `030_alter_transactions_add_legal_ratio.py` | GENERATED column | DROP |
| M13 | `031_create_voucher_validate_trigger.py` | `AFTER INSERT ON vouchers` validate `COUNT <= max_issuances` (non-mutating, C2 Option B) | DROP TRIGGER |

### 6.2 Models mới

```
backend/app/models/
├── campaign_template.py            (new)
├── campaign_issuance.py            (new)
├── campaign_regulatory_submission.py (new)
├── campaign_approval_event.py      (new)
├── tenant_authorization.py         (new)
├── campaign_service_fee.py         (new)
├── campaign_fee_schedule.py        (new)
├── campaign.py                     (extend)
├── voucher.py                      (extend: enum CANCELLED, cols, snapshot)
└── transaction.py                  (extend: legal_discount_ratio generated)
```

### 6.3 Services

```
backend/app/services/
├── campaign_template_service.py         (new, admin CRUD)
├── campaign_enrollment_service.py       (new, preview + enroll + tier calc)
├── campaign_approval_service.py         (new, ops_start/approve/reject + cascade cancel issued-only)
├── campaign_issuance_service.py         (new, lazy-create bằng ON CONFLICT)
├── campaign_post_report_service.py      (new, 45-day check)
├── tenant_authorization_service.py      (new, request-otp/sign/revoke; revoke guard bởi ops_filing_started_at)
├── campaign_fee_service.py              (new, calc theo schedule + invoice + mark_paid; VAT auto)
├── campaign_service.py                  (update, filter approval_status; get_claimable)
├── voucher_service.py                   (update, claim filter approval_status + authorization.revoked check; gắn issuance_id/source/snapshot; cancel-issued-only on reject)
└── transaction_service.py               (update, update realized_cost via view; warn >50%)
```

**`CampaignEnrollmentService.enroll` approval tier logic (I6):**

```python
def determine_tier(program_form, estimated_cost) -> str:
    # Form-based trước (luật định), rồi mới đến cost
    if program_form in ('may_rui_quay_so', 'may_rui_truc_tiep'):
        return 'dang_ky_so_ct'    # Điều 19 NĐ 81 — bất kể cost
    # Form giảm giá / tặng kèm / thường xuyên → theo cost
    if estimated_cost <= settings.CAMPAIGN_AUTO_THRESHOLD:
        return 'none'             # auto_approved
    if estimated_cost <= settings.CAMPAIGN_NOTIFY_THRESHOLD:
        return 'notify_so_ct'     # Điều 17
    return 'full_dossier'         # dossier đầy đủ
```

**`CampaignApprovalService.reject` (C3 + E1):**
```python
def reject(campaign_id, admin_user_id, reason):
    # Ordering invariant: UPDATE status TRƯỚC khi cancel voucher
    campaign.approval_status = 'rejected'
    campaign.rejection_reason = reason
    campaign.reviewed_by = admin_user_id

    # Warn admin nếu có voucher đã used (không cancel được)
    used_count = count(vouchers WHERE campaign_id=X AND status='used')
    if used_count > 0:
        warnings.append(f'{used_count} voucher đã sử dụng, không hoàn tác được')

    # Chỉ cancel voucher status='issued' (KHÔNG 'used')
    UPDATE vouchers
      SET status='cancelled', cancelled_at=NOW, cancelled_reason=reason
      WHERE campaign_id=X AND status='issued'

    # Refund fee flow — ẩn ở đồ án
    if settings.SERVICE_FEE_ENABLED:
        UPDATE campaign_service_fees
          SET status='refund_requested', refund_requested_at=NOW, refund_reason=reason
          WHERE campaign_id=X AND status='paid'

    INSERT campaign_approval_events (event_type='rejected', actor_user_id, reason)
```

### 6.4 Config

```python
# backend/app/core/config.py (đã chốt 2026-04-22)
CAMPAIGN_AUTO_THRESHOLD: int = 500_000            # v2.1: 500k VND
CAMPAIGN_NOTIFY_THRESHOLD: int = 2_000_000        # v2.1: 2M VND
CAMPAIGN_DEFAULT_POST_REPORT_DAYS: int = 45
SERVICE_FEE_ENABLED: bool = False                 # v2.2: OFF ở đồ án, ON ở khoá luận
SERVICE_FEE_VAT_RATE: float = 10.0
AUTH_RETENTION_YEARS: int = 10                    # Luật Kế toán 2015 Điều 41
CONSENT_TEXT_VERSION: str = "v1.0-2026-04"
```

**Feature flag `SERVICE_FEE_ENABLED` tác động:**
- Enrollment service: skip tạo `campaign_service_fees` row khi enroll.
- Approve service: bỏ check `service_fee_status IN ('paid','none')`.
- Reject service: skip refund flow.
- API `/merchant/campaigns/{id}/service-fee`, `/admin/campaigns/{id}/fees/*`, `/admin/fee-schedules/*`: return `404 Not Found` khi flag OFF (hoặc trang placeholder).
- FE merchant: ẩn card "Phí dịch vụ" ở `/merchant/campaigns/[id]`, bỏ step "Thanh toán" khỏi enrollment stepper.
- FE admin: ẩn tab/menu "Fee management".
- Seed demo: không gọi `CampaignFeeService.create_fee_draft`; bỏ qua block seed fee.

### 6.5 APIs

**Merchant:**
| Method | Path | Mục đích |
|---|---|---|
| GET | `/merchant/campaign-templates` | List active templates |
| POST | `/merchant/campaigns/enroll/preview` | Preview cost + fee + auth_doc_text + doc_hash |
| POST | `/merchant/authorizations/request-otp` | Gửi OTP email |
| POST | `/merchant/authorizations/sign` | Verify OTP → sign → create campaign pending + auth + fee draft |
| GET | `/merchant/campaigns/{id}` | Detail + approval_status + fee + auth |
| POST | `/merchant/authorizations/{id}/revoke` | Revoke (guarded bởi ops_filing_started_at IS NULL) |
| GET | `/merchant/campaigns/{id}/service-fee` | Invoice view |
| (removed) `POST /merchant/campaigns` | — | Xoá endpoint tạo tự do |

**Admin:**
| Method | Path | Mục đích |
|---|---|---|
| GET/POST/PATCH/DELETE | `/admin/campaign-templates[/{id}]` | CRUD template |
| GET | `/admin/campaigns/pending` | Queue pending |
| POST | `/admin/campaigns/{id}/mark-ops-started` | Click "bắt đầu nộp hồ sơ" — set `ops_filing_started_at` |
| POST | `/admin/campaigns/{id}/regulatory-submissions` | Upload công văn Sở CT |
| POST | `/admin/campaigns/{id}/service-fees/{fee_id}/mark-paid` | Mark fee paid |
| POST | `/admin/campaigns/{id}/approve` | Approve (guard 4 điều kiện ở 4.4) |
| POST | `/admin/campaigns/{id}/reject` | Reject + cascade cancel issued-only |
| GET | `/admin/campaigns/overdue-reports` | 45-day overdue |

### 6.6 Jobs

| Job | Cron | Mục đích |
|---|---|---|
| `expire_vouchers` | hourly | Set `status=expired` khi `expires_at < now` |
| `check_post_report_overdue` | daily 01:00 | Notify ops campaign `post_report_due_at < now AND post_report_submitted_at IS NULL` |
| `birthday_voucher` | (update) | Check `approval_status IN ('auto_approved','approved')` + `authorization.revoked_at IS NULL` |
| `purge_retention` | weekly | **NEW** — hard delete authorization/fee rows `retention_until < NOW()` (>10 năm); chạy trong transaction với log audit |

---

## 7. Frontend changes

### 7.1 Admin

- `/admin/campaign-templates` — list + create + edit + soft delete
- `/admin/campaigns/pending` — queue, cột: fee_status, auth_signed, ops_started_at, badge approval
- `/admin/campaigns/{id}` — single detail page (không phải kanban v1), có 5 section:
  1. Verify uỷ quyền (read + hash check)
  2. Verify fee paid
  3. Upload regulatory submission (công văn + xác nhận)
  4. Nút "Bắt đầu nộp hồ sơ" (set ops_filing_started_at)
  5. Nút Approve / Reject (hiển thị warn nếu có voucher đã used)
- `/admin/campaigns/overdue-reports` — bảng quá hạn 45 ngày

### 7.2 Merchant

- `/merchant/campaigns/enroll` — stepper 3 bước:
  1. Chọn template + điền form → "Xem trước"
  2. Preview: estimated_cost + fee table (pre-VAT / VAT / total) + auth_doc_text (render từ template Điều 562-569 BLDS) + tick consent → "Gửi OTP"
  3. Nhập OTP → submit → campaign `pending_approval`
- `/merchant/campaigns/[id]` tabs:
  - Tổng quan (+ badge approval)
  - Uỷ quyền (hash, chữ ký, nút Thu hồi disabled nếu `ops_filing_started_at IS NOT NULL`)
  - Phí dịch vụ (invoice)
  - Voucher đã phát

### 7.3 Types

`frontend/src/types/merchant.ts` thêm:
- `CampaignTemplateResponse/CreateRequest/UpdateRequest`
- `CampaignEnrollPreviewResponse` (estimated_cost, tier, fees, auth_doc_text, doc_hash)
- `AuthorizationOtpRequest/SignRequest/Response`
- `CampaignServiceFeeResponse`
- `CampaignApprovalEvent`, `CampaignIssuance`, `CampaignRegulatorySubmission`
- Update `CampaignResponse`: approval_status, approval_tier, program_form, estimated_cost, realized_cost, ops_filing_started_at, post_report_*, authorization_id, service_fee_*

---

## 8. Phases & commits (v2 — scope trim)

| Phase | Nội dung | Commit |
|---|---|---|
| 1 | M1 + M2a-c: model `CampaignTemplate`, alter `campaigns`, partial unique, backfill legacy | `feat(campaign): template model + alter campaigns + backfill legacy` |
| 2 | Admin template CRUD service + API | `feat(admin): CRUD campaign template` |
| 3 | M3 + M4a-b + M7: model `CampaignIssuance`, alter `vouchers`, view `v_campaign_stats` | `feat(voucher): issuance + audit trail + view thay issued_count` |
| 4 | M5 + M6 + M13: models regulatory/approval_events + validate trigger | `feat(campaign): hồ sơ pháp lý + audit event + validate trigger` |
| 5 | M8 + M9 + M10 + M11: auth + fee + schedule + alter campaigns | `feat(legal): uỷ quyền điện tử + phí dịch vụ + VAT fields` |
| 6 | `CampaignEnrollmentService` + preview + sign flow APIs | `feat(merchant): enroll preview + ký uỷ quyền OTP email` |
| 7 | `TenantAuthorizationService` + `CampaignFeeService` + revoke guard | `feat(service): authorization OTP + fee VAT + revoke guard` |
| 8 | `CampaignApprovalService` + admin queue APIs (pending/ops-start/approve/reject + cascade cancel issued-only) | `feat(admin): duyệt campaign + cascade cancel voucher issued-only` |
| 9 | Update `VoucherService.claim` (filter approval_status + authorization.revoked, issuance lazy-create bằng ON CONFLICT, snapshot terms_hash) | `fix(voucher): approval filter + snapshot + lazy issuance` |
| 10 | M12 + `TransactionService` update realized_cost via view, warn >50% | `feat(transaction): realized_cost từ view + warn >50%` |
| 11 | Jobs: `expire_vouchers`, `check_post_report_overdue`, `purge_retention`, update birthday_voucher | `feat(jobs): expire + overdue report + 10-year retention purge` |
| 12 | Seed templates + fee schedules | `chore(seed): 3 template + 5 fee schedule` |
| 13 | Admin FE: templates CRUD + detail page (5 section ops workflow) + overdue queue | `feat(admin-ui): template CRUD + ops workflow + overdue` |
| 14 | Merchant FE: stepper enroll + OTP sign + tab uỷ quyền + tab phí | `feat(merchant-ui): enroll stepper + OTP sign + tabs` |
| 15 | Smoke test E2E: enroll auto → enroll pending với OTP → ops flow → approve → claim → use; reject với used vouchers; revoke before ops_start; concurrent enroll block | `chore(smoke): E2E lifecycle + edge cases` |
| 16 | Tests: unit cost/tier/VAT calc; integration enroll/sign/revoke/reject-partial-used; cap validation; authorization guard | `test(voucher): pháp lý + lifecycle end-to-end` |

**Tổng v2: 16 commits** (trim từ 20 của v1) · **~10 ngày công** (bump từ 8.5 cho realistic).

---

## 9. Acceptance criteria (v2 — thêm cho C1-C5, I1-I6)

1. `alembic upgrade head` chạy sạch; legacy campaigns `approval_status='auto_approved'`; legacy campaigns `ends_at < NOW` có `post_report_submitted_at=NOW` (deemed-filed); legacy campaigns không spam `check_post_report_overdue`.
2. `CHECK (discount_type != 'percent' OR discount_value <= 50)` reject ở DB level.
3. Shop không còn gọi được `POST /merchant/campaigns`.
4. Enroll preview trả về đủ: `estimated_cost`, `approval_tier` (dựa program_form + cost), `fees` (pre-VAT, VAT, total_with_vat), `auth_doc_text`, `auth_doc_hash`.
5. Enroll sign:
   - OTP delivery ghi đúng email trong `signature_payload.otp_delivery_address`.
   - `consent_text_hash` = SHA-256 của exact bytes user thấy (không chỉ version).
   - `signed_at_server_clock` vs `signed_at_client_clock` đều được record.
   - Attempt-count tăng khi sai OTP.
6. Concurrent enroll 2 owner cùng template cùng tenant → 1 thành công, 1 nhận 409 `CAMPAIGN_PENDING_EXISTS` (partial unique index).
7. `program_form ∈ (may_rui_*)` → bất kể cost, `approval_tier='dang_ky_so_ct'`.
8. Revoke authorization:
   - Trước `ops_filing_started_at` → OK.
   - Sau `ops_filing_started_at` → 409 `REVOKE_BLOCKED_OPS_STARTED`.
9. Approve campaign chỉ succeed khi đủ 4 điều kiện (section 4.4); thiếu bất kỳ → 400 với lý do cụ thể.
10. Reject campaign:
    - Voucher `status='issued'` → bị `cancelled` (cascade).
    - Voucher `status='used'` → **không đụng**; admin nhận warning trước khi reject.
    - Ordering: `approval_status='rejected'` UPDATE trước cancel voucher.
11. `VoucherService.claim`:
    - Campaign `pending_approval/rejected/expired/deleted` hoặc `authorization.revoked_at IS NOT NULL` → 404 `CAMPAIGN_NOT_ELIGIBLE`.
    - Voucher mới luôn có `issuance_id`, `issue_source`, `discount_snapshot` (chỉ keys Campaign-owned + `terms_hash`).
12. View `v_campaign_stats.issued_count` consistent với COUNT(vouchers WHERE status IN ('issued','used')); voucher INSERT thứ N+1 khi vượt `max_issuances` → IntegrityError (từ validate trigger).
13. VAT tính đúng: `campaign_service_fees.vat_amount = amount × 0.10`; `total_with_vat = amount + vat_amount`.
14. Campaign end + 45 ngày không có `bao_cao_ket_thuc` → `check_post_report_overdue` notify ops.
15. Voucher expired tự động sau 1h.
16. Transaction `legal_discount_ratio` auto-compute (GENERATED); warn log ở service khi > 50.
17. Block delete-tenant khi có campaign `approved AND ends_at > NOW()`.
18. `purge_retention` hard delete authorization/fee chỉ khi `retention_until < NOW()`; test với row fixture `retention_until = NOW - 1 day`.
19. `pytest -v` ≥20 test mới pass; CI xanh.

---

## 10. Rủi ro & mitigation (v2)

| Rủi ro | Mitigation |
|---|---|
| Migration NOT NULL trên data có row vi phạm | Thứ tự nullable → backfill → NOT NULL, mỗi bước trong migration riêng; kiểm tra COUNT(*) WHERE col IS NULL = 0 trước alter |
| View `v_campaign_stats` chậm với dataset lớn | Scope đồ án chấp nhận; phase tối ưu: materialized view refresh on commit |
| Trigger validate + atomic claim vẫn có race hiếm | Claim chạy trong transaction serializable; trigger là second-line defense |
| Revoke authorization timing edge case (race revoke vs ops-start) | Postgres row lock FOR UPDATE trong transaction ở cả 2 path |
| Cascade cancel voucher khiến UX khách vỡ | UI `/member/vouchers` hiển thị voucher `cancelled` với badge + lý do; notification out-of-scope v1 nhưng log để đọc |
| OTP email bị spoof / rate limit | Rate limit `/authorizations/request-otp` 3 lần/5 phút; attempt-count trong payload; block sau 5 fail |
| Luật GDĐT 2023 nghiêm hơn kỳ vọng | ToS ghi rõ "click + OTP là uỷ quyền nội bộ, không tương đương chữ ký số cho giao dịch với cơ quan nhà nước" + lộ trình tích hợp VNeID/VNPT eSign phase sau |
| Hoá đơn điện tử NĐ 123/2020 chưa tích hợp | Data model đã có `e_invoice_*` fields; v1 manual mark; phase sau call API VNPT/Viettel |
| Luật VN cập nhật sau 2026-04-22 | Citations chỉ record snapshot; threshold ra config; note trong plan + DB comment |

---

## 11. Nice-to-have backlog (defer sau v1)

- **N1:** Voucher code 8→10 ký tự (~60 bit) + rate limit `/vouchers/{code}/redeem` 10 req/min/IP.
- **N2:** `campaign_fee_schedules` CRUD UI admin (v1 seed-only).
- **N3:** `scope=framework` authorization (6/12 tháng) — shop ký 1 lần dùng nhiều campaign.
- **N4:** Multi-issuance batch (campaign 1 → N lô phát manual_bulk).
- **N5:** Ops kanban view thay single-page detail.
- **N6:** Tích hợp e-invoice VNPT/Viettel thật (NĐ 123/2020).
- **N7:** Tích hợp VNeID / VNPT eSign / chữ ký số USB → upgrade `signature_method`.
- **N8:** Notification thực tế khi voucher cancel/issued/expired/tier-upgraded.
- **N9:** Upload file thật thay URL text cho submitted_docs (S3/MinIO).
- **N10:** Materialized view `v_campaign_stats` + refresh on commit.
- **N11:** VNPay/MoMo integration cho thanh toán phí dịch vụ (thay admin mark-paid manual).

---

## 12. Data retention & shop deletion (I3)

**Retention 10 năm** (Luật Kế toán 2015 Điều 41 — chứng từ kế toán):
- `tenant_authorizations.retention_until = signed_at + 10 năm`
- `campaign_service_fees.retention_until = created_at + 10 năm`
- `campaign_regulatory_submissions` — implicit 10 năm (tham chiếu campaign)
- `campaign_approval_events` — giữ 10 năm theo campaign
- Job `purge_retention` weekly hard-delete row `retention_until < NOW()` với audit log

**Shop xoá tài khoản:**
- Soft delete `tenants.deleted_at = NOW`
- Block delete nếu còn campaign `approved AND ends_at > NOW()`
- Authorizations + fees + approved campaigns **không xoá** → retention 10 năm
- Vouchers đã phát: vẫn tồn tại (transactions là tax record)
- Active campaigns `pending_approval` → auto-cancel + refund fee (manual ops)

---

## 13. VAT & hoá đơn điện tử (I4)

**NĐ 123/2020/NĐ-CP về hoá đơn điện tử:**
- Công ty thu phí dịch vụ → **doanh thu dịch vụ tư vấn** → phải xuất hoá đơn điện tử GTGT 10%.
- Data model đã sẵn: `campaign_service_fees.vat_rate/vat_amount/total_with_vat` (generated), `e_invoice_provider`, `e_invoice_payload` (reserved).

**v1 scope:**
- VAT tính auto (generated column Postgres).
- `e_invoice_provider='manual'` + `invoice_reference` nhập tay bởi admin.
- Ghi rõ trong docstring: "Tích hợp API VNPT/Viettel/MISA ngoài scope v1, tham chiếu NĐ 123/2020/NĐ-CP Điều 4, Điều 10".

**Phase sau (N6):**
- Call API e-invoice provider.
- Publish cho shop PDF/XML.
- Link invoice vào `campaign_service_fees.e_invoice_payload`.

---

## 14. Citations — tham chiếu pháp lý (snapshot 2026-04-22)

| Điều khoản | Văn bản | Nội dung | Applied to |
|---|---|---|---|
| Luật TM 2005 Điều 96 | Luật Thương mại 2005 | Hạn mức giá trị hàng hoá dùng để khuyến mại ≤ 50% (ngoại lệ 100% trong đợt tập trung) | CHECK constraint G1 |
| NĐ 81/2018 Điều 6 | NĐ 81/2018/NĐ-CP | Tổng giá trị khuyến mại ≤ 50% giá trị hàng hoá khuyến mại | Service warn G2 |
| NĐ 81/2018 Điều 7 | NĐ 81/2018 (có NĐ 17/2020 sửa đổi) | Đợt khuyến mại tập trung cho phép 100% | Service-level exception (không CHECK cứng) |
| NĐ 81/2018 Điều 8, 13 | NĐ 81/2018 | Hình thức khuyến mại: giảm giá, tặng kèm, may rủi (quay số, thẻ cào), tặng hàng, khách hàng thường xuyên | `program_form` enum |
| NĐ 81/2018 Điều 17 | NĐ 81/2018 | **Thông báo** khuyến mại tới Sở CT — cần ≥3 ngày làm việc trước | `approval_tier='notify_so_ct'` |
| NĐ 81/2018 Điều 19 | NĐ 81/2018 | **Đăng ký** khuyến mại — bắt buộc với may rủi hoặc ≥2 tỉnh | `approval_tier='dang_ky_so_ct'` |
| NĐ 81/2018 Điều 21 | NĐ 81/2018 | Báo cáo kết quả trong 45 ngày sau khi kết thúc | `post_report_due_at`, `check_post_report_overdue` |
| Luật TNDN sửa đổi 2014 | Luật thuế TNDN | Bỏ trần 15% chi phí khuyến mại; chi phí hợp lệ khi có chứng từ + đã thông báo/đăng ký | Justify approval workflow |
| Luật Giao dịch điện tử 2023 (hiệu lực 01/07/2024) | Luật GDĐT 2023 | Chữ ký điện tử: đơn giản / có độ tin cậy / số chuyên dùng (Điều 25); điều kiện "có độ tin cậy" yêu cầu xác thực danh tính đa yếu tố | OTP email = evidence nội bộ; ToS ghi rõ giới hạn |
| Bộ luật Dân sự 2015 Điều 562-569 | BLDS 2015 | Hợp đồng uỷ quyền: nội dung, thời hạn, thù lao, đơn phương chấm dứt | Template văn bản uỷ quyền render |
| Luật Kế toán 2015 Điều 41 | Luật Kế toán 2015 | Lưu trữ chứng từ kế toán ≥ 10 năm | `retention_until`, `purge_retention` job |
| NĐ 123/2020/NĐ-CP | NĐ 123/2020 | Hoá đơn điện tử: format, đăng ký với cơ quan thuế, publish cho khách | `campaign_service_fees.e_invoice_*` |
| Thông tư 07/2019/TT-BCT | Thông tư BCT | Biểu mẫu thông báo/đăng ký khuyến mại | Template hồ sơ ops chuẩn bị |

**Disclaimer (ghi trong ToS + DB comment):** Citations trên là **snapshot tại 2026-04-22**. Luật VN được sửa đổi thường xuyên; triển khai thực tế cần luật sư review lại văn bản hợp nhất mới nhất.

---

## 15. Items cần user confirm trước execute

**Đã giải quyết trong v2:**
- ~~C1 citations~~ → fix.
- ~~C2 trigger vs view~~ → Option B (view + non-mutating trigger).
- ~~C3 cascade cancel used voucher~~ → chỉ cancel status='issued'.
- ~~C4 race service fee / revoke~~ → `ops_filing_started_at` + partial unique fee.
- ~~C5 concurrent enroll~~ → partial unique `(tenant_id, template_id) WHERE pending`.
- ~~I1-I5~~ → đã apply.
- ~~I6 program_form~~ → thêm enum + tier logic form+cost.
- ~~I7 scope trim~~ → giảm 20→16 commits; framework/kanban/multi-issuance/fee_schedules CRUD UI → backlog.
- ~~Submitted docs từ shop~~ → managed service, ops upload.

**Đã chốt với user 2026-04-22:**

1. ✅ **Threshold**: `CAMPAIGN_AUTO_THRESHOLD=500_000` (500k) / `CAMPAIGN_NOTIFY_THRESHOLD=2_000_000` (2M) — demo dễ trigger cả 3 tier.
2. ✅ **Fee schedule**: theo đề xuất — `so_ct_filing=500k, dossier_preparation=1M, multi_province=+2M, express=+500k, waiver=0`.
3. ✅ **Post-report 45-day job**: implement v1 (cron query `WHERE due_at < NOW() AND post_report_submitted_at IS NULL` → warn admin).
4. ⏸️ **Retention purge job**: defer — chỉ tạo column `retention_until` để migration không phải chạy lần 2.
5. ⏸️ **PDF render**: defer — v1 chỉ render HTML + SHA-256 hash (`rendered_pdf_hash` → đổi tên `rendered_content_hash` trong model, giữ tên field cho future compat).
6. ⏸️ **Notification cancel**: log-only v1 — hiển thị `status=cancelled` + `cancelled_reason` trong trang chi tiết voucher user.
7. ✅ **Seed demo**: bắt buộc — `032_seed_demo_data.py` tạo sẵn 2-3 shop × 3 template × campaign ở các trạng thái `draft`, `pending_approval`, `auto_approved`, `approved`, `rejected` để demo full flow.

**3 edge case user flag thêm:**
- **E1 refund fee** khi reject campaign đã `paid` → thêm enum `refund_requested` / `refunded` + 3 cột audit. Xử lý tiền manual qua kế toán (không tự refund).
- **E2 atomic claim lock** → bắt buộc `SELECT ... FOR NO KEY UPDATE` hoặc `pg_advisory_xact_lock` trên campaign trong transaction claim.
- **E3 FK purge** → `campaigns.authorization_id` FK phải khai báo `ON DELETE SET NULL` ở Alembic.

---

## 16. Timeline v2

| Block | Phase | Ngày |
|---|---|---|
| Data layer core | 1-4 | 1.5 |
| Data layer legal | 5 | 0.5 |
| Business logic enroll + sign | 6-7 | 2 |
| Business logic approval + voucher + transaction | 8-10 | 1.5 |
| Jobs | 11 | 0.5 |
| Seed | 12 | 0.25 |
| Admin FE | 13 | 1.5 |
| Merchant FE | 14 | 1.5 |
| Smoke + Test | 15-16 | 1 |
| **Tổng** | | **~10 ngày công** |

---

## Next step

1. ~~User answer 7 items mục 15~~ ✅ chốt 2026-04-22.
2. ~~User approve execute v2~~ ✅ (chọn option A + flag 3 edge case).
3. ~~Code-reviewer pass 2~~ ✅ GO cho phase 1.
4. **Execute phase 1** (M1-M4 data layer core) — bắt đầu với migration `019_create_campaign_templates.py`.
