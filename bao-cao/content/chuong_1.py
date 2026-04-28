"""Chương 1 — Giới thiệu."""
from __future__ import annotations


def build(rb) -> None:
    rb.start_chapter("Chương 1", "Giới thiệu")

    # ─────────────────────────────────────────────
    # 1.1 Đặt vấn đề, mục tiêu
    # ─────────────────────────────────────────────
    rb.h2("1.1. ĐẶT VẤN ĐỀ, MỤC TIÊU")
    rb.p(
        "Trong một thập kỷ trở lại đây, thị trường bán lẻ và dịch vụ tại Việt Nam "
        "chứng kiến sự bùng nổ của các doanh nghiệp vừa và nhỏ (SME) — đặc biệt là "
        "các chuỗi cà phê, nhà hàng, tiệm bánh, cửa hàng thời trang và làm đẹp. "
        "SME chiếm tỷ trọng lớn trong tổng số doanh nghiệp đang hoạt động tại Việt Nam, "
        "đóng góp đáng kể vào tổng sản phẩm quốc nội và tạo việc làm cho hàng triệu "
        "lao động. Đặc điểm chung của nhóm này là quy mô nhỏ, vòng đời khách hàng "
        "gắn với một vài chi nhánh, ngân sách marketing hạn chế nhưng lại cần duy trì "
        "lượng khách hàng quen thuộc để đảm bảo doanh thu ổn định."
    )
    rb.p(
        "Chương trình khách hàng thân thiết (loyalty program) là công cụ kinh điển "
        "để giữ chân khách hàng: tích điểm theo hóa đơn, đổi quà, phát voucher nhân "
        "các dịp đặc biệt. Tuy nhiên, khi đi từ lý thuyết đến triển khai thực tế, "
        "SME Việt Nam đang đứng trước những vướng mắc cụ thể. Các giải pháp SaaS "
        "quốc tế như Smile.io hay LoyaltyLion tính phí theo quy mô khách hàng và "
        "không được thiết kế cho thị trường Việt Nam. Các nền tảng trong nước như "
        "Got It hay Urbox tập trung vào voucher marketplace, không giải quyết bài "
        "toán tích điểm đa cửa hàng cho chính doanh nghiệp. Các bộ công cụ POS "
        "kiểu Loyverse cho phép tích điểm nhưng không hỗ trợ multi-tenant thật sự, "
        "mỗi cửa hàng là một hệ thống tách biệt."
    )
    rb.p(
        "Từ các phân tích trên, đề tài đặt ra mục tiêu xây dựng một nền tảng loyalty "
        "multi-tenant: cho phép nhiều doanh nghiệp cùng vận hành chương trình khách "
        "hàng thân thiết độc lập trên cùng hạ tầng, với ví điểm toàn cục cross-shop "
        "cho phép khách hàng tích điểm tại nhiều đối tác khác nhau và sử dụng điểm "
        "linh hoạt. Phạm vi đề tài tập trung vào ba nhóm chức năng cốt lõi: "
        "ứng dụng dành cho khách hàng (tích điểm + đổi quà), bảng điều khiển dành "
        "cho đối tác (quản lý quà + POS + thống kê), và cổng quản trị hệ thống "
        "dành cho admin (duyệt đăng ký + giám sát điểm)."
    )

    rb.h3("1.1.1. Bối cảnh thị trường SME & loyalty")
    rb.p(
        "Qua khảo sát sơ bộ các cửa hàng cà phê, nhà hàng nhỏ và shop thời trang "
        "tại TP.HCM, có thể nhận thấy ba hiện trạng phổ biến. Thứ nhất, phần lớn "
        "cửa hàng đang dùng sổ giấy hoặc thẻ tích điểm vật lý — dẫn đến gian lận "
        "dễ dàng, mất dữ liệu khi thay nhân viên, và không thể tổng hợp dữ liệu "
        "để phân tích hành vi khách hàng. Thứ hai, những nơi có dùng phần mềm "
        "tích điểm thường là hệ thống đơn lẻ, không liên kết được giữa các chi nhánh "
        "hoặc không cho phép khách hàng dùng một tài khoản tích điểm tại nhiều "
        "thương hiệu cùng hệ sinh thái. Thứ ba, nhân viên POS thường không có công "
        "cụ đủ đơn giản để tra cứu và xác nhận phần thưởng của khách tại quầy "
        "trong thời gian ngắn, dẫn đến trải nghiệm khách hàng kém."
    )
    rb.p(
        "Nhu cầu thiết yếu được tổng hợp bao gồm: nhận diện nhanh khách quen qua "
        "QR cá nhân, tự động cộng điểm dựa trên tổng tiền hóa đơn, cho phép khách "
        "hàng đổi điểm lấy quà hoặc voucher giảm giá, giúp nhân viên POS xác nhận "
        "voucher tại quầy nhanh chóng, và cung cấp dashboard thống kê để chủ cửa hàng "
        "nắm bắt hiệu quả chương trình loyalty. Đây là tập hợp chức năng tối thiểu "
        "mà một giải pháp loyalty SME cần đáp ứng để có giá trị triển khai thực tế."
    )

    rb.h3("1.1.2. Mục tiêu cụ thể đề tài")
    rb.p(
        "Trên cơ sở phân tích nhu cầu, đề tài xác định ba mục tiêu cụ thể. Mục tiêu "
        "thứ nhất là thiết kế và hiện thực hóa kiến trúc multi-tenant nghiêm ngặt, "
        "trong đó mỗi đối tác (partner) là một tenant độc lập với dữ liệu được cô lập "
        "hoàn toàn, phân quyền rõ ràng cho bốn vai trò: super admin (quản trị hệ thống), "
        "owner (chủ doanh nghiệp), staff (nhân viên POS), và customer (khách hàng cuối). "
        "Mục tiêu thứ hai là xây dựng ví điểm toàn cục cross-shop, nơi điểm của khách "
        "hàng được lưu trữ tập trung với ràng buộc không âm ở cấp cơ sở dữ liệu, và "
        "mọi biến động điểm được ghi vào sổ cái append-only để đảm bảo khả năng "
        "kiểm toán. Mục tiêu thứ ba là chứng minh tính vận hành được của hệ thống "
        "qua triển khai thực tế trên môi trường production với Docker Compose và "
        "Cloudflare Tunnel, kèm theo smoke test E2E cho các luồng nghiệp vụ cốt lõi."
    )

    # ─────────────────────────────────────────────
    # 1.2 Thách thức cần giải quyết
    # ─────────────────────────────────────────────
    rb.h2("1.2. THÁCH THỨC CẦN GIẢI QUYẾT")
    rb.p(
        "Thiết kế một hệ thống loyalty cho SME tưởng chừng đơn giản nhưng khi đi sâu "
        "vào các yêu cầu phi chức năng và ràng buộc nghiệp vụ, đề tài phải đối mặt "
        "với nhiều thách thức kỹ thuật chồng chéo. Phần này tóm lược các bài toán "
        "trọng tâm mà hệ thống cần giải quyết và hướng tiếp cận tương ứng."
    )

    rb.h3("1.2.1. Cô lập dữ liệu đa tenant qua header và dependency injection")
    rb.p(
        "Mô hình multi-tenant shared schema đưa cột partner_id vào hầu hết các bảng "
        "nghiệp vụ, đặt ra yêu cầu: mọi truy vấn đọc/ghi phải bắt buộc được scope "
        "theo đúng partner_id, tránh rò rỉ dữ liệu sang tenant khác. Đề tài giải "
        "quyết bằng cơ chế header X-Partner-Id kết hợp với bốn dependency injection "
        "ở tầng FastAPI: require_super_admin, require_owner_in_partner, "
        "require_staff_in_partner, và require_customer_in_partner. Mỗi endpoint chỉ "
        "khai báo đúng một dependency phù hợp với vai trò được phép truy cập, đảm "
        "bảo không endpoint nào có thể xử lý request mà không xác thực quyền trong "
        "partner tương ứng trước."
    )

    rb.h3("1.2.2. Ví điểm toàn cục cross-shop với ràng buộc không âm")
    rb.p(
        "Điểm của khách hàng trong hệ thống này là toàn cục — tích điểm tại Cafe "
        "Cộng và đổi quà tại Lala Food dùng cùng một ví điểm. Thiết kế này đặt ra "
        "yêu cầu về tính nhất quán: khi đổi quà, hệ thống phải đảm bảo không có "
        "cách nào đưa số dư về âm dù có hai request đổi quà song song trên cùng "
        "một tài khoản. Cơ chế chính chống race condition là Optimistic "
        "Concurrency Control dựa trên database constraint: thay vì SELECT số dư "
        "rồi UPDATE (pattern dễ bị lost-update ở mức isolation READ COMMITTED), "
        "đề tài thực hiện một câu lệnh atomic duy nhất "
        "UPDATE users SET points_balance = points_balance - X WHERE id = U AND "
        "points_balance >= X RETURNING points_balance. Mệnh đề WHERE points_balance "
        ">= X là điểm mấu chốt: với hai request song song cùng đổi 80 điểm từ số dư "
        "100, request đến trước commit thành công đưa số dư về 20; request đến sau "
        "khi đụng row-level lock đợi commit của request trước, sau đó so điều kiện "
        "WHERE với giá trị đã cập nhật (20 < 80) nên rowcount = 0 và không UPDATE "
        "row nào. Service kiểm tra RETURNING trả None thì raise "
        "InsufficientPointsError, route map sang HTTP 400 'không đủ điểm'. Lớp thứ "
        "hai là CHECK constraint points_balance >= 0 ở cấp cơ sở dữ liệu, đóng vai "
        "trò defense-in-depth cho mọi đường ghi khác (admin SQL trực tiếp, script "
        "manual fix, hoặc bug code mới trong tương lai) không đi qua pattern atomic "
        "UPDATE WHERE — nhưng trong luồng đổi quà thông thường thì CHECK không bao "
        "giờ kích hoạt vì WHERE đã loại trước."
    )

    rb.h3("1.2.3. Append-only ledger đảm bảo khả năng kiểm toán")
    rb.p(
        "Mọi biến động điểm — tích điểm, đổi quà, điều chỉnh thủ công, hoặc hoàn "
        "điểm — đều được ghi thành một bản ghi riêng trong bảng point_ledger. "
        "Để đảm bảo tính bất biến của sổ cái, không một bản ghi nào được phép "
        "bị sửa hoặc xóa sau khi đã ghi. Đề tài hiện thực hóa ràng buộc này ở "
        "cấp cơ sở dữ liệu thông qua trigger PostgreSQL "
        "no_update_or_delete_point_ledger chặn hoàn toàn lệnh UPDATE và DELETE "
        "trên bảng point_ledger. Khi cần điều chỉnh sai sót, đề tài chỉ cho "
        "phép tạo entry bù trừ (compensation entry) mới thay vì sửa bản ghi cũ."
    )

    rb.h3("1.2.4. Bảo mật JWT, bcrypt và rate limiting")
    rb.p(
        "Hệ thống dùng JSON Web Token (JWT) cho xác thực phiên đăng nhập, kết hợp "
        "bcrypt cho lưu trữ mật khẩu. Để chống brute-force và các hành vi lạm dụng "
        "API, thư viện slowapi đóng vai trò rate limiter ở tầng middleware FastAPI — "
        "mặc định giới hạn login 30 request/phút và register 20 request/phút, key "
        "theo X-Forwarded-For được Cloudflare Tunnel inject. QR cá nhân của khách "
        "hàng được sinh từ user_id và mã hóa thành payload mà staff scan tại quầy, "
        "không lộ thông tin nhạy cảm trong mã QR. Luồng quên mật khẩu gửi temporary "
        "password qua SMTP với cơ chế fail-silent: nếu SMTP lỗi thì backend vẫn "
        "trả HTTP 200 và ghi log warning, tránh leak thông tin về việc email có "
        "tồn tại trong hệ thống hay không."
    )

    rb.h3("1.2.5. Cân bằng UX cho bốn vai trò khác nhau")
    rb.p(
        "Bốn nhóm người dùng có nhu cầu trải nghiệm hoàn toàn khác nhau. Khách hàng "
        "truy cập chủ yếu bằng điện thoại tại quầy thanh toán — giao diện cần mobile-first, "
        "tải nhanh, và tìm được nút QR trong vài giây. Chủ đối tác thường quản lý "
        "từ máy tính bàn hoặc laptop — cần dashboard đủ thông tin, biểu đồ rõ ràng. "
        "Nhân viên POS cần màn hình cực đơn giản: chỉ một nút scan và một nút xác nhận "
        "voucher, tránh bấm nhầm. Admin hệ thống cần bảng điều khiển tổng quan "
        "để duyệt đăng ký đối tác và giám sát điểm. Đề tài giải quyết bằng cách "
        "tách hoàn toàn bốn app shell với layout và theme riêng biệt: (member) "
        "mobile-first với BottomNavBar, (partner) desktop sidebar, (staff) "
        "POS focused với emerald theme, (admin) admin portal."
    )

    # ─────────────────────────────────────────────
    # 1.3 Phạm vi
    # ─────────────────────────────────────────────
    rb.h2("1.3. PHẠM VI THỰC HIỆN")

    rb.h3("1.3.1. Phạm vi trong đề tài (in-scope)")
    rb.p(
        "Đề tài bao gồm ba nhóm chức năng tương ứng với ba nhóm người dùng chính. "
        "Mỗi nhóm được thiết kế đầy đủ từ giao diện người dùng đến logic nghiệp vụ "
        "và lưu trữ dữ liệu."
    )
    rb.p("Nhóm End-user (khách hàng) gồm năm module:")
    rb.bullet("Đăng ký tài khoản, đăng nhập, quên mật khẩu (gửi temporary password qua SMTP), và đổi mật khẩu trong profile.")
    rb.bullet("Xem điểm hiện có và mã QR cá nhân (thẻ thành viên cross-shop).")
    rb.bullet("Danh sách đối tác tham gia hệ thống, xem chi tiết đối tác và danh sách quà có thể đổi.")
    rb.bullet("Đổi quà từ trang chi tiết đối tác (trừ điểm + tạo redemption với mã 8 ký tự).")
    rb.bullet("Ví voucher: xem các redemption đã đổi, trạng thái PENDING/USED/EXPIRED, sử dụng tại POS.")
    rb.p("Nhóm Đối tác / Merchant (chủ cửa hàng) gồm năm module:")
    rb.bullet("Đăng ký merchant và chờ admin duyệt (partner status PENDING → ACTIVE).")
    rb.bullet("Dashboard tổng quan: sáu KPI cốt lõi, biểu đồ doanh thu theo ngày, biểu đồ lượt đổi quà theo ngày, Top 5 quà phát ra nhiều nhất.")
    rb.bullet("CRUD quà (Reward): ba kiểu offer — PERCENT_DISCOUNT, FIXED_DISCOUNT, ITEM_GIFT. Trường offer_type bất biến sau khi tạo.")
    rb.bullet("POS tích điểm: scan QR khách hoặc nhập mã hóa đơn. POS đổi điểm: nhập mã redemption để xác nhận và mark used.")
    rb.bullet("Quản lý thành viên: xem chi tiết, điều chỉnh điểm (manual adjustment vào ledger), khoá tài khoản.")
    rb.p("Nhóm Admin hệ thống gồm ba module:")
    rb.bullet("Duyệt đăng ký merchant: approve (chuyển status ACTIVE + seed 1.000.000 điểm khởi đầu) hoặc reject.")
    rb.bullet("Log đăng nhập (audit): xem lịch sử đăng nhập theo user và thời gian — chỉ đọc.")
    rb.bullet("Quản lý điểm hệ thống: tổng điểm lưu hành, breakdown earned/redeemed/adjusted, log lịch sử điều chỉnh — chỉ đọc.")

    rb.h3("1.3.2. Phạm vi ngoài đề tài (out-of-scope, bảo lưu cho luận văn)")
    rb.p(
        "Các tính năng dưới đây nằm ngoài phạm vi đề tài thực tập tốt nghiệp "
        "và được bảo lưu để phát triển trong luận văn tốt nghiệp:"
    )
    rb.bullet("Hệ thống tier hạng thành viên (Đồng/Bạc/Vàng/Kim Cương) với chính sách ưu đãi theo hạng.")
    rb.bullet("Campaign khuyến mại có phê duyệt pháp lý (Nghị định 81/2018/NĐ-CP, Sở Công Thương).")
    rb.bullet("Voucher hệ thống với giới hạn số lượng phát và cơ chế chống race condition claim đồng thời.")
    rb.bullet("Service fee thật và tích hợp cổng thanh toán (VNPay, MoMo).")
    rb.bullet("Progressive Web App (PWA) offline-ready với Service Worker.")
    rb.bullet("Ứng dụng native mobile (iOS/Android).")
    rb.bullet("Cron job birthday voucher và expire voucher tự động.")

    rb.h3("1.3.3. Hướng phát triển mở rộng")
    rb.p(
        "Sau khi đề tài hoàn tất, nền tảng có thể được phát triển tiếp theo nhiều "
        "hướng. Trước tiên là bổ sung hệ thống tier hạng thành viên với chính sách "
        "ưu đãi khác nhau theo hạng, kết hợp campaign khuyến mại tuân thủ pháp lý "
        "Nghị định 81/2018/NĐ-CP. Tiếp theo là tích hợp cổng thanh toán để hiện "
        "thực hóa mô hình thu phí dịch vụ. Về phía người dùng cuối, phát triển "
        "PWA offline-ready sẽ cải thiện đáng kể trải nghiệm trong điều kiện mạng "
        "yếu tại quầy thanh toán. Về mặt trí tuệ nhân tạo, có thể ứng dụng "
        "machine learning để gợi ý quà phù hợp và dự báo tỉ lệ rời bỏ khách hàng."
    )

    # ─────────────────────────────────────────────
    # 1.4 Kết quả cần đạt
    # ─────────────────────────────────────────────
    rb.h2("1.4. KẾT QUẢ CẦN ĐẠT")
    rb.p(
        "Bảng dưới đây liệt kê các mục tiêu cụ thể của đề tài cùng tiêu chí "
        "đo lường tương ứng. Các mục tiêu này sẽ được đối chiếu với kết quả thực "
        "tế ở Chương 5."
    )
    rb.table(
        headers=["STT", "Mục tiêu", "Tiêu chí đo lường"],
        rows=[
            ["1", "Hệ thống multi-tenant hoạt động ổn định", "Nhiều partner cùng vận hành song song; dữ liệu không lẫn nhau qua test smoke E2E."],
            ["2", "Phân quyền 4 vai trò đầy đủ", "Super admin, Owner, Staff, Customer — mỗi vai trò chỉ truy cập đúng tài nguyên được phép."],
            ["3", "Ví điểm toàn cục với CHECK >= 0", "CHECK constraint points_balance_nonneg trên bảng users; không thể trừ quá số dư qua bất kỳ path nào."],
            ["4", "Append-only ledger có trigger DB", "Trigger no_update_or_delete_point_ledger chặn UPDATE/DELETE; verify qua psql trực tiếp."],
            ["5", "Smoke E2E các luồng cốt lõi", "Các luồng auth, tích điểm, đổi quà, duyệt merchant pass qua curl trên prod URL loyalty.ecom-bill.com."],
            ["6", "Dashboard merchant analytics", "Hiển thị đủ 6 KPI + 2 biểu đồ + Top 5 quà; dữ liệu khớp với bảng transactions và redemptions."],
            ["7", "Admin giám sát điểm hệ thống", "Trang system-points hiển thị tổng điểm lưu hành + breakdown + log — chỉ đọc."],
            ["8", "Deploy Docker Compose + Cloudflare Tunnel", "docker compose -p loyalty-prod up -d chạy sạch; frontend và backend accessible qua loyalty.ecom-bill.com."],
            ["9", "Báo cáo và HDSD đầy đủ", "Báo cáo đồ án hoàn chỉnh; HDSD mô tả luồng đăng ký đến đổi quà có ảnh minh họa."],
        ],
        caption="Các mục tiêu và tiêu chí đo lường của đề tài."
    )
    rb.p(
        "Mỗi mục tiêu sẽ được đối chiếu với kết quả đạt được ở Chương 5 — Kết luận. "
        "Đây cũng là căn cứ để xác định các phần việc còn tồn đọng và đề xuất "
        "hướng phát triển tiếp theo trong khuôn khổ luận văn tốt nghiệp."
    )
