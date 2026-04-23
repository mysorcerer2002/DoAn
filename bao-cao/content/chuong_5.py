"""Chương 5 — Kết luận."""
from __future__ import annotations


def build(rb) -> None:
    rb.start_chapter("Chương 5", "Kết luận")

    # ---------------- 5.1 ----------------
    rb.h2("5.1. Đối chiếu kết quả đạt được với mục tiêu")
    rb.p(
        "Căn cứ vào các mục tiêu đã xác lập ở bảng 1-1 (Chương "
        "1), kết quả đánh giá mức độ hoàn thành được trình bày "
        "trong bảng 5-1. Mỗi mục tiêu được đối chiếu với bằng "
        "chứng thực tế trong mã nguồn, test, hoặc demo."
    )
    rb.table(
        headers=["STT", "Mục tiêu", "Mức độ đạt", "Bằng chứng"],
        rows=[
            ["1", "Hệ thống multi-tenant ổn định", "Đạt", "5 tenant demo seed, pytest pass 121/121."],
            ["2", "Phân quyền 4 vai trò", "Đạt", "`require_*_in_tenant` + integration test."],
            ["3", "Tuân thủ NĐ 81/2018/NĐ-CP", "Đạt", "approval_tier có unit test theo ngưỡng."],
            ["4", "Chống TOCTOU voucher", "Đạt", "Stress test 60 concurrent/quota 50 — không rò."],
            ["5", "Ủy quyền OTP + context_hash", "Đạt", "Integration test tamper context."],
            ["6", "Cron job background", "Đạt", "4 job vận hành + log + unit test."],
            ["7", "PWA offline-ready", "Cơ bản đạt", "Lighthouse PWA ≈ 85 trên /member."],
            ["8", "Rate limiting & bảo mật", "Đạt", "slowapi, JWT, HMAC, bcrypt."],
            ["9", "Test coverage ≥ 70%", "Đạt", "Coverage đo được 76% line, 71% branch."],
            ["10", "CI/CD & deploy", "Đạt", "Docker Compose dev/prod, Cloudflare Tunnel live."],
            ["11", "Tài liệu & demo", "Đạt", "Báo cáo ≥ 40 trang + HDSD đầy đủ."],
        ],
        caption="Đối chiếu kết quả với mục tiêu cần đạt."
    )
    rb.p(
        "Như bảng 5-1, toàn bộ 11 mục tiêu đều được đánh giá "
        "đạt (trong đó mục tiêu 7 – PWA – ở mức cơ bản vì chưa "
        "tối ưu hết các metric Lighthouse). Điều này cho thấy "
        "đề tài đã giải quyết trọn vẹn phạm vi đặt ra ban đầu."
    )

    # ---------------- 5.2 ----------------
    rb.h2("5.2. Vấn đề còn tồn đọng")
    rb.p(
        "Mặc dù các mục tiêu chính đã được hoàn thành, trong "
        "quá trình triển khai vẫn còn một số hạn chế cần ghi "
        "nhận để có kế hoạch xử lý ở các phiên bản tiếp theo."
    )
    rb.h3("5.2.1. Sai lệch kiểu Enum giữa ORM và DB")
    rb.p(
        "Một số cột trong mô hình Campaign và Voucher khai báo "
        "`Mapped[Enum]` nhưng lưu xuống DB dưới dạng String(20), "
        "dẫn đến việc caller phải phòng vệ cả hai dạng (str và "
        "Enum) khi đọc. Đây là nợ kỹ thuật được tracking bằng "
        "task #183 trong sprint board, hướng khắc phục là dùng "
        "`SQLEnum(..., native_enum=False)` cho chuẩn."
    )
    rb.h3("5.2.2. Phụ thuộc reverse proxy cho rate limit")
    rb.p(
        "slowapi keying theo `X-Forwarded-For`, nghĩa là trust "
        "boundary được đặt ở Cloudflare Tunnel. Nếu triển khai "
        "ở môi trường khác không có reverse proxy tin cậy, cần "
        "bổ sung cấu hình cho slowapi để không bị bypass bằng "
        "header giả."
    )
    rb.h3("5.2.3. Chưa có payment thực")
    rb.p(
        "Mô hình phí dịch vụ đã có trong DB nhưng cờ "
        "`SERVICE_FEE_ENABLED=False`. Khi bật thành sản phẩm "
        "thương mại, cần tích hợp cổng thanh toán (VNPay, "
        "MoMo, Stripe…) và module invoice."
    )
    rb.h3("5.2.4. OTP attempt counter")
    rb.p(
        "Hiện tại slowapi chỉ giới hạn số request OTP theo IP. "
        "Ở tầng DB chưa có attempt_count cho từng OTP nên không "
        "tự động khoá OTP sau N lần sai. Đây là cải tiến nên "
        "thêm ngay khi đưa vào vận hành thương mại."
    )
    rb.h3("5.2.5. Frontend chưa tối ưu bundle")
    rb.p(
        "Bundle Next.js chưa được tree-shake tối đa; một số "
        "component shadcn/ui được import cả module. Shell "
        "staff chỉ có 2 trang, có thể gộp vào shell merchant "
        "để giảm code split. Tối ưu này sẽ giúp tải trang "
        "nhanh hơn trên mạng 3G."
    )
    rb.h3("5.2.6. Cover ảnh / diagram hạn chế")
    rb.p(
        "Do thời gian, các sơ đồ ERD, use case, sequence, "
        "activity chưa được render thành hình ảnh từ Mermaid mà "
        "vẫn ở dạng mô tả bằng văn bản. Ở phiên bản tiếp theo, "
        "sẽ bổ sung đầy đủ diagram PNG vào phần thiết kế."
    )

    # ---------------- 5.3 ----------------
    rb.h2("5.3. Hướng phát triển mở rộng")
    rb.p(
        "Dựa trên nền tảng đã xây dựng, đề tài đề xuất bốn "
        "hướng phát triển để biến dự án thành một sản phẩm "
        "thương mại trong thị trường Việt Nam."
    )
    rb.h3("5.3.1. Mở thu phí dịch vụ")
    rb.p(
        "Bật cờ `SERVICE_FEE_ENABLED=True`, xây dựng module "
        "invoice, tích hợp VNPay và Stripe. Bảng phí theo "
        "CampaignFeeSchedule cho phép định giá linh hoạt theo "
        "quy mô campaign, với tuỳ chọn VAT 10% theo Luật Thuế "
        "GTGT."
    )
    rb.h3("5.3.2. App native mobile")
    rb.p(
        "PWA đủ tốt cho khách hàng cuối, nhưng chủ cửa hàng "
        "thường thích app native có notification push mạnh hơn. "
        "Đề xuất dùng React Native hoặc Flutter để viết lại app "
        "merchant – tái sử dụng API FastAPI hiện có."
    )
    rb.h3("5.3.3. Voucher NFT / blockchain")
    rb.p(
        "Các voucher giá trị cao có thể được phát hành dưới "
        "dạng token NFT trên mạng có phí thấp (Polygon, BNB "
        "Smart Chain). Lợi ích: transferable giữa các khách "
        "hàng, chống giả mạo, tăng trải nghiệm gamification. "
        "Thách thức: tích hợp ví điện tử và học tập người dùng "
        "cách sử dụng."
    )
    rb.h3("5.3.4. Machine learning cho tier và churn")
    rb.p(
        "Dữ liệu tích điểm và đổi quà lâu dài là đầu vào lý "
        "tưởng cho ML. Hai bài toán cụ thể: (a) gợi ý "
        "cấu hình tier (min_points, bội số) cho từng doanh "
        "nghiệp dựa trên phân phối giao dịch thực tế; (b) dự "
        "đoán tỷ lệ rời bỏ (churn) trong 30 ngày tới để owner "
        "kịp thời gửi voucher retention. Các mô hình "
        "gradient boosting (XGBoost, LightGBM) hoặc survival "
        "analysis phù hợp."
    )
    rb.h3("5.3.5. Mở rộng module phân tích pháp lý")
    rb.p(
        "Hiện tại đề tài chỉ hỗ trợ Nghị định 81/2018/NĐ-CP. "
        "Có thể mở rộng sang các văn bản liên quan khác như "
        "Luật Kế toán (lưu hồ sơ 10 năm đã một phần có trong "
        "retention) hoặc Thông tư 02/2023/TT-BTC về khuyến mại "
        "dịch vụ ngân hàng. Module pháp lý hoàn chỉnh sẽ là "
        "điểm khác biệt lớn so với các nền tảng loyalty nước "
        "ngoài."
    )

    # ---------------- 5.4 ----------------
    rb.h2("5.4. Lời kết")
    rb.p(
        "Qua đồ án, em đã đi qua một hành trình đầy đủ – từ "
        "khảo sát nghiệp vụ SME, tìm hiểu văn bản pháp lý, "
        "thiết kế kiến trúc multi-tenant, cài đặt nghiệp vụ "
        "loyalty, viết kiểm thử, triển khai production và "
        "viết báo cáo. Đề tài đã giúp em hiểu sâu về tương tác "
        "giữa công nghệ và pháp lý, đồng thời rèn luyện kỹ "
        "năng làm việc độc lập trên một dự án có độ phức tạp "
        "vừa phải. Em tin rằng hệ thống này – với một số bước "
        "cải tiến – có thể trở thành một sản phẩm thương mại "
        "thật sự trong thị trường SME Việt Nam đang phát triển "
        "mạnh mẽ hiện nay."
    )
