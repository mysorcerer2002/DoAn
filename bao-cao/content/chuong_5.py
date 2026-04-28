"""Chương 5 — Kết luận."""
from __future__ import annotations


def build(rb) -> None:
    rb.start_chapter("Chương 5", "Kết luận")

    # ─────────────────────────────────────────────
    # 5.1 Đối chiếu kết quả vs mục tiêu
    # ─────────────────────────────────────────────
    rb.h2("5.1. ĐỐI CHIẾU KẾT QUẢ VỚI MỤC TIÊU")
    rb.p(
        "Sau khi hoàn thành toàn bộ quá trình phát triển và thử nghiệm, đề tài "
        "tiến hành đối chiếu từng mục tiêu đã đặt ra ở Chương 1.4 với kết quả "
        "thực tế đạt được. Bảng dưới đây tổng hợp trạng thái của từng mục tiêu "
        "cùng ghi chú về những phần còn cần cải thiện."
    )
    rb.table(
        headers=["STT", "Mục tiêu", "Trạng thái", "Ghi chú"],
        rows=[
            ["1", "Hệ thống multi-tenant hoạt động ổn định", "Đạt",
             "Nhiều partner (Cafe Cộng, Lala Food) vận hành song song; dữ liệu cô lập qua X-Partner-Id"],
            ["2", "Phân quyền 4 vai trò đầy đủ", "Đạt",
             "Super admin, Owner, Staff, Customer — mỗi endpoint khai báo đúng dependency tương ứng"],
            ["3", "Ví điểm toàn cục với CHECK >= 0", "Đạt",
             "CHECK constraint points_balance_nonneg trên DB; verify qua smoke test trừ quá số dư bị chặn"],
            ["4", "Append-only ledger có trigger DB", "Đạt",
             "Trigger no_update_or_delete_point_ledger xác nhận qua psql direct; không thể UPDATE/DELETE"],
            ["5", "Smoke E2E các luồng cốt lõi", "Đạt",
             "Tất cả 27 kịch bản pass qua curl + browser manual trên loyalty.ecom-bill.com"],
            ["6", "Dashboard merchant analytics", "Đạt",
             "6 KPI + 2 chart + Top 5 quà; dữ liệu khớp với transactions và redemptions trong DB"],
            ["7", "Admin giám sát điểm hệ thống", "Đạt",
             "Trang system-points đọc đúng SUM(points_balance) và breakdown từ point_ledger"],
            ["8", "Deploy Docker Compose + Cloudflare Tunnel", "Đạt",
             "Prod chạy sạch; migration auto-run khi container khởi động; accessible qua loyalty.ecom-bill.com"],
            ["9", "Báo cáo và HDSD đầy đủ", "Đạt",
             "Báo cáo đồ án hoàn chỉnh; HDSD mô tả luồng đăng ký → đổi quà kèm hình minh họa"],
        ],
        caption="Đối chiếu mục tiêu và kết quả thực tế của đề tài."
    )
    rb.p(
        "Nhìn chung, toàn bộ chín mục tiêu của đề tài đều đạt ở mức yêu cầu tối "
        "thiểu. Các chức năng cốt lõi — tích điểm, đổi quà, quản lý partner, "
        "giám sát điểm — đều hoạt động đúng trên môi trường production. "
        "Tuy nhiên, vẫn còn một số hạn chế kỹ thuật cần được ghi nhận trung thực "
        "và sẽ được trình bày trong mục tiếp theo."
    )

    # ─────────────────────────────────────────────
    # 5.2 Vấn đề còn tồn đọng
    # ─────────────────────────────────────────────
    rb.h2("5.2. VẤN ĐỀ CÒN TỒN ĐỌNG")

    rb.h3("5.2.1. Giới hạn kiểm thử tự động (pytest infra gap)")
    rb.p(
        "Do đặc thù môi trường phát triển Windows, bộ integration test dùng "
        "testcontainers không thể chạy hoàn chỉnh vì thư viện này yêu cầu "
        "quyền truy cập docker.sock và cấu hình Docker network bridge mà "
        "môi trường hiện tại không đáp ứng được đầy đủ. Đây là khoảng trống "
        "kỹ thuật cần giải quyết trong tương lai: lý tưởng nhất là thiết lập "
        "môi trường CI/CD trên Linux (GitHub Actions hoặc GitLab CI) để chạy "
        "integration test tự động sau mỗi commit, thay thế hoàn toàn cho "
        "quy trình kiểm thử thủ công hiện tại."
    )

    rb.h3("5.2.2. Frontend bundle size chưa được tối ưu")
    rb.p(
        "Bộ frontend Next.js 14 hiện tại chưa được tối ưu sâu về bundle size. "
        "Một số page component load toàn bộ thư viện charting dù chỉ cần dùng "
        "một phần nhỏ, dẫn đến First Load JS khá lớn trên các trang dashboard. "
        "Việc áp dụng dynamic import và lazy loading cho các chart component "
        "sẽ cải thiện đáng kể thời gian tải trang đầu tiên, đặc biệt trên "
        "kết nối di động."
    )

    rb.h3("5.2.3. Chưa có xác thực hai yếu tố (2FA) cho admin")
    rb.p(
        "Tài khoản super admin có quyền hạn cao nhất trong hệ thống: duyệt "
        "partner, xem toàn bộ log và giám sát điểm. Hiện tại, xác thực chỉ "
        "dựa trên JWT một lớp. Việc bổ sung 2FA (ví dụ TOTP qua Google "
        "Authenticator hoặc OTP qua email) cho tài khoản admin sẽ giảm đáng "
        "kể rủi ro nếu token bị đánh cắp."
    )

    rb.h3("5.2.4. Audit log chưa phủ toàn bộ action")
    rb.p(
        "Hiện tại, hệ thống chỉ có audit log cho hai loại sự kiện: đăng nhập "
        "(bảng login_logs) và điều chỉnh điểm thủ công (bảng point_ledger với "
        "reason=adjust). Các hành động quan trọng khác như duyệt/từ chối "
        "partner, sửa thông tin reward, khoá tài khoản thành viên chưa có "
        "audit trail. Một bảng audit_events tổng quát ghi lại mọi hành động "
        "có side effect sẽ là cải thiện đáng kể cho tính minh bạch và "
        "khả năng điều tra sự cố."
    )

    rb.h3("5.2.5. SMTP fail-silent có thể gây nhầm lẫn cho người dùng")
    rb.p(
        "Cơ chế fail-silent cho SMTP giúp bảo mật bằng cách không tiết lộ "
        "email nào tồn tại. Tuy nhiên, người dùng thực sự quên mật khẩu sẽ "
        "không nhận được thông báo nếu email không được gửi — họ chỉ thấy "
        "'Thành công' mà không nhận email. Giải pháp phù hợp cho sản xuất là "
        "xây dựng dashboard SMTP log cho admin xem các email gửi thất bại, "
        "hoặc retry queue để tự động gửi lại khi SMTP phục hồi."
    )

    rb.h3("5.2.6. Multi-tenant Shared Schema thiếu defense-in-depth ở tầng DB")
    rb.p(
        "Mô hình Shared Schema được lựa chọn để giữ chi phí vận hành thấp và "
        "phù hợp với scope đồ án. Tuy nhiên, cô lập dữ liệu giữa các partner "
        "hiện chỉ dựa trên application-level filter (mỗi query đều thêm điều "
        "kiện partner_id = X) và dependency require_owner_in_tenant. Nếu một "
        "endpoint trong tương lai quên thêm filter, dữ liệu của partner khác "
        "có thể bị rò rỉ. Giải pháp tiêu chuẩn công nghiệp là bật PostgreSQL "
        "Row-Level Security (RLS) — tạo policy ràng buộc row trả về phải có "
        "partner_id khớp với biến session current_setting('app.partner_id'). "
        "Khi đó, ngay cả khi application code có lỗi cũng không thể đọc dữ "
        "liệu sai tenant. Đây là cải tiến quan trọng cần thực hiện trước khi "
        "đưa hệ thống lên môi trường multi-tenant thực sự."
    )

    rb.h3("5.2.7. Append-only ledger không kháng được tấn công ở tầng superuser")
    rb.p(
        "Trigger no_update_or_delete_point_ledger chặn mọi UPDATE/DELETE từ "
        "application code và các tài khoản DB thường. Tuy nhiên, người có "
        "quyền superuser PostgreSQL vẫn có thể DROP TRIGGER, sửa dữ liệu, "
        "rồi tạo lại trigger — toàn bộ thao tác này không để lại dấu vết "
        "trong ledger. Đây là giới hạn cố hữu của bất kỳ trigger-based "
        "approach nào. Hai giải pháp triệt để: (a) bật pgaudit để log "
        "DDL/DML có quyền cao và push log sang hệ thống lưu trữ riêng "
        "ngoài tầm kiểm soát của DB admin; (b) chuyển sang hash-chained "
        "ledger — mỗi ledger entry chứa hash của entry trước đó, do đó bất "
        "kỳ thay đổi nào ở giữa chuỗi cũng sẽ phá vỡ chuỗi hash và bị "
        "phát hiện khi đối soát định kỳ. Hướng (b) là giải pháp đầy đủ "
        "nhất nhưng vượt scope đồ án."
    )

    rb.h3("5.2.8. JWT 24 giờ không có cơ chế revoke khi đổi password")
    rb.p(
        "Access token JWT hiện tại có thời gian sống 24 giờ và là stateless "
        "(server không lưu trạng thái token). Khi user đổi password hoặc "
        "owner khoá tài khoản nhân viên, các access token đã phát từ trước "
        "vẫn còn hiệu lực trong tối đa 24 giờ — tạo ra một cửa sổ rủi ro "
        "nhất định. Giải pháp tiêu chuẩn là thêm một tầng Redis blocklist: "
        "(1) mỗi JWT thêm trường jti (JWT ID) duy nhất và iat (issued-at); "
        "(2) khi user đổi password, lưu users.password_changed_at vào DB; "
        "(3) middleware kiểm tra mỗi request: nếu token.iat < user."
        "password_changed_at thì reject. Cách này không yêu cầu truy vấn "
        "Redis nếu password_changed_at được cache trong JWT của session "
        "tiếp theo. Trong scope đồ án, lựa chọn JWT 24 giờ + dependency "
        "require_staff_in_tenant đọc lại is_active mỗi request đã giảm bề "
        "mặt rủi ro xuống mức chấp nhận được, nhưng đây vẫn là điểm cần "
        "hoàn thiện trước khi triển khai sản xuất quy mô lớn."
    )

    # ─────────────────────────────────────────────
    # 5.3 Mở rộng (luận văn tốt nghiệp)
    # ─────────────────────────────────────────────
    rb.h2("5.3. HƯỚNG MỞ RỘNG (LUẬN VĂN TỐT NGHIỆP)")
    rb.p(
        "Nền tảng hiện tại đã chứng minh tính khả thi về mặt kỹ thuật cho các "
        "chức năng loyalty cốt lõi. Trong khuôn khổ luận văn tốt nghiệp, đề tài "
        "có thể được phát triển theo các hướng sau, mỗi hướng đều có giá trị "
        "nghiên cứu và ứng dụng thực tế rõ ràng."
    )
    rb.p(
        "Hướng mở rộng thứ nhất là hệ thống campaign khuyến mại có tuân thủ "
        "pháp lý Nghị định 81/2018/NĐ-CP. Đây là hướng có giá trị phân biệt "
        "cao nhất so với các giải pháp cạnh tranh: tự động phân loại tier "
        "pháp lý (không thông báo / thông báo Sở Công Thương / đăng ký Sở / "
        "đăng ký Bộ) dựa trên tổng giá trị khuyến mại ước tính, xây dựng "
        "luồng nộp hồ sơ điện tử và nhắc nhở báo cáo sau khuyến mại trong 45 ngày. "
        "Đây cũng là điểm khác biệt giúp nền tảng định vị như một managed "
        "service thay vì chỉ là phần mềm."
    )
    rb.p(
        "Hướng mở rộng thứ hai là hệ thống tier hạng thành viên với chính sách "
        "ưu đãi theo hạng (Đồng / Bạc / Vàng / Kim Cương). Tier được xác định "
        "dựa trên lifetime_earned của từng membership tại từng partner — đã "
        "có cột này trong schema hiện tại. Khi lên hạng, thành viên nhận "
        "được benefit khác nhau: tỉ lệ cộng điểm cao hơn, ưu tiên phục vụ "
        "hoặc voucher chào mừng hạng mới."
    )
    rb.p(
        "Hướng mở rộng thứ ba là service fee thật và tích hợp cổng thanh toán "
        "(VNPay hoặc MoMo). Mô hình kinh doanh của nền tảng là thu phí theo "
        "giá trị khuyến mại hoặc theo số lượng transaction — code data model "
        "đã có placeholder trong schema nhưng chưa kích hoạt. Tích hợp cổng "
        "thanh toán nội địa sẽ hoàn chỉnh vòng đời thương mại của sản phẩm."
    )
    rb.p(
        "Hướng mở rộng thứ tư là Progressive Web App (PWA) offline-ready với "
        "Serwist Service Worker. Tại thời điểm hiện tại, app chạy hoàn toàn "
        "online. Bổ sung PWA cho phép khách hàng xem QR cá nhân và ví voucher "
        "ngay cả khi không có kết nối mạng — rất hữu ích khi wifi cửa hàng "
        "không ổn định tại thời điểm thanh toán."
    )
    rb.p(
        "Hướng mở rộng thứ năm là ứng dụng native mobile (React Native hoặc "
        "Flutter). Mặc dù web app đã được thiết kế mobile-first, các tính năng "
        "như push notification khi được tặng điểm, biometric authentication "
        "và camera scan QR nhanh hơn đòi hỏi khả năng của native app. "
        "Kiến trúc backend RESTful hiện tại có thể phục vụ native app mà "
        "không cần thay đổi."
    )
    rb.p(
        "Hướng mở rộng thứ sáu là ứng dụng machine learning trong hai bài toán: "
        "gợi ý quà phù hợp cho từng khách hàng dựa trên lịch sử giao dịch và "
        "redemption (collaborative filtering hoặc content-based), và dự báo "
        "tỉ lệ rời bỏ (churn prediction) để chủ partner có thể chủ động "
        "gửi incentive giữ chân khách hàng có nguy cơ cao."
    )
    rb.p(
        "Hướng mở rộng thứ bảy là bảo mật nâng cao: 2FA (TOTP) cho tài khoản "
        "admin và owner, audit log toàn diện cho mọi action có side effect, "
        "và dashboard SMTP monitoring để theo dõi tỉ lệ gửi email thành công. "
        "Các cải thiện này cần thiết trước khi nền tảng được triển khai ở "
        "quy mô thương mại thực sự."
    )
