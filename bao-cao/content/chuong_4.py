"""Chương 4 — Thử nghiệm."""
from __future__ import annotations


def build(rb) -> None:
    rb.start_chapter("Chương 4", "Thử nghiệm")

    # ─────────────────────────────────────────────
    # 4.1 Kịch bản thử nghiệm
    # ─────────────────────────────────────────────
    rb.h2("4.1. KỊCH BẢN THỬ NGHIỆM")
    rb.p(
        "Bảng dưới đây liệt kê các kịch bản thử nghiệm được xây dựng để phủ toàn "
        "bộ các module trong phạm vi đề tài. Các kịch bản được nhóm theo domain "
        "nghiệp vụ và ưu tiên theo mức độ rủi ro: các luồng happy path cần "
        "chạy trước, sau đó là các trường hợp biên và lỗi nghiệp vụ."
    )
    rb.table(
        headers=["STT", "Module", "Kịch bản", "Đầu vào", "Kết quả kỳ vọng"],
        rows=[
            # Auth
            ["1", "Auth", "Đăng ký thành công", "Email mới, password >= 8 ký tự", "HTTP 201, user được tạo, có thể đăng nhập ngay"],
            ["2", "Auth", "Đăng ký email đã tồn tại", "Email đã dùng", "HTTP 409, thông báo email đã tồn tại bằng tiếng Việt"],
            ["3", "Auth", "Đăng nhập thành công", "Email + password đúng", "HTTP 200, access_token JWT hợp lệ"],
            ["4", "Auth", "Đăng nhập sai mật khẩu", "Email đúng, password sai", "HTTP 401, thông báo lỗi"],
            ["5", "Auth", "Quên mật khẩu (gửi temp pass)", "Email hợp lệ đã đăng ký", "HTTP 200 bất kể SMTP lỗi hay không; backend ghi log"],
            # Partner
            ["6", "Partner", "Đăng ký merchant — trạng thái PENDING", "Form đăng ký đầy đủ", "HTTP 201, partner.status = 'pending'"],
            ["7", "Partner", "Admin approve — seed 1 triệu điểm", "Admin POST /admin/partners/{id}/approve", "HTTP 200; partner.status = 'active'; point_ledger có entry +1.000.000"],
            ["8", "Partner", "Admin reject merchant", "Admin POST /admin/partners/{id}/reject", "HTTP 200; partner status không chuyển ACTIVE"],
            # Member
            ["9", "Member", "Xem điểm hiện tại", "Customer đã đăng nhập", "HTTP 200, trả points_balance chính xác"],
            ["10", "Member", "Xem QR cá nhân", "Customer đã đăng nhập, GET /member/qr", "HTTP 200, payload chứa user_id có thể decode"],
            ["11", "Member", "Danh sách đối tác", "GET /partners (public)", "HTTP 200, chỉ trả partner status=active"],
            ["12", "Member", "Chi tiết đối tác + danh sách quà", "GET /partners/{id} kèm rewards", "HTTP 200, rewards chỉ gồm is_active=True và chưa bị xóa"],
            # POS
            ["13", "POS", "Tích điểm happy path", "user_id hợp lệ, gross_amount=100.000đ", "HTTP 201, points_earned=10, ledger entry +10, balance tăng 10"],
            ["14", "POS", "Tích điểm với mã hóa đơn trùng", "receipt_code đã dùng trong cùng partner", "HTTP 409, không tạo transaction mới"],
            ["15", "POS", "Verify reward ITEM_GIFT", "redemption_code hợp lệ, status=PENDING", "HTTP 200; redemption.status → USED; used_at được ghi"],
            ["16", "POS", "Verify reward PERCENT_DISCOUNT", "redemption_code hợp lệ, offer_type PERCENT", "HTTP 200; trả original_amount và discount_amount"],
            # Reward CRUD
            ["17", "Reward", "Tạo quà FIXED_DISCOUNT thành công", "points_cost=500, offer_value=50000", "HTTP 201, reward được tạo với offer_type=FIXED_DISCOUNT"],
            ["18", "Reward", "Tạo quà PERCENT_DISCOUNT thành công", "points_cost=200, offer_value=20 (%)", "HTTP 201, reward.offer_value=20, check 1–100 pass"],
            ["19", "Reward", "Tạo quà ITEM_GIFT thành công", "points_cost=1000, offer_value=NULL", "HTTP 201, offer_value=NULL theo constraint"],
            ["20", "Reward", "Sửa quà — đổi offer_type bị từ chối", "PATCH reward với offer_type khác", "HTTP 422, thông báo offer_type không được thay đổi"],
            ["21", "Reward", "Soft delete quà", "DELETE /rewards/{id}", "HTTP 200; reward.deleted_at được ghi; không xuất hiện trong danh sách public"],
            # Đổi quà
            ["22", "Redemption", "Đổi quà thành công", "user.points_balance >= reward.points_cost", "HTTP 201; redemption code 8 ký tự; balance giảm; ledger delta âm"],
            ["23", "Redemption", "Đổi quà thiếu điểm", "user.points_balance < reward.points_cost", "HTTP 400, thông báo không đủ điểm"],
            ["24", "Redemption", "Đổi quà reward hết stock", "reward.stock = 0", "HTTP 409, thông báo hết hàng"],
            # Admin
            ["25", "Admin", "Xem log đăng nhập", "GET /admin/login-logs", "HTTP 200, danh sách phân trang đúng"],
            ["26", "Admin", "Xem điểm hệ thống", "GET /admin/system-points", "HTTP 200, tổng điểm = SUM(points_balance) tất cả users"],
            ["27", "Admin", "Xem log adjustment", "GET /admin/system-points/logs", "HTTP 200, danh sách điều chỉnh phân trang"],
        ],
        caption="Danh sách kịch bản thử nghiệm theo module và đầu vào kỳ vọng."
    )

    # ─────────────────────────────────────────────
    # 4.2 Kết quả thử nghiệm
    # ─────────────────────────────────────────────
    rb.h2("4.2. KẾT QUẢ THỬ NGHIỆM")
    rb.p(
        "Do đặc thù môi trường phát triển trên Windows, testcontainers — thư viện "
        "dùng để spin up PostgreSQL tạm thời cho integration test trong pytest — "
        "yêu cầu quyền truy cập docker.sock và cấu hình Docker network mà không "
        "thể đáp ứng đầy đủ trên môi trường hiện tại. Vì vậy, đề tài kết hợp "
        "hai phương pháp kiểm thử: smoke E2E qua curl gọi trực tiếp trên "
        "production URL loyalty.ecom-bill.com (với dữ liệu demo seed sẵn), "
        "và kiểm thử thủ công từng luồng qua trình duyệt với tài khoản demo. "
        "Các kết quả dưới đây phản ánh trạng thái thực tế của hệ thống."
    )
    rb.table(
        headers=["STT", "Kịch bản", "Phương pháp", "Trạng thái", "Ghi chú"],
        rows=[
            ["1", "Đăng ký thành công", "curl POST /auth/register", "PASS", ""],
            ["2", "Đăng ký email trùng", "curl POST /auth/register", "PASS", "HTTP 409 + message tiếng Việt"],
            ["3", "Đăng nhập thành công", "curl POST /auth/login", "PASS", "Trả JWT hợp lệ"],
            ["4", "Đăng nhập sai password", "curl POST /auth/login", "PASS", "HTTP 401"],
            ["5", "Quên mật khẩu", "curl + manual email check", "PASS", "SMTP fail-silent hoạt động đúng"],
            ["6", "Đăng ký merchant PENDING", "Browser manual", "PASS", "partner.status = pending sau khi submit"],
            ["7", "Admin approve + seed điểm", "Browser manual (admin)", "PASS", "Ledger entry +1.000.000 xác nhận qua psql"],
            ["8", "Admin reject merchant", "Browser manual (admin)", "PASS", ""],
            ["9", "Xem điểm hiện tại", "curl GET /users/me", "PASS", "points_balance chính xác"],
            ["10", "QR cá nhân", "Browser manual", "PASS", "QR hiển thị đúng, scan được"],
            ["11", "Danh sách đối tác", "curl GET /partners", "PASS", "Chỉ trả partner active"],
            ["12", "Chi tiết đối tác + rewards", "curl GET /partners/{id}", "PASS", ""],
            ["13", "Tích điểm happy path", "curl POST /staff/transactions", "PASS", "Điểm cộng đúng; ledger có entry"],
            ["14", "Tích điểm mã hóa đơn trùng", "curl POST /staff/transactions", "PASS", "HTTP 409"],
            ["15", "Verify reward ITEM_GIFT", "curl POST /staff/verify-reward", "PASS", "Status → USED"],
            ["16", "Verify reward PERCENT_DISCOUNT", "curl POST /staff/verify-reward", "PASS", "discount_amount trả về đúng"],
            ["17–19", "Tạo 3 loại quà", "Browser manual (owner)", "PASS", ""],
            ["20", "Sửa offer_type bị reject", "curl PATCH /rewards/{id}", "PASS", "HTTP 422"],
            ["21", "Soft delete quà", "Browser manual (owner)", "PASS", "Quà ẩn khỏi danh sách public"],
            ["22", "Đổi quà thành công", "Browser manual (member)", "PASS", "Redemption code 8 ký tự tạo đúng"],
            ["23", "Đổi quà thiếu điểm", "curl POST /redeem", "PASS", "HTTP 400"],
            ["24", "Đổi quà hết stock", "Browser manual", "PASS", "HTTP 409"],
            ["25–27", "Admin: log, điểm, adjustment", "Browser manual (admin)", "PASS", "Tất cả trang hiển thị dữ liệu đúng"],
        ],
        caption="Kết quả thử nghiệm các kịch bản."
    )
    rb.p(
        "Về hiệu năng, đề tài thực hiện một số kiểm tra cơ bản trên production "
        "URL. Rate limit slowapi hoạt động đúng: gửi liên tục hơn 30 request "
        "login/phút từ cùng IP nhận được HTTP 429. Thời gian phản hồi P95 của "
        "các endpoint thường dùng (GET /partners, POST /transactions) dao động "
        "trong khoảng 120–280ms trên môi trường production với Cloudflare Tunnel, "
        "đủ để đảm bảo trải nghiệm người dùng tốt trong điều kiện thực tế."
    )

    # ─────────────────────────────────────────────
    # 4.3 Xử lý ngoại lệ
    # ─────────────────────────────────────────────
    rb.h2("4.3. XỬ LÝ NGOẠI LỆ")

    rb.h3("4.3.1. Bảo vệ points_balance >= 0 — ba lớp phòng thủ")
    rb.p(
        "Đảm bảo số dư điểm không bao giờ về âm là một trong những ràng buộc "
        "quan trọng nhất của hệ thống. Đề tài triển khai ba lớp bảo vệ phối hợp "
        "để chắc chắn ràng buộc này không bị phá vỡ ở bất kỳ tình huống nào. "
        "Lớp thứ nhất là validation ở tầng Pydantic: schema yêu cầu amount > 0 "
        "cho mọi request trừ điểm, loại bỏ các input không hợp lệ ngay tại cổng "
        "vào API. Lớp thứ hai là kiểm tra số dư trong service trước khi thực hiện "
        "bất kỳ thao tác trừ điểm nào — service đọc points_balance hiện tại và so "
        "sánh với số điểm cần trừ, raise exception nếu không đủ. Lớp thứ ba là "
        "CHECK constraint points_balance_nonneg trực tiếp trên bảng users trong "
        "PostgreSQL — dù có bug ở hai lớp trên, database vẫn từ chối bất kỳ "
        "UPDATE nào đưa giá trị về âm và raise IntegrityError."
    )

    rb.h3("4.3.2. Append-only ledger và trigger bảo vệ")
    rb.p(
        "Tính bất biến của sổ cái điểm là yếu tố cốt lõi để đảm bảo khả năng "
        "kiểm toán lâu dài. Nếu dữ liệu lịch sử có thể bị sửa hoặc xóa, "
        "không còn cơ sở để xác nhận số dư hiện tại là chính xác hay đã bị "
        "can thiệp. Trigger no_update_or_delete_point_ledger trong PostgreSQL "
        "được định nghĩa bằng PL/pgSQL và gắn vào bảng point_ledger với "
        "BEFORE UPDATE OR DELETE: khi bất kỳ lệnh UPDATE hay DELETE nào cố "
        "gắng chạy trên bảng này, trigger raise EXCEPTION ngay lập tức, "
        "hủy transaction và trả lỗi. Điều này đảm bảo ngay cả admin hệ thống "
        "cũng không thể sửa lịch sử điểm thông qua kết nối trực tiếp vào database. "
        "Khi cần hiệu chỉnh sai sót, giải pháp duy nhất hợp lệ là tạo một "
        "compensation entry mới với delta ngược chiều và ghi rõ lý do."
    )

    rb.h3("4.3.3. Reward offer_type bất biến")
    rb.p(
        "Trường offer_type của Reward xác định cách tính giảm giá khi khách đổi "
        "quà tại POS: PERCENT_DISCOUNT tính phần trăm, FIXED_DISCOUNT trừ số tiền "
        "cố định, ITEM_GIFT tặng món hàng. Nếu cho phép thay đổi offer_type sau "
        "khi đã có redemption dựa trên quà đó, dữ liệu lịch sử sẽ mất nhất quán. "
        "Đề tài ngăn chặn điều này bằng cách kiểm tra trường offer_type trong "
        "Pydantic schema của PATCH request: nếu payload chứa offer_type khác với "
        "giá trị hiện tại, schema validator raise ValueError và Pydantic trả "
        "HTTP 422 với message rõ ràng trước khi request chạm tới service."
    )

    rb.h3("4.3.4. Email SMTP fail-silent")
    rb.p(
        "Luồng quên mật khẩu gửi temporary password qua email. Tuy nhiên, nếu "
        "backend trả HTTP 500 hay HTTP 404 khi SMTP lỗi, kẻ tấn công có thể "
        "dùng sự khác biệt trong response để suy ra email nào đã đăng ký "
        "trong hệ thống. Đề tài áp dụng cơ chế fail-silent: dù email có tồn "
        "tại hay không, dù SMTP gửi thành công hay thất bại, backend luôn trả "
        "HTTP 200 với cùng một message trung lập. Nếu SMTP lỗi, backend ghi "
        "một dòng log WARNING chứa user_id và thông tin lỗi để admin có thể "
        "theo dõi qua docker logs — nhưng khách hàng không nhận thông báo lỗi "
        "và không biết gì thêm về trạng thái email của mình trong hệ thống."
    )

    rb.h3("4.3.5. Xử lý trùng phone/email — global exception handler")
    rb.p(
        "Khi người dùng đăng ký với email hoặc số điện thoại đã tồn tại trong "
        "hệ thống, PostgreSQL raise IntegrityError với thông báo chứa tên "
        "unique index bị vi phạm (ix_users_email_unique hoặc ix_users_phone_unique). "
        "Thay vì để lỗi này rò rỉ ra ngoài dưới dạng HTTP 500, backend có một "
        "global exception handler trong app/main.py bắt sqlalchemy.exc.IntegrityError, "
        "phân tích tên constraint trong thông báo lỗi và ánh xạ sang HTTP 409 "
        "với message tiếng Việt phù hợp (ví dụ: 'Email đã được sử dụng'). "
        "Cơ chế này tập trung logic xử lý uniqueness tại một chỗ duy nhất, "
        "tránh phải thêm try-except cho từng endpoint."
    )
