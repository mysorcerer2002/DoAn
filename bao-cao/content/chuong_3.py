"""Chương 3 — Thiết kế hệ thống."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # D:/DoAn


def _img(rb, filename: str, caption: str, width_cm: float = 14.0) -> None:
    path = ROOT / filename
    rb.figure(str(path), caption, width_cm=width_cm)


def build(rb) -> None:
    rb.start_chapter("Chương 3", "Thiết kế hệ thống")

    # ---------------- 3.1 ----------------
    rb.h2("3.1. Mô hình dữ liệu")
    rb.p(
        "Chương này trình bày thiết kế cơ sở dữ liệu của hệ thống "
        "theo ba mức: mức ý niệm (Conceptual Data Model), mức luận "
        "lý (Logical Data Model) và mức vật lý (Physical Data "
        "Model). Mỗi mức đi từ trừu tượng đến chi tiết, đảm bảo "
        "thiết kế vừa phản ánh đúng nghiệp vụ vừa có thể hiện "
        "thực hóa bằng PostgreSQL."
    )

    rb.h3("3.1.1. Mức ý niệm (Conceptual)")
    rb.p(
        "Ở mức ý niệm, hệ thống được mô hình hóa thành 10 thực "
        "thể chính phản ánh các đối tượng nghiệp vụ cốt lõi, bao "
        "gồm: User (người dùng hệ thống), Tenant (doanh nghiệp), "
        "Membership (quan hệ khách hàng – doanh nghiệp), Tier "
        "(hạng thành viên), Transaction (giao dịch POS tích "
        "điểm), PointLedger (sổ cái điểm), Reward (phần thưởng "
        "có thể đổi), Redemption (lệnh đổi quà), Campaign (chiến "
        "dịch khuyến mại), Voucher (phiếu giảm giá đã cấp)."
    )
    rb.p(
        "Ngoài 10 thực thể chính, thiết kế cần 13 thực thể phụ "
        "trợ để hỗ trợ các nghiệp vụ mở rộng: VerificationCode "
        "(OTP nhiều loại), Notification (thông báo in-app), "
        "PointRule (cấu hình quy tắc quy đổi điểm theo tenant), "
        "TenantStaff (liên kết nhân viên với doanh nghiệp), "
        "TenantSettingsAudit (audit log), TenantAuthorization "
        "(ủy quyền công ty vận hành), CampaignTemplate (mẫu "
        "chiến dịch pháp lý), CampaignApprovalEvent (sự kiện "
        "duyệt), CampaignRegulatorySubmission (hồ sơ Sở CT), "
        "CampaignIssuance (định mức phát hành), "
        "CampaignServiceFee (phí dịch vụ), "
        "CampaignFeeSchedule (cấu hình phí), các enum helper."
    )
    rb.table(
        headers=["Nhóm", "Thực thể", "Vai trò"],
        rows=[
            ["Định danh", "User", "Tài khoản đăng nhập, chứa role hệ thống."],
            ["Định danh", "Tenant", "Doanh nghiệp SME, 1 tenant = 1 shop/chuỗi."],
            ["Quan hệ", "Membership", "Liên kết user với tenant, giữ tier + điểm."],
            ["Phân hạng", "Tier", "Ngưỡng điểm, tên hạng, bội số tích điểm."],
            ["Giao dịch", "Transaction", "Bill POS, pos_bill_id unique trong tenant."],
            ["Sổ cái", "PointLedger", "Tất cả biến động điểm (+ earn, − redeem)."],
            ["Quà tặng", "Reward", "Phần thưởng có thể đổi bằng điểm."],
            ["Đổi quà", "Redemption", "Lệnh đổi quà, mã verify ở POS."],
            ["Khuyến mại", "Campaign", "Chiến dịch giảm giá, có vòng đời duyệt."],
            ["Khuyến mại", "Voucher", "Phiếu giảm giá cấp cho member, có QR."],
            ["Hỗ trợ", "VerificationCode", "OTP register/login/authorization_sign."],
            ["Hỗ trợ", "TenantAuthorization", "Hợp đồng ủy quyền operator."],
            ["Hỗ trợ", "CampaignRegulatorySubmission", "Hồ sơ gửi Sở Công Thương."],
        ],
        caption="Các nhóm thực thể chính trong mô hình ý niệm."
    )

    rb.h3("3.1.2. Mức luận lý (Logical)")
    rb.p(
        "Ở mức luận lý, các thực thể được chuyển thành quan hệ "
        "với khóa chính, khóa ngoại, ràng buộc unique. Một số "
        "điểm thiết kế đáng chú ý."
    )
    rb.p(
        "Thứ nhất, User được tách khỏi Membership: một người có "
        "thể là khách hàng ở nhiều doanh nghiệp khác nhau, nhưng "
        "chỉ có một tài khoản đăng nhập chung. Điều này cho phép "
        "app khách hàng hiển thị danh sách tất cả membership "
        "của người dùng theo thẻ duy nhất – rất phù hợp với mô "
        "hình nền tảng dùng chung hạ tầng."
    )
    rb.p(
        "Thứ hai, Transaction có unique constraint "
        "(tenant_id, pos_bill_id) để chặn trường hợp nhân viên "
        "POS lỡ bấm \"tích điểm\" hai lần cho cùng một hóa đơn. "
        "Thiết kế này tận dụng IntegrityError + global handler "
        "trả về 409 tiếng Việt cho client."
    )
    rb.p(
        "Thứ ba, Voucher có unique code per tenant, đồng thời "
        "có partial unique index trên "
        "(member_id, campaign_id) WHERE status != 'cancelled' – "
        "chặn việc cùng một khách nhận hai voucher hợp lệ của "
        "cùng một chiến dịch."
    )
    rb.p(
        "Thứ tư, TenantAuthorization có trường context_hash – "
        "mã hash SHA-256 của nội dung ủy quyền tại thời điểm sinh "
        "OTP. Khi user xác nhận OTP, hệ thống tính lại hash và "
        "so sánh; nếu khác, tức có thao tác tamper, quá trình ký "
        "sẽ bị từ chối."
    )

    rb.h3("3.1.3. Mức vật lý (Physical) — DDL thực")
    rb.p(
        "Ở mức vật lý, thiết kế được chuyển hóa thành 23 bảng "
        "PostgreSQL thông qua 28 migration Alembic. Một số ràng "
        "buộc và chỉ mục quan trọng được liệt kê trong bảng 3-2."
    )
    rb.table(
        headers=["Đối tượng", "Loại", "Mục đích"],
        rows=[
            ["ix_user_email_unique", "Unique index", "Email tồn tại duy nhất toàn hệ thống."],
            ["ix_membership_tenant_phone", "Partial unique", "Khách duy nhất theo (tenant, phone)."],
            ["ix_transaction_tenant_bill", "Unique", "Tránh tích điểm trùng bill."],
            ["ix_voucher_tenant_code", "Unique", "Mã voucher không đụng trong tenant."],
            ["ix_voucher_member_campaign_active", "Partial unique", "1 voucher active / (member, campaign)."],
            ["pg_advisory_xact_lock('claim:' || id)", "Advisory lock", "Tuần tự hóa claim chiến dịch."],
            ["check_approval_tier", "Check constraint", "approval_tier ∈ {none, notify_so_ct, dang_ky_so_ct, full_dossier}."],
            ["trg_voucher_validate_max_issuances", "Trigger", "Tầng bảo vệ cuối chống over-issuance."],
            ["v_campaign_stats", "View", "Tổng hợp claim/used/remaining cho dashboard."],
        ],
        caption="Các ràng buộc và đối tượng PostgreSQL quan trọng."
    )

    # ---------------- 3.2 ----------------
    rb.h2("3.2. Mô hình xử lý")
    rb.p(
        "Phần này mô tả các use case chi tiết và cách hệ thống "
        "xử lý các luồng nghiệp vụ trọng yếu, đi kèm các điểm "
        "cài đặt kỹ thuật đáng chú ý."
    )

    rb.h3("3.2.1. Use case chi tiết")

    rb.h4("3.2.1.1. UC-01: Đăng ký merchant")
    rb.p(
        "Actor: Owner (chưa có tài khoản). Tiền điều kiện: không "
        "có. Luồng chính: (1) Owner truy cập /register/merchant, "
        "nhập thông tin doanh nghiệp ba bước: thông tin cơ bản, "
        "thông tin liên hệ, thông tin pháp lý. (2) Hệ thống tự "
        "sinh slug unique dựa trên tên doanh nghiệp, kiểm tra "
        "tiền tố LIKE để tránh trùng. (3) Tạo tenant trạng thái "
        "pending_approval, gửi email thông báo cho super admin. "
        "(4) Super admin đăng nhập admin portal, xem danh sách "
        "tenant chờ duyệt, bấm duyệt. (5) Tenant chuyển sang "
        "active, owner nhận email kèm liên kết setup. "
        "Hậu điều kiện: tenant có thể login, bắt đầu khai báo "
        "tier, reward."
    )

    rb.h4("3.2.1.2. UC-02: POS tích điểm")
    rb.p(
        "Actor: Staff. Tiền điều kiện: khách đã là membership "
        "của tenant. Luồng chính: (1) Staff đăng nhập staff "
        "shell. (2) Scan QR khách (đã ký HMAC bằng "
        "QR_HMAC_SECRET). (3) Backend verify chữ ký, tìm "
        "membership theo (tenant, user). (4) Nhập tổng tiền hóa "
        "đơn, pos_bill_id. (5) Service tính số điểm theo "
        "PointRule (ví dụ 10.000 đồng = 1 điểm × bội số tier). "
        "(6) Insert Transaction + PointLedger, cập nhật "
        "current_points. (7) Trigger kiểm tra tier, thăng hạng "
        "nếu đủ điểm. Hậu điều kiện: khách có bản ghi transaction "
        "với điểm vừa cộng."
    )

    rb.h4("3.2.1.3. UC-03: Đổi quà")
    rb.p(
        "Actor: Customer (sau đó Staff). Tiền điều kiện: đủ "
        "điểm, reward còn stock. Luồng chính: (1) Customer "
        "chọn reward trên app. (2) Service verify điểm ≥ "
        "reward.cost, stock > 0, trạng thái active. (3) Trừ điểm, "
        "giảm stock, tạo Redemption với mã redeem_code + QR. "
        "(4) Staff scan redeem_code tại POS, xác nhận, mark used. "
        "Luồng thay thế: nếu hết stock, trả 409; nếu điểm không "
        "đủ, trả 400."
    )

    rb.h4("3.2.1.4. UC-04: Tạo chiến dịch")
    rb.p(
        "Actor: Owner. Luồng chính: (1) Owner truy cập "
        "/merchant/campaigns/new. (2) Chọn campaign template "
        "(pre-set các tham số pháp lý). (3) Nhập tên, thời "
        "gian, loại giảm giá (% hoặc amount), max_issuances, "
        "giá trị mỗi voucher. (4) Backend compute estimated_cost "
        "= max_issuances × value_per_voucher; chọn "
        "approval_tier theo ngưỡng NĐ 81. (5) Lưu campaign "
        "status=draft. (6) Nếu tier > none, UI yêu cầu owner "
        "chuyển sang UC-05 Nộp hồ sơ."
    )

    rb.h4("3.2.1.5. UC-05: Nộp hồ sơ Sở Công Thương")
    rb.p(
        "Actor: Owner hoặc Operator (nếu có ủy quyền). Luồng "
        "chính: (1) Tạo CampaignRegulatorySubmission với "
        "doc_refs (URL hồ sơ PDF), số điện thoại, địa chỉ Sở CT. "
        "(2) Gửi submission, chuyển campaign sang "
        "status=pending_regulatory. (3) Sau khi Sở CT duyệt, "
        "Operator bấm \"đánh dấu đã duyệt\", cập nhật "
        "approval_event + chuyển campaign sang status=approved."
    )

    rb.h4("3.2.1.6. UC-06: Claim voucher (lõi race condition)")
    rb.p(
        "Actor: Customer. Tiền điều kiện: campaign active. "
        "Luồng chính: (1) Customer bấm \"Nhận voucher\" trên "
        "app. (2) Service bắt đầu transaction, acquire "
        "pg_advisory_xact_lock(hashtext('claim:'||campaign_id)). "
        "(3) Lệnh UPDATE campaigns SET issued_count = "
        "issued_count + 1 WHERE id = :id AND issued_count < "
        "max_issuances; nếu rowcount=0, abort. (4) INSERT "
        "Voucher với status='issued', member_id, code random. "
        "(5) Commit; advisory lock được release cùng "
        "transaction. Partial unique index sẽ chặn thêm nếu "
        "customer cố claim lần nữa. Luồng thay thế: nếu quota "
        "hết, trả 409 kèm message \"Hết suất\"."
    )

    rb.h4("3.2.1.7. UC-07: Ủy quyền OTP")
    rb.p(
        "Actor: Owner. Luồng chính: (1) Owner tạo authorization "
        "với nội dung (phạm vi ủy quyền, thời hạn, operator "
        "được ủy quyền). (2) Service compute context_hash = "
        "sha256(canonical(payload)), sinh OTP "
        "authorization_sign, gửi SMS. (3) Owner nhập OTP; "
        "Service verify OTP + đọc lại authorization, tính lại "
        "context_hash, so sánh. Nếu khớp, đánh dấu signed_at, "
        "ghi TenantSettingsAudit."
    )

    rb.h4("3.2.1.8. UC-08: Thăng hạng tự động")
    rb.p(
        "Actor: System. Kích hoạt: sau mỗi transaction cộng "
        "điểm. Luồng: (1) Service đọc tenant tiers sắp xếp theo "
        "min_points giảm dần. (2) Tìm tier đầu tiên có "
        "min_points ≤ current_points. (3) Nếu khác tier hiện "
        "tại, cập nhật membership.tier_id, ghi "
        "PointLedger loại 'tier_upgrade' ghi chú tiếng Việt."
    )

    rb.h3("3.2.2. Sơ đồ tuần tự các luồng xử lý chính")
    rb.p(
        "Luồng Đăng nhập JWT + chọn tenant được mô tả bởi Hình "
        "3-1. Người dùng gửi email/mật khẩu tới /auth/login; "
        "AuthService verify bcrypt và trả về access_token kèm "
        "danh sách memberships. Frontend lưu token vào Zustand "
        "auth-store, chọn tenant mặc định qua tenant-store và "
        "tự inject header X-Tenant-Id cho mọi request tiếp theo "
        "thông qua axios interceptor. Dependency "
        "require_customer_in_tenant hoặc require_owner_in_tenant "
        "trong FastAPI đảm bảo mọi endpoint được scope đúng tenant."
    )
    _img(rb, "bao-cao/diagrams/mermaid/seq_login_tenant.png",
         "Sơ đồ tuần tự — Đăng nhập JWT và chọn tenant.")

    rb.p(
        "Luồng Claim voucher được mô tả chi tiết bởi Hình 3-2 "
        "với ba actor kỹ thuật: Client (App PWA khách hàng), "
        "FastAPI Service, và PostgreSQL. Client gửi POST "
        "/campaigns/{id}/claim kèm JWT và X-Tenant-Id. FastAPI "
        "qua dependency xác thực customer-in-tenant, tạo một "
        "AsyncSession. Service mở transaction, gọi "
        "pg_advisory_xact_lock(hashtext('claim:' || campaign_id)). "
        "Các request khác cùng campaign_id sẽ được xếp hàng tại "
        "bước này. Service thực thi UPDATE quota guard; nếu "
        "rowcount=1, tiếp tục INSERT voucher; nếu rowcount=0, "
        "raise CampaignQuotaExceededError. Transaction commit – "
        "lock release. Ngay khi transaction commit, request đứng "
        "sau sẽ nối tiếp. Đây là cơ chế đảm bảo tính an toàn mà "
        "vẫn tối ưu được throughput."
    )
    _img(rb, "bao-cao/diagrams/mermaid/seq_claim_voucher.png",
         "Sơ đồ tuần tự — Khách hàng claim voucher (chống TOCTOU).")

    rb.p(
        "Luồng Đổi quà bằng OTP (Hình 3-3) là một cơ chế hai "
        "bước request-otp / confirm-otp dùng HMAC-SHA256 để ràng "
        "buộc mã OTP với đúng bộ ba (reward_id, member_id, "
        "staff_id). Nếu kẻ xấu cố sử dụng OTP trong một ngữ cảnh "
        "khác (khác reward hoặc khác khách), context_hash không "
        "khớp và hệ thống trả về 400 InvalidOTPError. Thời hạn "
        "OTP là 3 phút; chống abuse bằng slowapi rate limit."
    )
    _img(rb, "bao-cao/diagrams/mermaid/seq_redeem_otp.png",
         "Sơ đồ tuần tự — Đổi quà bằng OTP ràng buộc context_hash.")

    rb.h3("3.2.3. Sơ đồ hoạt động của vòng đời chiến dịch và voucher")
    rb.p(
        "Campaign có vòng đời hoạt động (Hình 3-4): draft → "
        "pending_regulatory (nếu tier ≥ notify_so_ct) → approved "
        "→ active → ended → post_report_submitted / overdue. Hệ "
        "thống thực thi chuyển trạng thái bằng kết hợp giữa thao "
        "tác thủ công (owner và super admin) và cron "
        "(expire_vouchers, check_post_report_overdue). Sau khi "
        "campaign kết thúc, cron tự động tính hạn 45 ngày theo "
        "Điều 20 NĐ 81/2018/NĐ-CP để cảnh báo báo cáo hậu khuyến "
        "mại."
    )
    _img(rb, "bao-cao/diagrams/mermaid/act_campaign_lifecycle.png",
         "Sơ đồ hoạt động — Vòng đời chiến dịch khuyến mại "
         "(NĐ 81/2018/NĐ-CP).")

    rb.p(
        "Tương ứng, mỗi voucher phát hành có vòng đời riêng "
        "(Hình 3-5): active → used (khi staff áp dụng thành công "
        "tại POS) hoặc active → expired (khi cron "
        "expire_vouchers phát hiện now > expires_at). Hai nhánh "
        "này chạy song song và được idempotent hóa để tránh "
        "race giữa POS và cron."
    )
    _img(rb, "bao-cao/diagrams/mermaid/act_voucher_lifecycle.png",
         "Sơ đồ hoạt động — Vòng đời voucher.")

    # ---------------- 3.3 ----------------
    rb.h2("3.3. Hệ thống màn hình")
    rb.p(
        "Frontend được chia thành năm app shell theo vai trò, "
        "triển khai bằng Next.js 14 App Router route groups. "
        "Bảng 3-3 liệt kê toàn bộ trang chính kèm vai trò truy "
        "cập và chức năng tóm tắt."
    )
    rb.table(
        headers=["App shell", "Route", "Vai trò", "Chức năng"],
        rows=[
            ["(auth)", "/login", "Mọi vai trò", "Đăng nhập chung."],
            ["(auth)", "/register", "Customer", "Đăng ký tài khoản khách."],
            ["(auth)", "/register/merchant", "Owner", "Đăng ký doanh nghiệp 3 bước."],
            ["(member)", "/member", "Customer", "Tổng quan điểm và hoạt động."],
            ["(member)", "/member/qr", "Customer", "QR cá nhân để POS quét."],
            ["(member)", "/member/shops", "Customer", "Danh sách cửa hàng đã tham gia."],
            ["(member)", "/member/vouchers", "Customer", "Danh sách voucher khả dụng."],
            ["(member)", "/member/rewards", "Customer", "Danh sách quà tặng có thể đổi."],
            ["(member)", "/member/transactions", "Customer", "Lịch sử giao dịch."],
            ["(member)", "/member/profile", "Customer", "Thông tin cá nhân, đổi mật khẩu."],
            ["(merchant)", "/merchant", "Owner", "Dashboard tenant: doanh thu, campaign."],
            ["(merchant)", "/merchant/members", "Owner", "Danh sách khách hàng + tier."],
            ["(merchant)", "/merchant/tiers", "Owner", "Cấu hình hạng thành viên."],
            ["(merchant)", "/merchant/rewards", "Owner", "Quản trị phần thưởng."],
            ["(merchant)", "/merchant/campaigns", "Owner", "Danh sách chiến dịch khuyến mại."],
            ["(merchant)", "/merchant/campaigns/new", "Owner", "Wizard tạo chiến dịch."],
            ["(merchant)", "/merchant/campaigns/{id}", "Owner", "Chi tiết chiến dịch + nộp hồ sơ."],
            ["(merchant)", "/merchant/staff", "Owner", "Quản lý nhân viên POS."],
            ["(merchant)", "/merchant/settings", "Owner", "Cài đặt tenant, ủy quyền."],
            ["(staff)", "/staff", "Staff", "Trang chủ POS: tra cứu khách."],
            ["(staff)", "/staff/pos", "Staff", "POS tích điểm + verify voucher."],
            ["(admin)", "/admin", "Super admin", "Dashboard toàn hệ thống."],
            ["(admin)", "/admin/tenants", "Super admin", "Duyệt và quản lý tenant."],
            ["(admin)", "/admin/campaigns", "Super admin", "Duyệt chiến dịch pháp lý."],
            ["(admin)", "/admin/users", "Super admin", "Quản lý người dùng hệ thống."],
            ["(admin)", "/admin/audit", "Super admin", "Xem audit log tenant settings."],
        ],
        caption="Danh sách trang chính của hệ thống."
    )

    rb.p(
        "Một số màn hình điển hình được minh hoạ dưới đây để "
        "cung cấp hình dung trực quan về giao diện và trải "
        "nghiệm người dùng."
    )
    _img(rb, "landing-polished-desktop.png",
         "Trang chủ giới thiệu dịch vụ (desktop).")
    _img(rb, "member-polished-mobile.png",
         "App khách hàng — dashboard điểm và voucher (mobile).")
    _img(rb, "member-shops-real.png",
         "Danh sách cửa hàng đã tham gia của khách hàng.")
    _img(rb, "merchant-polished-desktop.png",
         "Dashboard merchant — tổng quan doanh thu và campaign.")
    _img(rb, "merchant-real-data.png",
         "Merchant — danh sách khách hàng và tier.")
    _img(rb, "staff-dashboard.png",
         "Staff shell — trang chủ POS.")
    _img(rb, "staff-pos-form.png",
         "Staff shell — form tích điểm sau khi quét QR.")
    _img(rb, "staff-pos-voucher-applied.png",
         "Staff shell — xác nhận áp dụng voucher cho hóa đơn.")
    _img(rb, "admin-polished-desktop.png",
         "Admin portal — dashboard toàn hệ thống.")
    _img(rb, "admin-tenants-fixed.png",
         "Admin portal — danh sách tenant và trạng thái duyệt.")
    _img(rb, "merchant-register-step1.png",
         "Luồng đăng ký merchant — bước 1 thông tin cơ bản.")
    _img(rb, "merchant-register-step2-with-contact.png",
         "Luồng đăng ký merchant — bước 2 thông tin liên hệ.")
    _img(rb, "merchant-register-step3.png",
         "Luồng đăng ký merchant — bước 3 pháp lý và hoàn tất.")
    _img(rb, "voucher-detail-page-new.png",
         "App khách — chi tiết voucher với mã QR quét tại quầy.")

    # ---------------- 3.4 ----------------
    rb.h2("3.4. Hệ thống báo biểu")
    rb.p(
        "Ngoài các trang nghiệp vụ, hệ thống cung cấp bốn dạng "
        "báo biểu chính để phục vụ quản trị và tuân thủ."
    )
    rb.h3("3.4.1. Dashboard analytics cho merchant")
    rb.p(
        "Trang /merchant hiển thị số liệu tổng hợp theo khoảng "
        "thời gian: doanh thu từ giao dịch, số lượng khách mới, "
        "số lượng voucher đã claim/đã dùng, top reward theo "
        "lượt đổi. Dữ liệu được lấy từ view v_campaign_stats và "
        "các truy vấn tổng hợp trên Transaction + PointLedger, "
        "có cache ở tầng TanStack Query để giảm round-trip."
    )

    rb.h3("3.4.2. Báo cáo hậu khuyến mại (NĐ 81 Điều 20)")
    rb.p(
        "Sau khi chiến dịch kết thúc, owner bấm \"Xuất báo cáo\" "
        "từ trang chi tiết; hệ thống render file PDF tổng hợp: "
        "số voucher phát hành, số đã dùng, giá trị quy đổi, danh "
        "sách khách hàng đã claim. File này có thể được dùng "
        "trực tiếp để nộp Sở Công Thương."
    )

    rb.h3("3.4.3. Audit log tenant settings")
    rb.p(
        "Mọi thay đổi cấu hình quan trọng của tenant (thông tin "
        "doanh nghiệp, tier, authorization, point rule) đều được "
        "ghi vào TenantSettingsAudit với actor, timestamp, "
        "before/after JSON. Super admin xem qua "
        "/admin/audit?tenant_id=…, giúp điều tra các sự cố hoặc "
        "tranh chấp."
    )

    rb.h3("3.4.4. Xuất CSV giao dịch")
    rb.p(
        "Trang /merchant/members/{id} cung cấp nút \"Xuất CSV\" "
        "để owner tải toàn bộ lịch sử giao dịch của một khách "
        "hàng cụ thể – hữu ích khi khách hàng khiếu nại về điểm. "
        "Endpoint trả file CSV encoding UTF-8 BOM để Excel mở "
        "đúng tiếng Việt."
    )
