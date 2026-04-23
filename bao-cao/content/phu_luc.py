"""Phụ lục — Hướng dẫn sử dụng luồng Campaign → Voucher."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _img(rb, filename: str, caption: str, width_cm: float = 13.0) -> None:
    path = ROOT / filename
    rb.figure(str(path), caption, width_cm=width_cm)


def build(rb) -> None:
    rb.start_frontmatter("Phụ lục A — Hướng dẫn sử dụng")

    rb.p(
        "Phụ lục này hướng dẫn cách sử dụng tính năng đại diện "
        "nhất của hệ thống – luồng Campaign → Voucher – đi từ "
        "góc nhìn chủ doanh nghiệp (owner) tạo chiến dịch, qua "
        "vai trò công ty vận hành duyệt hồ sơ, đến khi khách "
        "hàng nhận voucher và nhân viên POS xác nhận tại quầy. "
        "Luồng đi qua 9 bước, mỗi bước đi kèm một ảnh chụp màn "
        "hình minh hoạ. Các tài khoản sử dụng là tài khoản demo "
        "được seed sẵn trong `backend/seed_demo.py`."
    )

    rb.h2("A.1. Bước 1 — Owner đăng nhập")
    rb.p(
        "Owner truy cập https://loyalty.ecom-bill.com/login, "
        "nhập email (ví dụ `owner@cafe.vn`) và mật khẩu (ví dụ "
        "`owner1234`). Hệ thống kiểm tra JWT + bcrypt, chuyển "
        "hướng tới /merchant và tự động chọn tenant đầu tiên mà "
        "owner có quyền."
    )

    rb.h2("A.2. Bước 2 — Truy cập trang Campaign")
    rb.p(
        "Từ sidebar merchant, owner chọn mục \"Chiến dịch\". "
        "Trang /merchant/campaigns liệt kê tất cả chiến dịch đã "
        "có của tenant cùng trạng thái (draft, pending_regulatory, "
        "approved, active, ended). Nhấn \"+ Tạo chiến dịch\" để "
        "mở wizard."
    )
    _img(rb, "merchant-polished-desktop.png",
         "Trang merchant — nơi bắt đầu tạo chiến dịch.")

    rb.h2("A.3. Bước 3 — Điền thông tin chiến dịch")
    rb.p(
        "Wizard gồm ba bước phụ: (a) Thông tin cơ bản – tên, "
        "mô tả, thời gian; (b) Cấu hình voucher – loại giảm "
        "giá (% hoặc amount), giá trị, max_issuances; (c) "
        "Đối tượng áp dụng – chọn tier được tham gia, có cho "
        "chia sẻ không. Sau khi xác nhận, hệ thống compute "
        "ngay `estimated_cost` và `approval_tier`, hiển thị "
        "banner \"Cần thông báo Sở Công Thương\" nếu tier > "
        "none."
    )

    rb.h2("A.4. Bước 4 — Nộp hồ sơ Sở Công Thương (nếu cần)")
    rb.p(
        "Trong trang chi tiết campaign, nếu "
        "`approval_tier=notify_so_ct` trở lên, owner bấm "
        "\"Nộp hồ sơ Sở Công Thương\". Hệ thống mở form để tải "
        "file hồ sơ (PDF công văn, bảng kê voucher, thẻ cào "
        "nếu có). Sau khi submit, trạng thái campaign chuyển "
        "thành `pending_regulatory`."
    )

    rb.h2("A.5. Bước 5 — Công ty vận hành duyệt")
    rb.p(
        "Super admin đăng nhập /admin, vào tab \"Campaigns "
        "chờ duyệt\", mở chi tiết, đối chiếu hồ sơ với quy "
        "định. Nếu hợp lệ, bấm \"Duyệt\" → campaign chuyển "
        "sang `approved`. Nếu cần chỉnh, bấm \"Từ chối\" kèm "
        "lý do, owner sẽ thấy lý do ở phần Lịch sử phê duyệt."
    )
    _img(rb, "admin-polished-desktop.png",
         "Admin portal — nơi duyệt hồ sơ campaign.")

    rb.h2("A.6. Bước 6 — Campaign chuyển sang active")
    rb.p(
        "Khi tới thời điểm `start_at`, cron hoặc service tự "
        "động chuyển campaign sang trạng thái `active`. Từ "
        "thời điểm này, khách hàng đủ điều kiện (đúng tier, "
        "chưa claim) sẽ thấy voucher khả dụng ở app /member."
    )

    rb.h2("A.7. Bước 7 — Khách hàng claim voucher")
    rb.p(
        "Khách mở app /member, vào tab \"Voucher\", bấm nút "
        "\"Nhận ngay\" trên campaign đang active. Request POST "
        "/campaigns/{id}/claim được gửi. Service lock advisory, "
        "UPDATE quota, INSERT voucher, commit. Voucher mới "
        "xuất hiện ở tab \"Voucher của tôi\"."
    )
    _img(rb, "voucher-detail-page-new.png",
         "Chi tiết voucher trên app khách hàng, có QR quét.")

    rb.h2("A.8. Bước 8 — Staff verify voucher tại POS")
    rb.p(
        "Khi khách đến quầy, staff mở /staff/pos, scan QR "
        "voucher của khách. Hệ thống trả về thông tin "
        "voucher + điều kiện áp dụng. Nếu phù hợp hóa đơn hiện "
        "tại, staff bấm \"Áp dụng\" – voucher chuyển sang "
        "`used`."
    )
    _img(rb, "staff-pos-voucher-applied.png",
         "Staff xác nhận voucher cho hóa đơn.")

    rb.h2("A.9. Bước 9 — Owner theo dõi thống kê")
    rb.p(
        "Trang chi tiết campaign ở portal merchant cập nhật "
        "số liệu claimed / used / remaining từ view "
        "`v_campaign_stats`. Owner có thể xuất báo cáo hậu "
        "khuyến mại (Nghị định 81 Điều 20) để gửi Sở Công "
        "Thương trong thời hạn 45 ngày."
    )
    rb.p(
        "Sau 9 bước trên, toàn bộ vòng đời của một chiến dịch "
        "khuyến mại đã được khép lại. Hệ thống cung cấp đầy đủ "
        "dấu vết audit log để chủ doanh nghiệp hoặc cơ quan "
        "quản lý có thể truy ngược từng thao tác nếu cần."
    )
