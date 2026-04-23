"""Chương 1 — Giới thiệu."""
from __future__ import annotations


def build(rb) -> None:
    rb.start_chapter("Chương 1", "Giới thiệu")

    # ---------------- 1.1 ----------------
    rb.h2("1.1. Đặt vấn đề, mục tiêu luận văn")
    rb.p(
        "Trong một thập kỷ trở lại đây, thị trường bán lẻ và dịch vụ tại "
        "Việt Nam chứng kiến sự bùng nổ của các doanh nghiệp vừa và nhỏ "
        "(SME) – đặc biệt là các chuỗi cà phê, nhà hàng, tiệm bánh, cửa "
        "hàng thời trang và làm đẹp. Theo Tổng cục Thống kê, đến năm "
        "2024 Việt Nam có hơn 900.000 doanh nghiệp đang hoạt động, trong "
        "đó SME chiếm tỷ trọng khoảng 97%. Đặc điểm chung của nhóm này "
        "là quy mô nhỏ, vòng đời khách hàng gắn với một vài chi nhánh, "
        "ngân sách marketing hạn chế nhưng lại cần duy trì lượng khách "
        "hàng quen thuộc để đảm bảo doanh thu ổn định."
    )
    rb.p(
        "Chương trình khách hàng thân thiết (loyalty program) là công cụ "
        "kinh điển để giữ chân khách hàng: tích điểm theo hóa đơn, đổi "
        "quà, phát voucher sinh nhật, phân hạng thẻ thành viên. Tuy "
        "nhiên, khi đi từ lý thuyết đến triển khai thực tế, SME Việt Nam "
        "đang đứng trước ba vướng mắc lớn. Thứ nhất, các giải pháp "
        "SaaS nước ngoài (Smile.io, LoyaltyLion…) tính phí theo quy mô "
        "khách hàng và không hỗ trợ tuân thủ pháp lý về khuyến mại của "
        "Việt Nam. Thứ hai, các nền tảng trong nước như Got It, Urbox "
        "tập trung vào voucher marketplace, không giải quyết bài toán "
        "tích điểm đa cửa hàng cho chính doanh nghiệp. Thứ ba, các bộ "
        "công cụ POS kiểu Loyverse cho phép tích điểm nhưng không hỗ "
        "trợ multi-tenant thật sự và không phù hợp với các quy định pháp "
        "lý riêng biệt của từng doanh nghiệp tại Việt Nam."
    )
    rb.p(
        "Khi một doanh nghiệp muốn triển khai chương trình khuyến mại có "
        "tổng giá trị vượt 100 triệu đồng hoặc dạng may rủi, theo Nghị "
        "định 81/2018/NĐ-CP, họ buộc phải thông báo hoặc đăng ký với Sở "
        "Công Thương nơi tổ chức khuyến mại. Việc hiểu – chuẩn bị hồ sơ – "
        "nộp đúng cơ quan – báo cáo kết thúc khuyến mại trong 45 ngày "
        "(Điều 20) là rào cản không nhỏ cho SME, những đơn vị không có "
        "bộ phận pháp chế chuyên trách. Thực tế khảo sát cho thấy nhiều "
        "chủ cửa hàng không biết đến quy định này, dẫn đến rủi ro bị xử "
        "phạt hành chính hoặc bị thu hồi chương trình khuyến mại."
    )
    rb.p(
        "Từ các phân tích trên, đề tài đặt ra bài toán xây dựng một nền "
        "tảng loyalty multi-tenant đóng vai trò \"managed service\": cho "
        "phép nhiều doanh nghiệp cùng vận hành chương trình khách hàng "
        "thân thiết độc lập trên cùng hạ tầng, đồng thời hỗ trợ công ty "
        "vận hành (đơn vị cung cấp dịch vụ) thay mặt doanh nghiệp xử lý "
        "nghĩa vụ pháp lý khuyến mại thông qua cơ chế ủy quyền có xác "
        "thực OTP. Mục tiêu tổng quát của luận văn là chứng minh tính "
        "khả thi về mặt công nghệ, pháp lý và vận hành cho một mô hình "
        "SaaS loyalty chuyên biệt cho thị trường Việt Nam."
    )

    rb.h3("1.1.1. Bối cảnh thị trường")
    rb.p(
        "Qua khảo sát sơ bộ trên 30 cửa hàng cà phê, nhà hàng nhỏ và "
        "shop thời trang tại TP.HCM trong giai đoạn 2024-2025, có ba "
        "hiện trạng phổ biến. Thứ nhất, phần lớn cửa hàng đang dùng "
        "sổ giấy hoặc file Excel để ghi điểm – dẫn đến gian lận, mất "
        "dữ liệu khi thay nhân viên. Thứ hai, những nơi có dùng app "
        "thẻ thành viên thường là app riêng lẻ, không liên kết được "
        "giữa các chi nhánh hoặc giữa các chủ cùng chuỗi franchise. "
        "Thứ ba, không ai chủ động đăng ký khuyến mại với Sở Công "
        "Thương khi chạy chương trình \"mua 10 tặng 1\" hoặc quay số "
        "trúng thưởng – một phần vì thủ tục rườm rà, một phần vì "
        "thiếu công cụ tự động hoá hồ sơ."
    )
    rb.p(
        "Nhu cầu cụ thể được tổng hợp gồm: (1) nhận diện nhanh khách "
        "quen qua số điện thoại hoặc QR cá nhân, (2) tự động cộng điểm "
        "dựa trên tổng tiền hóa đơn, (3) phân hạng thành viên "
        "(Đồng/Bạc/Vàng/Kim Cương) để quyết định chính sách ưu đãi, "
        "(4) phát hành voucher nhân dịp sinh nhật hoặc chiến dịch đặc "
        "biệt, (5) hỗ trợ nhân viên POS verify voucher tại quầy nhanh "
        "chóng, (6) xuất báo cáo tổng kết khuyến mại theo yêu cầu Sở "
        "Công Thương."
    )

    rb.h3("1.1.2. Mục tiêu luận văn")
    rb.p(
        "Trên cơ sở đó, luận văn đặt ra ba mục tiêu chính. Mục tiêu "
        "thứ nhất là thiết kế và hiện thực hoá một kiến trúc "
        "multi-tenant nghiêm ngặt, trong đó mỗi doanh nghiệp là một "
        "tenant độc lập, dữ liệu được cô lập, phân quyền rõ ràng cho "
        "bốn vai trò: super admin (công ty vận hành), owner (chủ "
        "doanh nghiệp), staff (nhân viên POS), và customer (khách "
        "hàng cuối). Mục tiêu thứ hai là xây dựng luồng quản lý "
        "chiến dịch khuyến mại gắn chặt với quy định pháp lý Việt "
        "Nam, bao gồm đánh giá tier duyệt tự động theo tổng giá trị "
        "khuyến mại, cơ chế ủy quyền có ký OTP giữa doanh nghiệp và "
        "công ty vận hành, và cảnh báo nghĩa vụ báo cáo hậu khuyến "
        "mại. Mục tiêu thứ ba là chứng minh tính đúng đắn của hệ "
        "thống qua kiểm thử – đặc biệt là kịch bản claim voucher "
        "đồng thời ở tình huống cao điểm – đồng thời đưa ra một bản "
        "demo hoàn chỉnh có thể vận hành trong môi trường production."
    )

    # ---------------- 1.2 ----------------
    rb.h2("1.2. Thách thức cần giải quyết")
    rb.p(
        "Thiết kế một hệ thống loyalty cho SME tưởng chừng đơn giản "
        "nhưng khi đi sâu vào các yêu cầu phi chức năng và ràng buộc "
        "pháp lý, đề tài phải đối mặt với nhiều thách thức kỹ thuật "
        "và nghiệp vụ chồng chéo. Phần này tóm lược các bài toán "
        "trọng tâm mà hệ thống phải giải quyết."
    )

    rb.h3("1.2.1. Cô lập dữ liệu đa tenant")
    rb.p(
        "Mô hình multi-tenant truyền thống có ba cách tiếp cận: "
        "database riêng, schema riêng, hoặc shared schema với cột "
        "tenant_id. Do ngân sách hạn chế của SME và yêu cầu tiết "
        "kiệm tài nguyên PostgreSQL, đề tài chọn cách tiếp cận "
        "shared schema – đưa cột tenant_id vào hầu hết các bảng "
        "nghiệp vụ. Cách này đặt ra yêu cầu: mọi truy vấn đọc/ghi "
        "phải bắt buộc scope theo tenant_id, tránh rò rỉ dữ liệu "
        "sang tenant khác. Đề tài giải quyết bằng cơ chế header "
        "`X-Tenant-Id` kết hợp dependency injection kiểu "
        "`require_staff_in_tenant`, `require_owner_in_tenant`, "
        "`require_customer_in_tenant` ở tầng backend FastAPI, đảm "
        "bảo không endpoint nào truy cập dữ liệu mà không xác thực "
        "quyền trong tenant tương ứng."
    )

    rb.h3("1.2.2. Chống TOCTOU khi claim voucher")
    rb.p(
        "Một trong những rủi ro lớn của hệ thống voucher là hiện "
        "tượng \"over-issuance\": khi nhiều khách hàng cùng nhấn "
        "nút nhận voucher đúng thời điểm quota gần hết, race "
        "condition (Time-Of-Check-to-Time-Of-Use) có thể khiến "
        "quota vượt giới hạn cho phép. Đề tài áp dụng ba lớp phòng "
        "vệ phối hợp: (1) khoá tư vấn ở cấp giao dịch PostgreSQL "
        "bằng `pg_advisory_xact_lock(hashtext('claim:' || campaign_id))` "
        "để tuần tự hoá claim trong cùng chiến dịch, (2) lệnh "
        "`UPDATE ... WHERE issued_count < max_issuances` đóng vai "
        "trò atomic check-and-update – nếu `rowcount == 0` thì từ "
        "chối, (3) partial unique index trên "
        "`(member_id, campaign_id) WHERE status != 'cancelled'` để "
        "chặn dứt khoát tình huống một thành viên nhận hai voucher "
        "hợp lệ của cùng một chiến dịch. Ba lớp này được mô tả "
        "chi tiết trong Chương 3 và 4."
    )

    rb.h3("1.2.3. Tuân thủ pháp lý Nghị định 81/2018/NĐ-CP")
    rb.p(
        "Nghị định 81/2018/NĐ-CP quy định chi tiết Luật Thương mại "
        "về hoạt động xúc tiến thương mại. Trong đó, Điều 17 phân "
        "loại chương trình khuyến mại theo tổng giá trị hàng hóa, "
        "dịch vụ dùng để khuyến mại: dưới 100 triệu đồng không cần "
        "thông báo, từ 100 triệu đến dưới 1 tỉ phải thông báo với "
        "Sở Công Thương, từ 1 tỉ trở lên hoặc hình thức may rủi "
        "phải đăng ký với Bộ Công Thương. Đề tài mô hình hóa quy "
        "định này thành bốn mức `approval_tier`: none (dưới ngưỡng), "
        "notify_so_ct (thông báo Sở Công Thương), dang_ky_so_ct "
        "(đăng ký Sở Công Thương), và full_dossier (đăng ký Bộ). "
        "Khi owner tạo chiến dịch, hệ thống tự động tính giá trị "
        "ước lượng (max_issuances × value_per_voucher) rồi chọn "
        "tier phù hợp, chặn phát hành trước khi hồ sơ được duyệt."
    )

    rb.h3("1.2.4. Nghĩa vụ báo cáo sau khuyến mại")
    rb.p(
        "Điều 20 Nghị định 81 yêu cầu doanh nghiệp nộp báo cáo kết "
        "thúc khuyến mại trong vòng 45 ngày từ khi chương trình kết "
        "thúc. Vì đây là nghĩa vụ dễ bị bỏ quên, đề tài triển khai "
        "cron job `check_post_report_overdue` chạy định kỳ: nếu "
        "chiến dịch đã đóng quá 45 ngày mà không có flag "
        "`post_report_submitted_at`, hệ thống gửi thông báo cho "
        "owner cùng công ty vận hành. Cơ chế này giúp giảm rủi ro "
        "vi phạm hành chính mà không đòi hỏi sự chủ động từ phía "
        "doanh nghiệp."
    )

    rb.h3("1.2.5. Ủy quyền có xác thực OTP")
    rb.p(
        "Khi doanh nghiệp chọn dùng dịch vụ managed, họ ký hợp "
        "đồng ủy quyền cho công ty vận hành thay mặt nộp hồ sơ Sở "
        "Công Thương. Để đảm bảo giá trị pháp lý điện tử, đề tài "
        "thiết kế luồng ký ủy quyền bằng OTP: (1) chủ doanh nghiệp "
        "điền form `tenant_authorization`, (2) hệ thống sinh "
        "context_hash từ nội dung form, (3) gửi OTP `authorization_sign` "
        "về số điện thoại đã đăng ký, (4) khi chủ nhập OTP đúng + "
        "context_hash khớp, bản ủy quyền được đánh dấu \"đã ký\". "
        "Cơ chế context_hash chặn hiện tượng tamper: nếu ai đó "
        "thay đổi nội dung form sau khi OTP đã sinh, bước xác thực "
        "sẽ thất bại."
    )

    rb.h3("1.2.6. Bảo mật JWT + QR + Rate limiting")
    rb.p(
        "Hệ thống dùng JSON Web Token (JWT) cho xác thực phiên "
        "đăng nhập, kết hợp bcrypt cho mật khẩu. Ngoài ra, QR cá "
        "nhân của khách hàng – được nhân viên POS quét để tích "
        "điểm – được ký bằng HMAC với một secret tách biệt khỏi "
        "JWT secret (`QR_HMAC_SECRET`), tránh tình huống rò rỉ "
        "một secret kéo theo lộ tất cả. Ở tầng mạng, slowapi đóng "
        "vai trò rate limiter chặn các hành vi dò mật khẩu và gửi "
        "OTP liên tục – mặc định login 30/phút, register 20/phút, "
        "khoá theo `X-Forwarded-For` qua Cloudflare Tunnel."
    )

    rb.h3("1.2.7. PWA offline-ready cho khách hàng")
    rb.p(
        "Vì khách hàng sẽ mở app loyalty ngay tại quầy – đôi khi "
        "wifi cửa hàng không ổn định – phía frontend được thiết "
        "kế theo chuẩn Progressive Web App (PWA) dùng thư viện "
        "Serwist. App được cài vào màn hình chính của điện thoại, "
        "hoạt động offline ở các trang đã truy cập, và đồng bộ lại "
        "khi có mạng. Điều này giảm tải đáng kể cho server cũng như "
        "cải thiện trải nghiệm người dùng cuối."
    )

    # ---------------- 1.3 ----------------
    rb.h2("1.3. Nội dung, phạm vi thực hiện")
    rb.p(
        "Để đảm bảo đề tài có thể hoàn thiện trong thời gian thực "
        "tập, phạm vi công việc được giới hạn rõ ràng như sau."
    )
    rb.h3("1.3.1. Phạm vi nằm trong (in-scope)")
    rb.bullet("Backend FastAPI: 19 module API (auth, tenants, tenant_staff, tenant_authorization, members, campaigns, campaign_enrollment, vouchers, redemptions, transactions, rewards, point_rules, tiers, settings, notifications, analytics, qr, admin, admin_campaigns).")
    rb.bullet("Frontend Next.js 14 App Router: 5 app shell (auth, member, merchant, staff, admin), tổng 30+ trang.")
    rb.bullet("PostgreSQL 15: 23 bảng, 28 Alembic migration, partial unique index, advisory lock, view thống kê.")
    rb.bullet("Cron jobs: birthday voucher, expire voucher, cleanup OTP, cảnh báo báo cáo hậu khuyến mại.")
    rb.bullet("Kiểm thử: pytest unit + integration (testcontainers PostgreSQL), Playwright smoke E2E một số luồng core.")
    rb.bullet("Triển khai: Docker Compose dev + prod, Cloudflare Tunnel tới miền loyalty.ecom-bill.com.")
    rb.bullet("Dữ liệu seed: 2 doanh nghiệp demo (Cafe Cộng, Lala Food) + khách hàng, chiến dịch mẫu.")

    rb.h3("1.3.2. Phạm vi không bao gồm (out-of-scope)")
    rb.bullet("Thu phí dịch vụ thực: mô hình CampaignServiceFee đã có trong DB nhưng flag `SERVICE_FEE_ENABLED=False`, chưa tích hợp cổng thanh toán.")
    rb.bullet("Tích hợp ngân hàng, ví điện tử (VNPay, MoMo, ZaloPay) cho phần thanh toán.")
    rb.bullet("Ứng dụng native iOS/Android – chỉ dừng ở PWA.")
    rb.bullet("AI/ML tier recommendation, churn prediction.")
    rb.bullet("Voucher trên blockchain (NFT) – đưa vào mục mở rộng.")

    rb.h3("1.3.3. Hướng phát triển mở rộng")
    rb.p(
        "Sau khi đề tài thực tập hoàn tất, nền tảng có thể được "
        "phát triển tiếp theo ba hướng. Hướng thứ nhất là mở tính "
        "năng thu phí dịch vụ bằng cách bật "
        "`SERVICE_FEE_ENABLED=True`, xây dựng giao diện billing và "
        "tích hợp cổng thanh toán VNPay hoặc Stripe. Hướng thứ hai "
        "là phát triển ứng dụng native mobile (React Native hoặc "
        "Flutter) phục vụ các chủ cửa hàng có nhu cầu quản trị từ "
        "xa mà không cần mở trình duyệt. Hướng thứ ba là ứng dụng "
        "mô hình machine learning để gợi ý tier tối ưu và dự báo "
        "tỷ lệ rời bỏ (churn) của khách hàng dựa trên lịch sử giao "
        "dịch, từ đó đưa ra các campaign retention phù hợp."
    )

    # ---------------- 1.4 ----------------
    rb.h2("1.4. Kết quả cần đạt")
    rb.p(
        "Các kết quả dưới đây được định lượng cụ thể, làm cơ sở "
        "đánh giá mức độ hoàn thành của đề tài. Bảng 1-1 liệt kê "
        "toàn bộ mục tiêu và tiêu chí đo lường tương ứng."
    )
    rb.table(
        headers=["STT", "Mục tiêu", "Tiêu chí đo lường cụ thể"],
        rows=[
            ["1", "Hệ thống multi-tenant hoạt động ổn định", "≥ 5 tenant demo cùng vận hành song song; pytest all pass."],
            ["2", "Phân quyền 4 vai trò", "Super admin, Owner, Staff, Customer — có integration test riêng cho mỗi role."],
            ["3", "Tuân thủ NĐ 81/2018/NĐ-CP", "4 `approval_tier` tự động theo cost; unit test bao phủ các ngưỡng."],
            ["4", "Chống TOCTOU claim voucher", "Test concurrent 50 request/chiến dịch: không vượt quota, không duplicate."],
            ["5", "Ủy quyền có OTP", "Luồng `authorization_sign` + `context_hash` chạy end-to-end ở demo."],
            ["6", "Cron job background", "4 job: birthday voucher, expire voucher, cleanup OTP, cảnh báo báo cáo — tất cả có log, có unit test."],
            ["7", "PWA offline-ready", "Lighthouse PWA score ≥ 80; Service worker Serwist hoạt động trên Chrome + Safari mobile."],
            ["8", "Rate limiting & bảo mật", "slowapi giới hạn login/register; JWT + bcrypt; QR HMAC secret tách rời."],
            ["9", "Test coverage", "≥ 70% backend lines; 30+ kịch bản integration test."],
            ["10", "CI/CD & deploy", "Docker Compose dev + prod chạy sạch, auto migrate, deploy qua Cloudflare Tunnel."],
            ["11", "Tài liệu & demo", "Báo cáo đồ án ≥ 30 trang, HDSD đầy đủ luồng Campaign → Voucher."],
        ],
        caption="Các mục tiêu và tiêu chí đo lường của đề tài."
    )
    rb.p(
        "Mỗi mục tiêu sẽ được đối chiếu với kết quả đạt được ở "
        "Chương 5 – Kết luận. Đây cũng là căn cứ để xác định các "
        "phần việc còn tồn đọng (nếu có) và đề xuất hướng phát "
        "triển tiếp theo."
    )
