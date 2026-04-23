"""Chương 2 — Phương pháp thực hiện."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def build(rb) -> None:
    rb.start_chapter("Chương 2", "Phương pháp thực hiện")

    # ---------------- 2.1 ----------------
    rb.h2("2.1. Khảo sát hệ thống tương tự")
    rb.p(
        "Trước khi thiết kế hệ thống, đề tài tiến hành khảo sát bốn "
        "nền tảng loyalty tiêu biểu đang được sử dụng rộng rãi cho "
        "SME để xác định khoảng trống thị trường cũng như học hỏi "
        "các thông lệ tốt."
    )

    rb.h3("2.1.1. Got It Vietnam")
    rb.p(
        "Got It là nền tảng voucher quà tặng B2B hàng đầu Việt Nam, "
        "cho phép doanh nghiệp mua voucher từ các thương hiệu có "
        "sẵn để tặng khách hàng, nhân viên. Điểm mạnh là hệ sinh "
        "thái rộng (hơn 200 thương hiệu) và quy trình tích hợp API "
        "đơn giản. Tuy nhiên, Got It không hỗ trợ chương trình "
        "loyalty nội bộ – doanh nghiệp vẫn phải tự quản lý điểm "
        "thành viên và thẻ hạng. Giá dịch vụ cũng tương đối cao "
        "với SME ngân sách nhỏ."
    )

    rb.h3("2.1.2. Urbox")
    rb.p(
        "Urbox cũng là nền tảng voucher marketplace nhưng thêm "
        "tính năng ví điểm B2B2C: doanh nghiệp có thể nạp điểm "
        "cho nhân viên, khách hàng, họ dùng điểm đổi voucher trong "
        "marketplace. Mô hình này hợp với công ty lớn có chương "
        "trình phúc lợi nhân viên, nhưng ít phù hợp cho cửa hàng "
        "cà phê nhỏ – vốn cần tích điểm dựa trên hóa đơn thực tế "
        "và phát voucher riêng của chính cửa hàng."
    )

    rb.h3("2.1.3. Loyverse POS")
    rb.p(
        "Loyverse là bộ công cụ POS miễn phí kèm tính năng loyalty "
        "cơ bản: tích điểm theo tổng hóa đơn, đổi điểm lấy giảm "
        "giá. Ưu điểm: dễ dùng, có app mobile cho chủ cửa hàng. "
        "Nhược điểm: không multi-tenant thật sự – mỗi chủ cần tạo "
        "một tài khoản riêng, không chia sẻ khách hàng giữa các "
        "thương hiệu; không hỗ trợ pháp lý khuyến mại Việt Nam."
    )

    rb.h3("2.1.4. Smile.io / LoyaltyLion")
    rb.p(
        "Hai SaaS loyalty hàng đầu thị trường quốc tế, tích hợp "
        "sâu với Shopify. Giá trị cộng thêm là bộ UI kit kéo-thả "
        "cho phép chủ shop tự cấu hình chương trình khách hàng. "
        "Nhược điểm: thị trường mục tiêu là e-commerce Âu-Mỹ, "
        "không có module xử lý pháp lý khuyến mại theo NĐ 81 "
        "Việt Nam."
    )

    rb.h3("2.1.5. Bảng so sánh tính năng")
    rb.table(
        headers=["Tính năng", "Got It", "Urbox", "Loyverse", "Smile.io", "Đề tài"],
        rows=[
            ["Tích điểm theo hóa đơn", "Không", "Có", "Có", "Có", "Có"],
            ["Multi-tenant thật sự", "Có", "Có", "Không", "Một phần", "Có"],
            ["Voucher marketplace", "Có", "Có", "Không", "Không", "Không"],
            ["Chiến dịch khuyến mại", "Có", "Có", "Cơ bản", "Có", "Có"],
            ["Duyệt theo NĐ 81", "Không", "Không", "Không", "Không", "Có"],
            ["Ủy quyền công ty vận hành", "Không", "Không", "Không", "Không", "Có"],
            ["PWA offline", "Không", "Không", "Không", "Có", "Có"],
            ["QR cá nhân khách", "Có", "Có", "Có", "Có", "Có"],
            ["Chi phí cho SME", "Cao", "Trung bình", "Thấp", "Trung bình", "Quản trị"],
        ],
        caption="So sánh tính năng giữa các nền tảng loyalty và đề tài.",
    )
    rb.p(
        "Kết luận: đề tài lấp được khoảng trống mà các nền tảng "
        "hiện có chưa phục vụ – multi-tenant nghiêm ngặt kết hợp "
        "tuân thủ pháp lý khuyến mại Việt Nam cho nhóm SME."
    )

    # ---------------- 2.2 ----------------
    rb.h2("2.2. Công nghệ sử dụng")
    rb.p(
        "Việc chọn stack công nghệ dựa trên các tiêu chí: tốc độ "
        "phát triển, cộng đồng lớn, hệ sinh thái đầy đủ, tương "
        "thích PostgreSQL, hỗ trợ async tốt."
    )

    rb.h3("2.2.1. Backend")
    rb.bullet("FastAPI 0.115+ — framework Python async, auto-generate OpenAPI docs.")
    rb.bullet("SQLAlchemy 2.0 async + asyncpg — ORM hiện đại, driver PostgreSQL async.")
    rb.bullet("Alembic — quản lý migration, auto-run khi container khởi động.")
    rb.bullet("Pydantic v2 — DTO request/response, validate dữ liệu.")
    rb.bullet("slowapi — rate limiting, khóa theo IP.")
    rb.bullet("APScheduler — cron-like job runner.")
    rb.bullet("python-jose + bcrypt — JWT và băm mật khẩu.")
    rb.bullet("pytest + httpx + testcontainers-postgres — framework test.")

    rb.h3("2.2.2. Frontend")
    rb.bullet("Next.js 14 App Router + TypeScript — SSR + client component.")
    rb.bullet("Tailwind v4 + shadcn/ui — utility-first CSS + component library.")
    rb.bullet("TanStack Query — quản lý state dữ liệu server.")
    rb.bullet("Zustand — store client cho auth token và tenant chọn.")
    rb.bullet("react-hook-form + zod — form + validation.")
    rb.bullet("Serwist — service worker cho PWA offline.")
    rb.bullet("qrcode.react — sinh QR cá nhân khách hàng.")

    rb.h3("2.2.3. Cơ sở dữ liệu")
    rb.bullet("PostgreSQL 15 — hỗ trợ partial unique index, advisory lock, view.")
    rb.bullet("23 bảng nghiệp vụ + enum, FK với chiến lược CASCADE/SET NULL.")
    rb.bullet("View v_campaign_stats cho dashboard.")
    rb.bullet("Trigger voucher_validate_max_issuances chống over-issuance.")
    rb.bullet("Partial unique index cho membership theo (tenant, phone).")

    rb.h3("2.2.4. Hạ tầng triển khai")
    rb.bullet("Docker Compose — file dev (docker-compose.yml) và prod tách biệt.")
    rb.bullet("Cloudflare Tunnel — không mở port public, expose qua tunnel.")
    rb.bullet("Backend image ~ 150MB, frontend image ~ 200MB.")

    # ---------------- 2.3 ----------------
    rb.h2("2.3. Phương pháp luận")

    rb.h3("2.3.1. Kiến trúc thin-route / fat-service")
    rb.p(
        "Backend FastAPI được tổ chức theo mô hình \"thin route – "
        "fat service\": router `app/api/<resource>.py` chỉ parse "
        "request, gọi service tương ứng, map exception domain "
        "thành HTTPException và trả về schema. Mọi logic nghiệp "
        "vụ tập trung trong service – giúp tái sử dụng ở cron "
        "job, CLI hoặc unit test."
    )
    rb.p(
        "Global exception handler ở `app/main.py` bắt "
        "`sqlalchemy.exc.IntegrityError` chuyển thành HTTP 409 "
        "với thông điệp tiếng Việt. Router không cần try/except "
        "bao quanh mỗi INSERT."
    )

    rb.h3("2.3.2. Cô lập tenant qua header + dependency")
    rb.p(
        "Mọi endpoint phi-public đều bắt buộc header "
        "`X-Tenant-Id`. Dependency `get_tenant_id` kết hợp "
        "`get_current_user` tạo các dependency cao hơn: "
        "`require_staff_in_tenant`, `require_owner_in_tenant`, "
        "`require_customer_in_tenant`, `require_super_admin`. "
        "Thay đổi dependency tương đương thay đổi ai được phép "
        "gọi endpoint – tài liệu phân quyền rõ ràng."
    )

    rb.h3("2.3.3. Test-Driven Development cục bộ")
    rb.p(
        "Các module nghiệp vụ quan trọng (voucher, campaign, "
        "tenant authorization) được viết kèm unit test trước "
        "khi xây route. Integration test dùng testcontainers để "
        "khởi tạo PostgreSQL thật, chạy migration rồi test."
    )

    rb.h3("2.3.4. Quy trình Git")
    rb.p(
        "Mỗi tính năng phát triển trên branch riêng, commit "
        "messages tiếng Việt theo chuẩn Conventional Commits. "
        "Trước khi merge, đề tài dùng GitNexus để đánh giá "
        "blast radius của thay đổi, tránh refactor phá luồng."
    )

    # ---------------- 2.4 ----------------
    rb.h2("2.4. Phân tích nghiệp vụ")

    rb.h3("2.4.1. Các quy trình nghiệp vụ chính")
    rb.p(
        "Hệ thống bao trùm 11 quy trình nghiệp vụ cốt lõi. Bảng "
        "2-2 liệt kê từng quy trình cùng vai trò chủ động kích "
        "hoạt và mô tả ngắn."
    )
    rb.table(
        headers=["STT", "Quy trình", "Actor khởi tạo", "Tóm tắt"],
        rows=[
            ["1", "Đăng ký merchant", "Owner", "Đăng ký tenant 3 bước; super admin duyệt → kích hoạt."],
            ["2", "POS tích điểm", "Staff", "Scan QR khách, nhập tổng tiền, ghi transaction + cộng điểm."],
            ["3", "Đổi quà", "Customer", "Chọn reward, trừ điểm, sinh mã đổi quà tại POS."],
            ["4", "Tạo chiến dịch", "Owner", "Khai báo loại giảm giá, hạn mức; compute approval_tier."],
            ["5", "Nộp hồ sơ Sở CT", "Owner / Operator", "Khi tier ≥ notify; upload hồ sơ, nhận mã tham chiếu."],
            ["6", "Duyệt chiến dịch", "Super Admin / Sở CT", "Xem hồ sơ, bấm duyệt / từ chối."],
            ["7", "Claim voucher", "Customer", "Chiến dịch active, claim trong hạn mức, nhận voucher QR."],
            ["8", "Verify voucher POS", "Staff", "Quét QR voucher, kiểm tenant + status, mark used."],
            ["9", "Cron sinh nhật", "System", "Hằng ngày quét membership sinh nhật → phát voucher."],
            ["10", "Cron hậu khuyến mại", "System", "Quét chiến dịch đã đóng > 45 ngày chưa report → cảnh báo."],
            ["11", "Ủy quyền ký OTP", "Owner", "Tạo authorization, OTP, ký context_hash."],
        ],
        caption="Các quy trình nghiệp vụ chính.",
    )

    rb.h3("2.4.2. Sơ đồ chức năng tổng quát")
    rb.p(
        "Hệ thống được phân rã chức năng theo kiểu top-down "
        "(xem Hình 2-1). Gốc cây là toàn bộ nền tảng loyalty "
        "multi-tenant, được chia thành năm phân hệ chức năng "
        "lớn, mỗi phân hệ tiếp tục phân rã xuống các chức năng "
        "con có thể đo lường bằng endpoint API hoặc trang giao "
        "diện cụ thể."
    )
    rb.figure(
        str(ROOT / "bao-cao" / "assets" / "so_do_chuc_nang.png"),
        "Sơ đồ chức năng tổng quát của hệ thống.",
        width_cm=15.5,
    )
    rb.p(
        "Phân hệ thứ nhất – Xác thực & Phân quyền – phụ trách "
        "đăng ký, đăng nhập, cấp phát JWT, quản lý phiên, kiểm "
        "tra vai trò. Phân hệ thứ hai – Quản trị đa tenant – "
        "cung cấp super admin portal để duyệt tenant mới, "
        "khoá/mở doanh nghiệp, xem analytics toàn hệ thống. "
        "Phân hệ thứ ba – Nghiệp vụ loyalty – bao gồm tích "
        "điểm POS, đổi quà, quản lý thẻ hạng, lịch sử giao "
        "dịch. Phân hệ thứ tư – Khuyến mại & Tuân thủ pháp lý – "
        "quản lý chiến dịch, voucher, nộp hồ sơ Sở Công Thương, "
        "ký ủy quyền OTP. Phân hệ thứ năm – App khách hàng "
        "cuối – giao diện mobile-first cho customer."
    )

    rb.h3("2.4.3. Use case tổng quát")
    rb.p(
        "Sơ đồ use case tổng quát có năm actor: Super Admin "
        "(công ty vận hành), Owner (chủ doanh nghiệp SME), "
        "Staff (nhân viên POS), Customer (khách hàng cuối), "
        "System/Cron (tác nhân hệ thống cho job chạy nền). "
        "Mỗi actor được phân bổ tập use case tương ứng phạm vi "
        "quyền hạn – chi tiết từng use case được liệt kê ở "
        "Chương 3. Nguyên tắc chung: Customer không thao tác "
        "dữ liệu quản trị; Staff chỉ thực hiện tác vụ POS; "
        "Owner vận hành toàn bộ nghiệp vụ trong tenant của "
        "mình nhưng không thấy tenant khác; Super Admin có "
        "góc nhìn cross-tenant nhưng không truy xuất PII khách "
        "hàng trực tiếp."
    )

    rb.h3("2.4.4. Chu trình phát triển")
    rb.p(
        "Đề tài chia làm 16 phase, mỗi phase là milestone có "
        "thể demo độc lập. Phase 0 – khởi tạo repo, hạ tầng "
        "Docker. Phase 1-3 – backend cơ bản: auth, tenant, "
        "membership. Phase 4-6 – nghiệp vụ POS, transaction, "
        "reward. Phase 7-10 – campaign, voucher, redemption, "
        "tuân thủ NĐ 81. Phase 11-13 – ủy quyền OTP, cron "
        "jobs, audit log. Phase 14-16 – frontend hoàn thiện, "
        "PWA, E2E Playwright. Sau mỗi phase có review code, "
        "cập nhật migration và tài liệu."
    )
