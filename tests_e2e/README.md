# Pytest E2E suite cho Chương 4 báo cáo

Bộ kiểm thử chức năng pytest cho 34 kịch bản trong Bảng 4-1 báo cáo đồ án.

## Cấu trúc

```
tests_e2e/
├── README.md                  ← tài liệu này
├── pytest.ini                 ← cấu hình pytest
├── conftest.py                ← fixtures (token, http client, db_exec, helpers)
├── test_group_a_auth.py       ← TC-A01..A10  — Xác thực và phân quyền (10 test)
├── test_group_b_partner.py    ← TC-B01..B10  — Vòng đời đối tác (10 test)
├── test_group_c_pos.py        ← TC-C01..C16 + TC-C13b — Tích điểm + đổi quà (17 test)
├── test_group_d_admin.py      ← TC-D01..D07  — Quản trị + kiểm toán (7 test)
└── results/                   ← HTML report + JUnit XML (gitignored)
```

**Tổng: 44 test functions** = 34 TC kịch bản gốc + một số sub-check (vd TC-C09 có inspect+use+verify_used).

## Yêu cầu môi trường

- Python ≥ 3.10
- `pip install pytest httpx pytest-html`
- Backend + Frontend container đang chạy: `docker compose -p loyalty-prod up -d`
- Postgres + Backend container reachable cho `db_exec` + `bcrypt_hash` helpers
- Demo data đã seed (`backend/seed_demo.py`)

## Chạy

### Chạy toàn bộ + xuất HTML report

```bash
python -m pytest tests_e2e \
    --html=tests_e2e/results/report.html \
    --self-contained-html \
    --junitxml=tests_e2e/results/junit.xml
```

Mở `tests_e2e/results/report.html` để xem dashboard PASS/FAIL với chi tiết từng test (chụp screenshot cho Phụ lục B).

### Chạy 1 group

```bash
python -m pytest tests_e2e/test_group_a_auth.py -v
python -m pytest tests_e2e/test_group_c_pos.py::test_c04_vuot_nguong_nang_hang -v
```

### Override BASE_URL (vd test prod)

```bash
BASE_URL=https://loyalty.ecom-bill.com/api python -m pytest tests_e2e
```

## Tài khoản demo (seed sẵn)

| Vai trò | Email | Mật khẩu |
|---|---|---|
| Super admin | `admin@loyalty.vn` | `admin1234` |
| Owner Cafe Cộng | `owner@cafe.vn` | `owner1234` |
| Owner Lala Food | `owner@lala.vn` | `owner1234` |
| Customer | `khach1..5@gmail.com` | `khach1234` |

## Mapping TC → test function

### Nhóm A — Xác thực và phân quyền (QT1)

| TC | Test function | Đầu vào | Kết quả mong đợi |
|---|---|---|---|
| TC-A01 | `test_a01_dang_ky_hop_le` | Họ tên, SĐT, email, pwd hợp lệ | 201 + JWT |
| TC-A02 | `test_a02_dang_ky_email_trung` | Email trùng | 409 |
| TC-A03a | `test_a03a_dang_nhap_bang_email` | Email + pwd đúng | JWT |
| TC-A03b | `test_a03b_dang_nhap_bang_phone` | SĐT + pwd đúng | JWT |
| TC-A04 | `test_a04_dang_nhap_sai_pwd` | Email/SĐT đúng, pwd sai | 401 |
| TC-A05 | `test_a05_quen_mat_khau` | Forgot password | 200 + flag TRUE |
| TC-A06 | `test_a06_truy_cap_khi_buoc_doi_pwd` | Token với flag → API khác | 423 password_change_required |
| TC-A07 | `test_a07_doi_mat_khau_va_truy_cap_lai` | Đổi pwd → API khác | 204 + 200 |
| TC-A08 | `test_a08_super_admin_skip_buoc_doi` | Forgot pwd cho admin | flag KHÔNG set + admin API 200 |
| TC-A09 | `test_a09_khach_truy_cap_admin_api` | Customer → /admin/* | 403 |
| TC-A10 | `test_a10_owner_a_truy_cap_pos_b` | Owner Cafe → POS Lala | 403 |

### Nhóm B — Vòng đời đối tác (QT2, QT3)

| TC | Test function |
|---|---|
| TC-B01 | `test_b01_dang_ky_partner_hop_le` |
| TC-B02 | `test_b02_dang_ky_partner_thieu_giay_phep` |
| TC-B03 | `test_b03_admin_phe_duyet` |
| TC-B04 | `test_b04_admin_tu_choi` |
| TC-B05 | `test_b05_partner_pending_truy_cap_endpoint_active` |
| TC-B06 | `test_b06_admin_suspend_active_partner` |
| TC-B07 | `test_b07_cau_hinh_ty_le_tich_diem` |
| TC-B08 | `test_b08_cau_hinh_hang_thanh_vien` |
| TC-B09 | `test_b09_bat_use_tiers` |
| TC-B10 | `test_b10_tat_use_tiers` |

### Nhóm C — Tích điểm và đổi quà (QT4-7)

| TC | Test function |
|---|---|
| TC-C01..C16 + C13b | `test_c01_*` đến `test_c16_*` (17 test functions) |

### Nhóm D — Quản trị và kiểm toán (QT8)

| TC | Test function |
|---|---|
| TC-D01..D07 | `test_d01_*` đến `test_d07_*` |

## Thiết kế

### Test isolation

- Mỗi test KHÔNG phụ thuộc state từ test trước (mỗi TC tạo data riêng qua fixtures).
- Fixtures setup/teardown tự dọn dẹp (vd `restore_user_password` ở TC-A07).
- Random IP per request bypass rate limit slowapi.

### Giả lập state qua DB

Một số TC cần state cụ thể không đạt được qua API thông thường (vd hạng Vàng, voucher quá hạn, must_change_password=true). Helper `db_exec()` chạy `psql` qua `docker exec` để set state chính xác. Helper `bcrypt_hash()` gọi `app.core.security.hash_password` qua `docker exec backend python` để hash mật khẩu test đúng format.

### Verify side effects

Mỗi TC verify không chỉ HTTP status mà còn:
- DB state (vd `must_change_password` flag, `last_status_reason`)
- Audit log entries (before/after snapshot, reason)
- Ledger entries (actor_user_id cho EARN)

## Kết quả tham khảo

Run cuối (commit `eb6d463`): **44/44 PASS** trên môi trường `loyalty-prod` (FE proxy `http://localhost:3199/api`).

## Capture cho Phụ lục B

1. Chạy với `--html=results/report.html` → screenshot dashboard (tổng PASS/FAIL + duration)
2. Click từng test → expand chi tiết request/response → screenshot (vd TC-C04 hiển thị tier_upgraded=true)
3. JUnit XML có thể import vào CI/CD report tools nếu cần
