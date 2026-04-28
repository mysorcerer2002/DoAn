"""Chương 3 — Thiết kế hệ thống."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # D:/DoAn


def _img(rb, filename: str, caption: str, width_cm: float = 14.0) -> None:
    path = ROOT / filename
    rb.figure(str(path), caption, width_cm=width_cm)


def build(rb) -> None:
    rb.start_chapter("Chương 3", "Thiết kế hệ thống")

    # ─────────────────────────────────────────────
    # 3.1 Mô hình dữ liệu
    # ─────────────────────────────────────────────
    rb.h2("3.1. MÔ HÌNH DỮ LIỆU")
    rb.p(
        "Chương này trình bày thiết kế cơ sở dữ liệu của hệ thống theo ba mức: "
        "mức ý niệm (Conceptual Data Model), mức luận lý (Logical Data Model) và "
        "mức vật lý (Physical Data Model). Mỗi mức đi từ trừu tượng đến chi tiết, "
        "đảm bảo thiết kế vừa phản ánh đúng nghiệp vụ vừa có thể hiện thực hóa "
        "bằng PostgreSQL 15."
    )

    rb.h3("3.1.1. Mức ý niệm (Conceptual)")
    rb.p(
        "Ở mức ý niệm, hệ thống được mô hình hóa thành chín thực thể chính phản "
        "ánh các đối tượng nghiệp vụ cốt lõi. Mỗi thực thể đại diện cho một "
        "khái niệm nghiệp vụ độc lập và có quan hệ rõ ràng với các thực thể "
        "xung quanh. Sơ đồ ERD tổng thể được trình bày trong hình dưới đây, "
        "còn bảng kế tiếp mô tả vai trò của từng thực thể."
    )
    rb.p(
        "Lưu ý về TimestampMixin: hai cột created_at và updated_at được khai báo "
        "tập trung trong lớp TimestampMixin của tệp app/models/base.py, sau đó "
        "được kế thừa vào hầu hết các bảng (User, Partner, PartnerStaff, "
        "Membership, Reward, Redemption, Transaction, PointLedger). Đây là "
        "kỹ thuật mixin của Python để tránh lặp code, không phải một bảng "
        "riêng — vì vậy ERD chỉ vẽ chín thực thể nghiệp vụ và liệt kê "
        "created_at / updated_at trực tiếp bên trong mỗi thực thể."
    )
    _img(rb, "bao-cao/assets/uml/erd.png", "ERD tổng thể chín thực thể chính của hệ thống.")
    rb.table(
        headers=["Entity", "Mô tả", "Quan hệ chính"],
        rows=[
            ["User", "Người dùng hệ thống — khách hàng, chủ partner, nhân viên hoặc admin; ví điểm toàn cục points_balance ≥ 0", "1 User → nhiều Membership (qua từng partner)"],
            ["Partner", "Doanh nghiệp đối tác tham gia nền tảng loyalty", "1 Partner → nhiều Membership, Reward, Transaction"],
            ["PartnerStaff", "Liên kết nhân viên với partner (role staff)", "1 User ↔ tối đa 1 Partner qua PartnerStaff (uniq user_id)"],
            ["Membership", "Quan hệ khách hàng – partner; lưu lifetime_earned cho hạng thành viên", "UNIQUE(partner_id, user_id) → 1 Membership"],
            ["Reward", "Phần thưởng có thể đổi điểm: PERCENT_DISCOUNT, FIXED_DISCOUNT, ITEM_GIFT", "1 Partner → nhiều Reward"],
            ["Redemption", "Lệnh đổi quà; mang redemption_code 8 ký tự để dùng tại POS", "1 User + 1 Reward → nhiều Redemption"],
            ["Transaction", "Giao dịch POS tích điểm cho khách hàng", "1 Membership → nhiều Transaction"],
            ["PointLedger", "Sổ cái điểm append-only ghi mọi biến động (earn / redeem / adjust / expire / refund). Cột actor_user_id ghi nhận chủ shop khi điều chỉnh thủ công", "1 User → nhiều entry (cross-partner)"],
            ["LoginLog", "Nhật ký đăng nhập (thành công / thất bại) để admin kiểm toán", "1 User → nhiều LoginLog"],
        ],
        caption="Chín thực thể chính và quan hệ ở mức ý niệm."
    )
    rb.p(
        "Việc điều chỉnh điểm thủ công của chủ shop không có bảng riêng: "
        "mỗi lần điều chỉnh chỉ INSERT một bản ghi vào point_ledger với "
        "reason = 'adjust', actor_user_id = chủ shop và description = lý do. "
        "Cách này tận dụng được trigger append-only của point_ledger nên không "
        "thể UPDATE / DELETE để xoá dấu vết, đồng thời tránh trùng lặp dữ liệu "
        "với một bảng PointAdjustment riêng."
    )

    rb.h3("3.1.2. Mức luận lý (Logical)")
    rb.p(
        "Ở mức luận lý, các thực thể được chuyển thành các bảng quan hệ với khóa "
        "chính, khóa ngoại và các ràng buộc tính nhất quán. Thiết kế tuân theo "
        "chuẩn 3NF (Third Normal Form) để tránh dư thừa dữ liệu. Bảng dưới đây "
        "mô tả năm bảng trung tâm với các ràng buộc quan trọng nhất."
    )
    rb.table(
        headers=["Bảng", "Khóa chính (PK)", "Khóa ngoại (FK) chính", "Ràng buộc unique / check"],
        rows=[
            ["users", "id (serial)", "—", "UNIQUE(email) partial WHERE email IS NOT NULL; CHECK points_balance >= 0"],
            ["partners", "id (serial)", "owner_user_id → users.id", "UNIQUE(slug); status IN ('pending','active','suspended')"],
            ["memberships", "id (serial)", "partner_id → partners.id; user_id → users.id", "UNIQUE(partner_id, user_id); CHECK lifetime_earned >= 0"],
            ["rewards", "id (serial)", "partner_id → partners.id", "CHECK points_cost > 0; CHECK offer_value hợp lệ theo offer_type"],
            ["redemptions", "id (serial)", "partner_id, user_id, reward_id → FK tương ứng", "UNIQUE(partner_id, redemption_code); CHECK points_spent > 0"],
            ["transactions", "id (serial)", "partner_id → partners.id; membership_id → memberships.id", "PARTIAL UNIQUE(partner_id, receipt_code) WHERE receipt_code IS NOT NULL"],
            ["point_ledger", "id (serial)", "partner_id → partners.id; user_id → users.id", "CHECK balance_after >= 0; Trigger chặn UPDATE/DELETE"],
        ],
        caption="Năm bảng trung tâm với ràng buộc ở mức luận lý."
    )

    rb.h3("3.1.3. Mức vật lý (Physical)")
    rb.p(
        "Ở mức vật lý, các ràng buộc được hiện thực hóa trực tiếp trên PostgreSQL "
        "thông qua DDL. Đây là lớp phòng thủ cuối cùng, đảm bảo tính toàn vẹn dữ "
        "liệu ngay cả khi có lỗi ở tầng application. Ba cơ chế quan trọng nhất "
        "được mô tả dưới đây."
    )
    rb.p(
        "Thứ nhất, CHECK constraint points_balance >= 0 trên bảng users (tên "
        "constraint: points_balance_nonneg) đảm bảo không có UPDATE nào có thể "
        "đưa số dư điểm của bất kỳ người dùng nào về giá trị âm. Constraint này "
        "chặn lỗi ở cấp database và raise IntegrityError nếu tầng service có bug "
        "bỏ sót kiểm tra số dư. Migration tương ứng có mã e2f3a4b5c6d7 trong "
        "thư mục backend/alembic/versions/."
    )
    rb.p(
        "Thứ hai, trigger PostgreSQL no_update_or_delete_point_ledger được định "
        "nghĩa bằng PL/pgSQL và gắn vào bảng point_ledger với event BEFORE UPDATE "
        "OR DELETE. Bất kỳ lệnh UPDATE hoặc DELETE nào trên bảng này đều bị "
        "chặn ngay lập tức bằng lệnh RAISE EXCEPTION với thông báo rõ ràng. "
        "Trigger này đảm bảo bảng point_ledger là append-only thật sự ở cấp "
        "database, không chỉ ở tầng application."
    )
    rb.p(
        "Thứ ba, index B-tree kết hợp trên transactions(partner_id, created_at) "
        "và point_ledger(user_id, created_at) được tạo để tăng tốc truy vấn "
        "analytics thường dùng: tổng hợp doanh thu theo ngày, lịch sử biến động "
        "điểm của một người dùng. Ngoài ra, partial unique index trên "
        "transactions(partner_id, receipt_code) WHERE receipt_code IS NOT NULL "
        "ngăn trùng mã hóa đơn trong cùng một partner mà không ảnh hưởng đến "
        "các giao dịch không có mã hóa đơn."
    )

    # ─────────────────────────────────────────────
    # 3.2 Mô hình xử lý
    # ─────────────────────────────────────────────
    rb.h2("3.2. MÔ HÌNH XỬ LÝ")

    rb.h3("3.2.1. Use case chi tiết")
    rb.p(
        "Phần này trình bày năm use case trọng tâm với đầy đủ precondition, "
        "main flow, alternate flow và postcondition."
    )

    rb.h4("UC-01: Đăng nhập (JWT)")
    rb.table(
        headers=["Thuộc tính", "Nội dung"],
        rows=[
            ["Actor", "Customer, Owner, Staff, Super Admin"],
            ["Precondition", "Người dùng đã có tài khoản, chưa đăng nhập; trang /login đang mở"],
            ["Main flow", "1. Người dùng nhập email/phone + mật khẩu và submit form.\n2. Frontend POST /auth/login.\n3. Backend xác thực bcrypt; nếu đúng, phát JWT (HS256, 7 ngày).\n4. Frontend lưu token vào localStorage, chuyển hướng về trang chính của role."],
            ["Alternate flow", "3a. Mật khẩu sai → 401, hiển thị lỗi. 3b. Quá rate limit → 429, hiển thị thông báo chờ."],
            ["Postcondition", "Người dùng đã đăng nhập; axios interceptor tự động đính JWT vào mọi request tiếp theo"],
        ],
        caption="UC-01: Đăng nhập JWT."
    )

    rb.h4("UC-02: Đăng ký merchant và admin duyệt")
    rb.table(
        headers=["Thuộc tính", "Nội dung"],
        rows=[
            ["Actor", "Owner (đăng ký), Super Admin (duyệt)"],
            ["Precondition", "Owner đã đăng nhập; chưa có partner nào với cùng slug"],
            ["Main flow", "1. Owner điền form đăng ký partner (tên, mô tả, danh mục, liên hệ) và submit.\n2. Backend tạo partner với status PENDING.\n3. Super Admin vào /admin/partners, xem danh sách PENDING và bấm Approve.\n4. Backend chuyển status → ACTIVE, seed 1.000.000 điểm vào point_ledger (reason=ADJUST, ref_type=SYSTEM)."],
            ["Alternate flow", "3a. Admin bấm Reject → partner status PENDING giữ nguyên hoặc chuyển SUSPENDED; owner nhận thông báo."],
            ["Postcondition", "Partner có status ACTIVE; partner_id có thể dùng trong X-Partner-Id header; partner có 1.000.000 điểm khởi đầu"],
        ],
        caption="UC-02: Đăng ký merchant và admin duyệt."
    )

    rb.h4("UC-03: POS tích điểm")
    rb.table(
        headers=["Thuộc tính", "Nội dung"],
        rows=[
            ["Actor", "Staff (hoặc Owner)"],
            ["Precondition", "Staff đã đăng nhập; khách hàng có membership tại partner này"],
            ["Main flow", "1. Khách hàng mở trang /member/qr, hiển thị QR code.\n2. Staff scan QR (hoặc nhập mã hóa đơn) → lấy được user_id của khách.\n3. Staff nhập gross_amount vào form POS và submit.\n4. Backend tính points_earned = floor(net_amount / 10000).\n5. Backend INSERT transaction, INSERT point_ledger (delta dương), UPDATE users.points_balance trong một DB transaction."],
            ["Alternate flow", "2a. QR hết hạn hoặc không hợp lệ → 400; staff nhập số điện thoại thay thế."],
            ["Postcondition", "Transaction được tạo; khách hàng thấy điểm mới ngay khi làm mới trang"],
        ],
        caption="UC-03: POS tích điểm."
    )

    rb.h4("UC-04: Đổi quà từ trang đối tác")
    rb.table(
        headers=["Thuộc tính", "Nội dung"],
        rows=[
            ["Actor", "Customer"],
            ["Precondition", "Customer đã đăng nhập; points_balance >= points_cost của quà muốn đổi; reward đang active"],
            ["Main flow", "1. Customer vào /member/partners/{slug}, chọn quà và bấm Đổi quà.\n2. Dialog xác nhận hiển thị tên quà, điểm cần và số điểm hiện có.\n3. Customer xác nhận → Frontend POST /partners/{id}/rewards/{id}/redeem.\n4. Backend kiểm tra balance, trừ điểm, tạo redemption (status=PENDING, code=8 ký tự), ghi point_ledger (delta âm).\n5. Redemption xuất hiện trong /member/vouchers."],
            ["Alternate flow", "4a. Điểm không đủ → 400, hiển thị lỗi. 4b. Reward hết stock → 409, thông báo hết hàng."],
            ["Postcondition", "Redemption có status PENDING; khách có mã 8 ký tự để dùng tại POS partner"],
        ],
        caption="UC-04: Đổi quà từ trang đối tác."
    )

    rb.h4("UC-05: Admin giám sát điểm hệ thống")
    rb.table(
        headers=["Thuộc tính", "Nội dung"],
        rows=[
            ["Actor", "Super Admin"],
            ["Precondition", "Super Admin đã đăng nhập"],
            ["Main flow", "1. Admin vào /admin/system-points.\n2. Backend tổng hợp: SUM(points_balance) từ users, SUM(delta) theo reason từ point_ledger.\n3. Trang hiển thị card tổng điểm lưu hành, breakdown earned/redeemed/adjusted, bảng log adjustment phân trang."],
            ["Alternate flow", "Không có — trang chỉ đọc, không có action ghi."],
            ["Postcondition", "Admin nắm được tổng quan điểm toàn hệ thống; không có thay đổi dữ liệu"],
        ],
        caption="UC-05: Admin giám sát điểm hệ thống."
    )

    rb.h3("3.2.2. Sơ đồ tuần tự các luồng quan trọng")
    rb.p(
        "Ba sơ đồ tuần tự dưới đây mô tả chi tiết luồng trao đổi dữ liệu giữa "
        "các thành phần hệ thống cho ba nghiệp vụ cốt lõi nhất."
    )
    rb.p(
        "Luồng đăng nhập JWT: Người dùng submit form đăng nhập → Frontend gọi "
        "POST /auth/login với email/phone và password → Backend tra cứu user theo "
        "email/phone → Xác thực bcrypt(password, password_hash) → Nếu đúng, "
        "ký JWT bằng SECRET_KEY (HS256, payload chứa user_id và system_role, "
        "exp = 7 ngày) → Trả access_token về Frontend → Frontend lưu vào "
        "localStorage → axios interceptor tự động thêm Authorization: Bearer {token} "
        "vào mọi request tiếp theo. Mỗi lần đăng nhập thành công, backend "
        "INSERT một bản ghi vào bảng login_logs."
    )
    _img(rb, "bao-cao/assets/diagrams/seq-login.png", "Sơ đồ tuần tự luồng đăng nhập JWT.")
    rb.p(
        "Luồng POS tích điểm: Khách hàng mở /member/qr → trang hiển thị QR SVG "
        "sinh bằng qrcode.react (payload là user_id dạng JSON) → Staff scan QR → "
        "Frontend decode payload lấy user_id → Hiển thị tên khách → Staff nhập "
        "gross_amount và submit → Frontend POST /staff/transactions với "
        "X-Partner-Id header → Backend thực hiện trong DB transaction: "
        "tìm membership(partner_id, user_id), tính points_earned = floor(net/10000), "
        "INSERT transactions, INSERT point_ledger(delta=+earned, reason=earn), "
        "UPDATE users.points_balance += earned → Trả transaction response "
        "→ Frontend hiển thị xác nhận."
    )
    _img(rb, "bao-cao/assets/diagrams/seq-pos-earn.png", "Sơ đồ tuần tự luồng POS tích điểm.")
    rb.p(
        "Luồng đổi quà: Customer trên /member/partners/{slug} bấm Đổi quà → "
        "Dialog confirm hiện → Customer bấm Xác nhận → Frontend POST "
        "/partners/{id}/rewards/{rid}/redeem với X-Partner-Id → Backend kiểm tra "
        "reward.is_active và not deleted, kiểm tra user.points_balance >= reward.points_cost, "
        "giảm stock (nếu không NULL), INSERT redemption(status=PENDING, code=random_8_chars), "
        "INSERT point_ledger(delta=-cost, reason=redeem), UPDATE users.points_balance -= cost "
        "trong cùng DB transaction → Trả redemption response → Frontend điều "
        "hướng về /member/vouchers."
    )
    _img(rb, "bao-cao/assets/diagrams/seq-redeem.png", "Sơ đồ tuần tự luồng đổi quà từ trang đối tác.")

    rb.h3("3.2.3. Sơ đồ hoạt động")
    rb.p(
        "Sơ đồ hoạt động dưới đây mô tả hai luồng nghiệp vụ có quyết định phân "
        "nhánh quan trọng: đăng ký merchant và quên mật khẩu."
    )
    rb.p(
        "Luồng đăng ký merchant: Owner điền và submit form đăng ký partner. "
        "Backend tạo partner với status PENDING và thông báo thành công. "
        "Admin vào trang pending list, xem xét thông tin. Nếu Admin bấm Approve: "
        "backend cập nhật status = ACTIVE, seed 1.000.000 điểm (INSERT point_ledger "
        "với reason=ADJUST, ref_type=SYSTEM, delta=+1000000), và ghi activated_at. "
        "Nếu Admin bấm Reject: backend ghi nhận lý do từ chối, owner không thể "
        "đăng nhập với quyền owner của partner đó. Kết thúc luồng."
    )
    _img(rb, "bao-cao/assets/diagrams/act-merchant-register.png", "Sơ đồ hoạt động luồng đăng ký và duyệt merchant.")
    rb.p(
        "Luồng quên mật khẩu: Người dùng nhập email và submit form. Backend "
        "tra cứu user theo email — nếu không tìm thấy, vẫn trả HTTP 200 "
        "(tránh rò rỉ thông tin). Nếu tìm thấy: tạo temporary password ngẫu nhiên "
        "(12 ký tự alphanum), hash bằng bcrypt, cập nhật users.password_hash, "
        "gọi aiosmtplib gửi email bất đồng bộ. Nếu SMTP lỗi: ghi log warning "
        "nhưng vẫn trả HTTP 200 để user không biết email gửi thất bại "
        "(fail-silent). Người dùng nhận email, đăng nhập bằng mật khẩu tạm, "
        "rồi đổi sang mật khẩu mới trong profile."
    )
    _img(rb, "bao-cao/assets/diagrams/act-forgot-password.png", "Sơ đồ hoạt động luồng quên mật khẩu (fail-silent SMTP).")

    # ─────────────────────────────────────────────
    # 3.3 Hệ thống màn hình
    # ─────────────────────────────────────────────
    rb.h2("3.3. HỆ THỐNG MÀN HÌNH")
    rb.p(
        "Frontend được tổ chức thành năm app shell độc lập trong Next.js 14 App "
        "Router, mỗi shell có layout, theme màu và logic xác thực riêng biệt. "
        "Cách tổ chức này đảm bảo trải nghiệm người dùng tối ưu cho từng vai trò "
        "mà không ảnh hưởng lẫn nhau."
    )
    rb.p(
        "Shell (auth) tại /login và /register là public — không có chrome header/sidebar, "
        "giao diện tập trung vào form. Shell (member) tại /member/* là mobile-first "
        "với max-width 448px, BottomNavBar 4 tab cố định ở đáy màn hình. "
        "Shell (partner) tại /partner/* là desktop-first với sidebar trái, "
        "header và content area dạng responsive grid. Shell (staff) tại /staff/* "
        "là POS focused với emerald theme, chỉ hiển thị hai chức năng chính: "
        "tích điểm và verify reward. Shell (admin) tại /admin/* là admin portal "
        "với sidebar và bảng dữ liệu dạng danh sách."
    )
    rb.table(
        headers=["Shell", "Đường dẫn", "Mô tả trang", "Role được phép"],
        rows=[
            ["(auth)", "/login", "Đăng nhập với email/phone + password", "Public"],
            ["(auth)", "/register", "Đăng ký tài khoản khách hàng", "Public"],
            ["(auth)", "/register/merchant", "Đăng ký tài khoản chủ partner", "Public"],
            ["(member)", "/member", "Trang chủ: số điểm + lịch sử gần đây", "Customer"],
            ["(member)", "/member/qr", "Hiển thị QR cá nhân cho POS scan", "Customer"],
            ["(member)", "/member/partners", "Danh sách đối tác đang active", "Customer"],
            ["(member)", "/member/partners/[slug]", "Chi tiết đối tác + danh sách quà", "Customer"],
            ["(member)", "/member/vouchers", "Ví voucher: tất cả redemption", "Customer"],
            ["(member)", "/member/vouchers/[id]", "Chi tiết redemption + mã QR dùng tại POS", "Customer"],
            ["(member)", "/member/profile", "Thông tin cá nhân + đổi mật khẩu", "Customer"],
            ["(partner)", "/partner", "Dashboard: KPI + biểu đồ + Top 5 quà", "Owner"],
            ["(partner)", "/partner/rewards", "Danh sách quà của partner", "Owner"],
            ["(partner)", "/partner/rewards/new", "Tạo quà mới (3 offer type)", "Owner"],
            ["(partner)", "/partner/rewards/[id]", "Sửa quà (offer_type không đổi được)", "Owner"],
            ["(partner)", "/partner/members", "Danh sách thành viên", "Owner"],
            ["(partner)", "/partner/members/[id]", "Chi tiết thành viên + điều chỉnh điểm + khoá", "Owner"],
            ["(partner)", "/partner/pos", "POS: tích điểm hoặc verify reward", "Owner, Staff"],
            ["(staff)", "/staff", "POS tích điểm (scan QR hoặc nhập mã hóa đơn)", "Staff"],
            ["(staff)", "/staff/verify", "POS verify reward (nhập redemption code)", "Staff"],
            ["(admin)", "/admin", "Dashboard admin: số partner pending", "Super Admin"],
            ["(admin)", "/admin/partners", "Danh sách partner + approve/reject", "Super Admin"],
            ["(admin)", "/admin/login-logs", "Log đăng nhập hệ thống — chỉ đọc", "Super Admin"],
            ["(admin)", "/admin/system-points", "Tổng điểm + breakdown + log adjustment", "Super Admin"],
        ],
        caption="Toàn bộ trang chính của hệ thống theo shell và role."
    )
    rb.p(
        "Một số màn hình quan trọng được minh họa trong các hình dưới đây. "
        "Hình đầu tiên là trang home của khách hàng — hiển thị số điểm và shortcut "
        "QR. Hình thứ hai là dashboard partner. Hình thứ ba là giao diện POS tích điểm. "
        "Hình thứ tư là trang admin system-points."
    )
    _img(rb, "bao-cao/assets/screenshots/member-home.png", "Trang home khách hàng: số điểm hiện tại và shortcut QR cá nhân.")
    _img(rb, "bao-cao/assets/screenshots/partner-dashboard.png", "Dashboard partner: KPI 6 cột và biểu đồ analytics.")
    _img(rb, "bao-cao/assets/screenshots/staff-pos.png", "Giao diện POS tích điểm: scan QR khách hoặc nhập mã hóa đơn.")
    _img(rb, "bao-cao/assets/screenshots/admin-system-points.png", "Trang admin giám sát điểm hệ thống: tổng điểm lưu hành và breakdown.")

    # ─────────────────────────────────────────────
    # 3.4 Hệ thống báo biểu
    # ─────────────────────────────────────────────
    rb.h2("3.4. HỆ THỐNG BÁO BIỂU")
    rb.p(
        "Hệ thống cung cấp bốn loại báo biểu phục vụ cho ba nhóm người dùng khác "
        "nhau. Mỗi báo biểu được thiết kế để trả lời một câu hỏi nghiệp vụ cụ thể "
        "và chỉ hiển thị dữ liệu trong phạm vi quyền của người dùng đó."
    )

    rb.h3("3.4.1. Dashboard analytics của đối tác")
    rb.p(
        "Dashboard partner tại /partner là báo biểu chính của chủ cửa hàng, "
        "cung cấp cái nhìn tổng quan về hiệu quả chương trình loyalty. "
        "Dashboard được chia thành ba khu vực: KPI tổng quan, biểu đồ xu hướng "
        "và bảng ranking."
    )
    rb.p(
        "Khu vực KPI hiển thị sáu chỉ số trong cùng một hàng card: tổng giao dịch "
        "tích điểm trong kỳ, tổng doanh thu (gross_amount), tổng điểm đã phát "
        "(SUM delta WHERE reason=earn), tổng lượt đổi quà, tỉ lệ đổi quà "
        "trên tổng giao dịch (đo engagement của chương trình), và số khách hàng "
        "mới trong kỳ (membership có joined_at trong khoảng thời gian lọc). "
        "Người dùng có thể lọc theo khoảng ngày tuỳ chọn."
    )
    rb.p(
        "Khu vực biểu đồ gồm hai chart đường/cột đặt cạnh nhau: biểu đồ đường "
        "doanh thu theo ngày (gross_amount group by date) và biểu đồ cột số lượt "
        "đổi quà theo ngày (redemptions group by date). Cả hai chart đồng bộ "
        "theo cùng trục thời gian với bộ lọc ngày."
    )
    rb.p(
        "Khu vực Top 5 quà phổ biến là bảng xếp hạng các Reward có số lượt "
        "redemption nhiều nhất trong kỳ lọc. Mỗi dòng hiển thị tên quà, "
        "offer_type, points_cost và số lượt đã đổi."
    )

    rb.h3("3.4.2. Log đăng nhập (Admin)")
    rb.p(
        "Trang /admin/login-logs hiển thị lịch sử đăng nhập toàn hệ thống theo "
        "dạng bảng phân trang. Mỗi bản ghi gồm: user email/phone, IP address "
        "(từ X-Forwarded-For), thời gian đăng nhập và trạng thái (thành công "
        "hay thất bại). Admin có thể lọc theo user hoặc khoảng thời gian. "
        "Đây là công cụ audit để phát hiện đăng nhập bất thường hoặc brute-force."
    )

    rb.h3("3.4.3. Log điều chỉnh điểm (Admin)")
    rb.p(
        "Trang /admin/system-points hiển thị log các điều chỉnh điểm thủ công "
        "do owner thực hiện cho từng thành viên. Mỗi bản ghi gồm: partner, "
        "user được điều chỉnh, actor thực hiện (owner nào), delta (dương hoặc âm), "
        "lý do ghi chú và thời gian. Admin dùng báo biểu này để giám sát các "
        "hành vi điều chỉnh bất thường giữa các partner."
    )

    rb.h3("3.4.4. Tổng điểm hệ thống (Admin)")
    rb.p(
        "Card tổng quan tại /admin/system-points hiển thị ba chỉ số toàn cục: "
        "tổng điểm đang lưu hành (SUM points_balance từ tất cả users active), "
        "breakdown tích lũy theo loại (SUM delta WHERE reason='earn' là tổng "
        "điểm đã phát, SUM ABS(delta) WHERE reason='redeem' là tổng điểm đã "
        "dùng, SUM delta WHERE reason='adjust' là tổng điều chỉnh thủ công), "
        "và số partner đang active. Các chỉ số này cho phép admin theo dõi "
        "sức khỏe tổng thể của hệ thống điểm và phát hiện bất thường."
    )
