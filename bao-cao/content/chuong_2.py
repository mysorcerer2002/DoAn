"""Chương 2 — Phương pháp thực hiện."""
from __future__ import annotations


def build(rb) -> None:
    rb.start_chapter("Chương 2", "Phương pháp thực hiện")

    # ─────────────────────────────────────────────
    # 2.1 Khảo sát hệ thống tương tự
    # ─────────────────────────────────────────────
    rb.h2("2.1. KHẢO SÁT HỆ THỐNG TƯƠNG TỰ")
    rb.p(
        "Trước khi thiết kế hệ thống, đề tài tiến hành khảo sát bốn nhóm giải pháp "
        "loyalty đang phổ biến trên thị trường nhằm xác định khoảng trống mà đề tài "
        "cần lấp đầy. Việc khảo sát tập trung vào hai tiêu chí chính: khả năng "
        "hỗ trợ multi-tenant thật sự cho SME và mức độ phù hợp với thói quen "
        "vận hành của doanh nghiệp nhỏ tại Việt Nam."
    )
    rb.p(
        "Smile.io và LoyaltyLion là hai nền tảng SaaS loyalty quốc tế được sử dụng "
        "rộng rãi trong lĩnh vực thương mại điện tử. Cả hai cung cấp tính năng "
        "tích điểm, phát thưởng và phân hạng thành viên theo chuẩn quốc tế. "
        "Tuy nhiên, mô hình định giá theo số lượng thành viên hoặc đơn hàng "
        "khiến chi phí leo thang nhanh khi quy mô tăng — không phù hợp với ngân "
        "sách hạn chế của SME Việt Nam. Ngoài ra, cả hai nền tảng đều không được "
        "thiết kế cho thị trường Việt Nam, thiếu hỗ trợ ngôn ngữ tiếng Việt "
        "và không tích hợp với các phương thức thanh toán nội địa."
    )
    rb.p(
        "Got It và Urbox là hai nền tảng voucher marketplace phổ biến tại Việt Nam, "
        "cho phép doanh nghiệp phát hành và phân phối voucher qua kênh của nền tảng. "
        "Điểm mạnh là mạng lưới phân phối rộng và thương hiệu đã được nhận diện. "
        "Tuy nhiên, cả hai không cung cấp tính năng tích điểm tự quản cho doanh "
        "nghiệp — khách hàng tích điểm trên hệ thống của nền tảng chứ không phải "
        "của doanh nghiệp, làm mất đi giá trị dữ liệu khách hàng riêng của từng cửa hàng."
    )
    rb.p(
        "Loyverse là một hệ thống POS nhỏ gọn phổ biến trong giới F&B tại Đông Nam Á, "
        "tích hợp tính năng quản lý khách hàng và tích điểm cơ bản. Ưu điểm là "
        "giao diện đơn giản, dễ dùng cho nhân viên. Tuy nhiên, Loyverse không hỗ "
        "trợ multi-tenant thật sự — mỗi cửa hàng là một tài khoản độc lập, không "
        "chia sẻ được ví điểm giữa nhiều thương hiệu trong cùng hệ sinh thái. "
        "Ngoài ra, tính năng báo cáo analytics còn hạn chế, không đủ để chủ "
        "chuỗi cửa hàng quản lý tổng thể."
    )
    rb.table(
        headers=["Tên nền tảng", "Khu vực", "Loại hình", "Multi-tenant SME", "Điểm yếu chính"],
        rows=[
            ["Smile.io", "Quốc tế", "SaaS loyalty", "Không", "Phí cao theo quy mô; không hỗ trợ VN"],
            ["LoyaltyLion", "Quốc tế", "SaaS loyalty", "Không", "Tập trung e-commerce; không POS offline"],
            ["Got It / Urbox", "Việt Nam", "Voucher marketplace", "Không", "Không cho doanh nghiệp tự quản dữ liệu"],
            ["Loyverse", "Đông Nam Á", "POS + loyalty", "Hạn chế", "Mỗi cửa hàng là tài khoản riêng biệt"],
            ["Hệ thống này", "Việt Nam", "Loyalty Platform multi-tenant", "Có", "MVP — chưa có tier và campaign nâng cao"],
        ],
        caption="So sánh các giải pháp loyalty hiện có với hệ thống đề tài."
    )

    # ─────────────────────────────────────────────
    # 2.2 Công nghệ sử dụng
    # ─────────────────────────────────────────────
    rb.h2("2.2. CÔNG NGHỆ SỬ DỤNG")
    rb.p(
        "Việc lựa chọn công nghệ được thực hiện dựa trên ba tiêu chí: tốc độ phát "
        "triển phù hợp với thời gian thực tập, hệ sinh thái thư viện trưởng thành "
        "đủ để xử lý các bài toán kỹ thuật phức tạp, và khả năng triển khai "
        "production trên hạ tầng chi phí thấp."
    )

    rb.h3("2.2.1. Backend")
    rb.table(
        headers=["Thư viện / Framework", "Vai trò", "Lý do chọn"],
        rows=[
            ["FastAPI 0.110+", "Web framework chính", "Async-native, tự động sinh OpenAPI, type-safe với Pydantic v2"],
            ["SQLAlchemy 2.0 async", "ORM", "Mapped[] annotation type-safe, hỗ trợ asyncpg, session management rõ ràng"],
            ["asyncpg", "PostgreSQL driver", "Driver async hiệu năng cao nhất cho PostgreSQL"],
            ["Alembic", "Database migration", "Quản lý migration có versioning, tích hợp tốt với SQLAlchemy"],
            ["Pydantic v2", "Validation và serialization", "Hiệu năng cao hơn v1, model_validator đủ mạnh cho business rules"],
            ["python-jose", "JWT", "Thư viện JWT Python phổ biến, hỗ trợ HS256"],
            ["bcrypt (passlib)", "Password hashing", "Thuật toán bcrypt industry-standard cho lưu trữ mật khẩu an toàn"],
            ["slowapi", "Rate limiting", "Tích hợp trực tiếp vào FastAPI, key theo header X-Forwarded-For"],
            ["aiosmtplib", "Gửi email SMTP", "Client SMTP async, fail-silent khi SMTP lỗi không block response"],
        ],
        caption="Các thư viện backend và lý do lựa chọn."
    )

    rb.h3("2.2.2. Frontend")
    rb.table(
        headers=["Thư viện / Framework", "Vai trò", "Lý do chọn"],
        rows=[
            ["Next.js 14 App Router", "Framework frontend", "Server Component + Client Component, routing file-based, production-ready"],
            ["TypeScript", "Ngôn ngữ", "Type safety giảm bug runtime, IDE support tốt"],
            ["Tailwind CSS v4", "Styling", "Utility-first, không CSS riêng, dễ responsive"],
            ["shadcn/ui", "Component library", "Headless components có thể tùy chỉnh, tích hợp Tailwind sẵn"],
            ["TanStack Query v5", "Server state management", "Cache, refetch, invalidation tự động; giảm boilerplate fetch"],
            ["Zustand", "Client state", "Nhẹ, không boilerplate, đủ cho auth store và tenant store"],
            ["react-hook-form + zod", "Form + validation", "Hiệu năng cao, schema validation chia sẻ được với backend"],
            ["qrcode.react", "Sinh mã QR", "Thư viện QR đơn giản, render SVG hoặc Canvas trực tiếp"],
            ["axios", "HTTP client", "Interceptor JWT và X-Partner-Id tự động cho mọi request"],
        ],
        caption="Các thư viện frontend và lý do lựa chọn."
    )

    rb.h3("2.2.3. Cơ sở dữ liệu và hạ tầng")
    rb.p(
        "Cơ sở dữ liệu PostgreSQL 15 được chọn vì hỗ trợ đầy đủ các tính năng "
        "cần thiết cho đề tài: CHECK constraint phức tạp, trigger PL/pgSQL để "
        "hiện thực hóa append-only ledger, partial unique index cho ràng buộc "
        "nghiệp vụ, và index B-tree kết hợp cho truy vấn analytics. Đặc biệt, "
        "asyncpg — driver async của PostgreSQL — cho phép xử lý nhiều request "
        "đồng thời mà không chặn event loop của FastAPI."
    )
    rb.p(
        "Về hạ tầng, toàn bộ hệ thống được đóng gói bằng Docker Compose với hai "
        "môi trường riêng biệt: môi trường phát triển (dev) và môi trường production "
        "(prod). Cloudflare Tunnel được dùng để expose backend và frontend ra "
        "internet qua domain loyalty.ecom-bill.com mà không cần mở port trên "
        "firewall. Migration Alembic được cấu hình chạy tự động khi container "
        "backend khởi động, đảm bảo schema luôn đồng bộ với code."
    )

    # ─────────────────────────────────────────────
    # 2.3 Phương pháp luận
    # ─────────────────────────────────────────────
    rb.h2("2.3. PHƯƠNG PHÁP LUẬN")

    rb.h3("2.3.1. Kiến trúc phân lớp (Layered Architecture)")
    rb.p(
        "Backend được tổ chức theo kiến trúc phân lớp nghiêm ngặt với bốn lớp "
        "chính. Lớp API (app/api/) chứa các FastAPI router, chịu trách nhiệm "
        "parse request, gọi service và ánh xạ lỗi domain thành HTTPException "
        "với status code phù hợp. Lớp Service (app/services/) chứa toàn bộ "
        "logic nghiệp vụ — service nhận AsyncSession trong constructor và raise "
        "domain exception khi vi phạm rule. Lớp Model (app/models/) là SQLAlchemy "
        "ORM với Mapped[] annotation type-safe. Lớp Schema (app/schemas/) là "
        "Pydantic v2 DTO cho request và response. Nguyên tắc cốt lõi là route "
        "mỏng, service béo (thin-route, fat-service): không có business logic "
        "trong file API."
    )

    rb.h3("2.3.2. Multi-tenant qua header và dependency injection")
    rb.p(
        "Mỗi request API từ frontend gửi kèm header X-Partner-Id chứa ID của "
        "partner đang được truy cập. Tầng dependency injection của FastAPI "
        "xác thực header này và kiểm tra quyền của người dùng hiện tại trong "
        "partner đó trước khi cho phép xử lý request. Bốn dependency được "
        "định nghĩa trong app/core/deps.py: require_super_admin (chỉ admin hệ "
        "thống), require_owner_in_partner (chủ đối tác), "
        "require_staff_in_partner (nhân viên — dùng cho POS), và "
        "require_customer_in_partner (khách hàng có membership). Mỗi endpoint "
        "khai báo đúng một dependency, đảm bảo phân quyền nhất quán không "
        "phụ thuộc vào logic của service."
    )

    rb.h3("2.3.3. Append-only ledger pattern")
    rb.p(
        "Thay vì lưu số dư điểm duy nhất và cập nhật theo từng giao dịch, "
        "hệ thống duy trì cả hai: cột points_balance trên bảng users (để "
        "truy vấn nhanh số dư hiện tại) và bảng point_ledger append-only "
        "(để kiểm toán toàn bộ lịch sử). Mỗi khi điểm thay đổi, hệ thống "
        "thực hiện trong cùng một database transaction: cập nhật "
        "users.points_balance và INSERT một bản ghi mới vào point_ledger "
        "với delta, reason, ref_type, ref_id và balance_after. Trigger "
        "PostgreSQL no_update_or_delete_point_ledger được kích hoạt khi "
        "có lệnh UPDATE hoặc DELETE trên bảng point_ledger và tự động "
        "raise exception, ngăn mọi hành vi sửa lịch sử sau khi đã ghi."
    )

    rb.h3("2.3.4. Kiểm thử và đảm bảo chất lượng")
    rb.p(
        "Đề tài sử dụng pytest làm framework kiểm thử chính cho backend, "
        "với các test được phân chia thành hai nhóm: unit test kiểm tra "
        "từng service function độc lập và integration test kiểm tra luồng "
        "end-to-end qua database thật. Tuy nhiên, cần ghi nhận một giới "
        "hạn kỹ thuật thực tế: trên môi trường Windows, testcontainers — "
        "thư viện dùng để spin up PostgreSQL tạm thời cho integration test — "
        "yêu cầu quyền truy cập docker.sock và cấu hình Docker network mà "
        "môi trường phát triển hiện tại không đáp ứng được hoàn toàn. "
        "Do đó, đề tài bổ sung phương pháp kiểm thử khác: smoke E2E qua "
        "curl trực tiếp trên production URL loyalty.ecom-bill.com, kiểm "
        "thử thủ công từng luồng nghiệp vụ qua trình duyệt, và UAT "
        "(User Acceptance Testing) với các tài khoản demo seed sẵn."
    )

    rb.h3("2.3.5. Git workflow và kiểm soát chất lượng code")
    rb.p(
        "Toàn bộ lịch sử phát triển được quản lý trên Git với quy ước commit "
        "message theo Conventional Commits (feat/fix/chore/refactor + scope). "
        "Code review được thực hiện sau mỗi task hoàn thành trước khi chuyển "
        "sang task tiếp theo, đảm bảo không tích lũy technical debt. "
        "Frontend được kiểm tra type bằng tsc --noEmit và ESLint sau mỗi "
        "lần thay đổi lớn. Migration Alembic được viết với cả upgrade() và "
        "downgrade() để có thể rollback khi cần. Toàn bộ codebase được "
        "deploy liên tục lên môi trường production qua Docker Compose, "
        "cho phép kiểm tra hành vi thực tế của hệ thống song song với phát triển."
    )

    # ─────────────────────────────────────────────
    # 2.4 Phân tích nghiệp vụ
    # ─────────────────────────────────────────────
    rb.h2("2.4. PHÂN TÍCH NGHIỆP VỤ")

    rb.h3("2.4.1. Các quy trình nghiệp vụ chính")
    rb.p(
        "Hệ thống xử lý tám luồng nghiệp vụ cốt lõi được mô tả lần lượt dưới đây."
    )
    rb.p(
        "Luồng (1) — Đăng ký và đăng nhập: Khách hàng điền form đăng ký với "
        "email/số điện thoại và mật khẩu. Backend hash mật khẩu bằng bcrypt "
        "và lưu vào bảng users. Khi đăng nhập, backend xác thực bcrypt và "
        "phát JWT có thời hạn, frontend lưu token vào localStorage và đính "
        "kèm vào mọi request tiếp theo qua axios interceptor."
    )
    rb.p(
        "Luồng (2) — Quên mật khẩu: Khách hàng nhập email vào form quên mật khẩu. "
        "Backend tạo temporary password ngẫu nhiên, hash và cập nhật vào "
        "users.password_hash, sau đó gọi aiosmtplib gửi email chứa mật khẩu tạm. "
        "Nếu SMTP lỗi, backend vẫn trả HTTP 200 và ghi log warning — cơ chế "
        "fail-silent ngăn rò rỉ thông tin về việc email có tồn tại trong hệ "
        "thống hay không."
    )
    rb.p(
        "Luồng (3) — Đổi mật khẩu: Sau khi đăng nhập bằng mật khẩu tạm, "
        "khách hàng vào trang profile và cập nhật mật khẩu mới. Backend xác "
        "thực mật khẩu hiện tại trước khi cập nhật hash mới vào cơ sở dữ liệu."
    )
    rb.p(
        "Luồng (4) — Đăng ký merchant và admin duyệt: Chủ cửa hàng điền form "
        "đăng ký partner với tên, mô tả, danh mục và thông tin liên hệ. Partner "
        "được tạo với status PENDING. Admin vào cổng quản trị, xem danh sách "
        "pending và bấm Approve. Backend chuyển status thành ACTIVE và đồng thời "
        "seed 1.000.000 điểm khởi đầu vào point_ledger với reason ADJUST và "
        "ref_type SYSTEM, tạo nền tảng để partner bắt đầu phát điểm cho khách hàng."
    )
    rb.p(
        "Luồng (5) — POS tích điểm: Khách hàng mở trang QR cá nhân trên điện "
        "thoại. Nhân viên POS scan QR hoặc nhập mã hóa đơn để xác định khách hàng. "
        "Nhân viên nhập số tiền hóa đơn vào form. Backend tính điểm được cộng, "
        "tạo transaction record, INSERT vào point_ledger với delta dương và cập "
        "nhật users.points_balance trong cùng một database transaction."
    )
    rb.p(
        "Luồng (6) — POS đổi điểm (verify reward): Khách hàng đã đổi quà trước "
        "đó và có mã redemption 8 ký tự. Nhân viên POS nhập mã vào form verify. "
        "Backend tìm redemption theo partner_id và code, kiểm tra status PENDING "
        "và thời hạn chưa hết, cập nhật status thành USED và ghi used_at, "
        "used_by_staff_id. Giao diện POS hiển thị thông tin quà để nhân viên "
        "xác nhận và trao cho khách."
    )
    rb.p(
        "Luồng (7) — Khách hàng đổi quà từ trang đối tác: Khách hàng vào trang "
        "chi tiết đối tác, xem danh sách quà và điểm cần thiết cho mỗi quà. "
        "Khi bấm Đổi quà, dialog xác nhận hiện ra với thông tin chi tiết. "
        "Sau khi xác nhận, backend kiểm tra points_balance đủ, trừ điểm, tạo "
        "redemption với mã 8 ký tự ngẫu nhiên unique trong phạm vi partner, "
        "và ghi vào point_ledger với delta âm."
    )
    rb.p(
        "Luồng (8) — Admin giám sát điểm hệ thống: Admin vào trang system-points "
        "để xem tổng quan điểm toàn hệ thống. Trang hiển thị tổng điểm đang lưu "
        "hành (tổng points_balance của tất cả users), breakdown "
        "earned/redeemed/adjusted tính từ bảng point_ledger, và log lịch sử "
        "các adjustment thủ công. Đây là chức năng chỉ đọc — admin không có "
        "form điều chỉnh điểm trực tiếp."
    )

    rb.h3("2.4.2. Sơ đồ chức năng hệ thống")
    rb.p(
        "Hệ thống được phân rã thành ba nhánh chức năng chính tương ứng "
        "với ba nhóm người dùng. Bảng dưới đây trình bày cây phân rã "
        "chức năng theo dạng phân cấp."
    )
    rb.table(
        headers=["Nhóm", "Module", "Chức năng con"],
        rows=[
            ["End-user", "Tài khoản", "Đăng ký / Đăng nhập / Quên mật khẩu / Đổi mật khẩu"],
            ["End-user", "Ví điểm & QR", "Xem điểm hiện tại / Sinh mã QR cá nhân / Lịch sử biến động"],
            ["End-user", "Khám phá đối tác", "Danh sách đối tác / Chi tiết đối tác / Danh sách quà"],
            ["End-user", "Đổi quà", "Chọn quà / Xác nhận / Trừ điểm / Tạo redemption code"],
            ["End-user", "Ví voucher", "Xem redemption đã đổi / Trạng thái PENDING/USED/EXPIRED / Dùng tại POS"],
            ["Đối tác", "Onboarding", "Đăng ký partner / Chờ duyệt / Xem trạng thái"],
            ["Đối tác", "Dashboard", "KPI tổng quan / Biểu đồ doanh thu / Biểu đồ đổi quà / Top 5 quà"],
            ["Đối tác", "Quản lý quà", "Tạo / Sửa / Ẩn quà / 3 loại offer: PERCENT, FIXED, ITEM_GIFT"],
            ["Đối tác", "POS", "Tích điểm (scan QR hoặc nhập mã hóa đơn) / Verify reward (nhập redemption code)"],
            ["Đối tác", "Quản lý thành viên", "Xem danh sách / Chi tiết thành viên / Điều chỉnh điểm / Khoá tài khoản"],
            ["Admin", "Duyệt merchant", "Xem pending list / Approve (+ seed điểm) / Reject"],
            ["Admin", "Log đăng nhập", "Xem lịch sử đăng nhập theo user/thời gian — chỉ đọc"],
            ["Admin", "Điểm hệ thống", "Tổng điểm lưu hành / Breakdown / Log adjustment — chỉ đọc"],
        ],
        caption="Cây phân rã chức năng hệ thống theo ba nhóm người dùng."
    )

    rb.h3("2.4.3. Các actor và use case tổng quát")
    rb.p(
        "Hệ thống có bốn actor chính với phạm vi truy cập và use case khác nhau "
        "như mô tả trong bảng dưới đây. Ranh giới quyền hạn giữa Owner và Staff "
        "đặc biệt quan trọng: Staff chỉ có quyền thực hiện giao dịch POS, không "
        "được truy cập CRUD quà hay xem dashboard analytics."
    )
    rb.table(
        headers=["Actor", "Vai trò", "Use case chính", "Shell truy cập"],
        rows=[
            ["Customer", "Khách hàng cuối — người tích điểm và đổi quà", "Đăng ký, đăng nhập, xem điểm, QR cá nhân, xem đối tác, đổi quà, xem voucher", "/member/* — mobile-first, BottomNavBar"],
            ["Owner", "Chủ đối tác — quản lý toàn bộ hoạt động cửa hàng", "Dashboard, CRUD quà, xem thành viên, điều chỉnh điểm, toàn quyền POS", "/partner/* — desktop sidebar"],
            ["Staff", "Nhân viên POS — thực hiện giao dịch tại quầy", "Tích điểm (scan QR), verify reward (nhập code), tạo transaction", "/staff/* — POS focused, emerald theme"],
            ["Super Admin", "Quản trị viên hệ thống — giám sát toàn cục", "Duyệt partner, xem login log, xem điểm hệ thống", "/admin/* — admin portal"],
        ],
        caption="Bốn actor và use case tổng quát của hệ thống."
    )
