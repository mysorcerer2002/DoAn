"""Phụ lục — Hướng dẫn sử dụng luồng Đăng ký → Đổi quà từ đối tác."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # D:/DoAn


def _img(rb, filename: str, caption: str, width_cm: float = 13.0) -> None:
    path = ROOT / filename
    rb.figure(str(path), caption, width_cm=width_cm)


def build(rb) -> None:
    rb.start_frontmatter("PHỤ LỤC: HƯỚNG DẪN SỬ DỤNG — LUỒNG ĐĂNG KÝ ĐẾN ĐỔI QUÀ")

    rb.p(
        "Phụ lục này hướng dẫn từng bước cho một khách hàng mới sử dụng hệ "
        "thống từ lúc đăng ký tài khoản đến lúc đổi quà thành công tại cửa hàng "
        "đối tác. Luồng này được thực hiện trên thiết bị di động (điện thoại "
        "thông minh) với trình duyệt bất kỳ, không cần cài ứng dụng. "
        "URL sản phẩm: loyalty.ecom-bill.com."
    )

    # ── Bước 1 ──────────────────────────────────
    rb.h3("Bước 1. Đăng ký tài khoản khách hàng")
    rb.p(
        "Khách hàng mở trình duyệt và truy cập https://loyalty.ecom-bill.com/register. "
        "Trang đăng ký yêu cầu nhập họ tên đầy đủ, địa chỉ email (hoặc số điện "
        "thoại), và mật khẩu tối thiểu 8 ký tự. Sau khi điền đầy đủ thông tin "
        "và bấm nút Đăng ký, hệ thống tạo tài khoản ngay lập tức và tự động "
        "đăng nhập vào ứng dụng. Không cần xác thực email."
    )
    _img(rb, "bao-cao/assets/screenshots/buoc-1-register.png",
         "Bước 1: Form đăng ký tài khoản khách hàng tại /register.")

    # ── Bước 2 ──────────────────────────────────
    rb.h3("Bước 2. Đăng nhập vào ứng dụng")
    rb.p(
        "Nếu đã có tài khoản từ trước, khách hàng truy cập "
        "https://loyalty.ecom-bill.com/login, nhập email và mật khẩu rồi bấm "
        "Đăng nhập. Sau khi xác thực thành công, ứng dụng chuyển hướng về "
        "trang chủ thành viên tại /member. JWT được lưu vào localStorage và "
        "tự động đính kèm vào mọi request tiếp theo. Nếu quên mật khẩu, "
        "bấm vào đường dẫn 'Quên mật khẩu?' và nhập email để nhận mật khẩu "
        "tạm thời qua email."
    )
    _img(rb, "bao-cao/assets/screenshots/buoc-2-login.png",
         "Bước 2: Trang đăng nhập tại /login.")

    # ── Bước 3 ──────────────────────────────────
    rb.h3("Bước 3. Xem số điểm và QR cá nhân")
    rb.p(
        "Trang chủ /member hiển thị tổng số điểm hiện tại của khách hàng cùng "
        "lịch sử biến động điểm gần đây. Khách hàng tích điểm tại bất kỳ đối "
        "tác nào trên nền tảng, số điểm đều được cộng vào cùng một ví điểm "
        "toàn cục này. Ở đáy màn hình có BottomNavBar với bốn tab: Trang chủ, "
        "Đối tác, Voucher và QR. Bấm vào tab QR để mở trang /member/qr hiển "
        "thị mã QR cá nhân — đây là 'thẻ thành viên' dùng để tích điểm tại quầy."
    )
    _img(rb, "bao-cao/assets/screenshots/buoc-3-member-home.png",
         "Bước 3: Trang chủ thành viên tại /member — hiển thị số điểm tổng.")

    # ── Bước 4 ──────────────────────────────────
    rb.h3("Bước 4. Khám phá danh sách đối tác")
    rb.p(
        "Khách hàng bấm tab Đối tác trên BottomNavBar để vào trang /member/partners. "
        "Trang hiển thị danh sách tất cả các đối tác đang active trên nền tảng "
        "với logo, tên, danh mục (cafe, food, retail, beauty) và mô tả ngắn. "
        "Khách hàng có thể cuộn danh sách và bấm vào một đối tác yêu thích "
        "để xem chi tiết. Ví dụ: bấm vào Cafe Cộng hoặc Lala Food."
    )
    _img(rb, "bao-cao/assets/screenshots/buoc-4-partner-list.png",
         "Bước 4: Danh sách đối tác đang hoạt động trên nền tảng tại /member/partners.")

    # ── Bước 5 ──────────────────────────────────
    rb.h3("Bước 5. Xem chi tiết đối tác và danh sách quà")
    rb.p(
        "Trang chi tiết đối tác tại /member/partners/{slug} hiển thị thông tin "
        "đầy đủ của cửa hàng: logo, banner, mô tả, địa chỉ và giờ hoạt động. "
        "Phía dưới là danh sách các phần thưởng có thể đổi tại đối tác này, "
        "sắp xếp theo điểm cần thiết từ thấp đến cao. Mỗi quà hiển thị: tên, "
        "mô tả, điểm cần đổi, loại ưu đãi (giảm phần trăm / giảm số tiền cố "
        "định / tặng món) và nút Đổi quà. Nếu số điểm hiện tại không đủ, "
        "nút Đổi quà bị vô hiệu hóa kèm tooltip giải thích."
    )
    _img(rb, "bao-cao/assets/screenshots/buoc-5-partner-detail.png",
         "Bước 5: Trang chi tiết đối tác — danh sách quà và điểm cần đổi.")

    # ── Bước 6 ──────────────────────────────────
    rb.h3("Bước 6. Đổi quà — xác nhận giao dịch")
    rb.p(
        "Khách hàng bấm nút Đổi quà trên một phần thưởng bất kỳ. Hệ thống hiện "
        "dialog xác nhận với đầy đủ thông tin: tên quà, điểm cần dùng, số điểm "
        "hiện tại và số điểm còn lại sau khi đổi. Khách hàng đọc kỹ thông tin "
        "và bấm Xác nhận để tiếp tục. Backend xử lý ngay: kiểm tra số dư điểm, "
        "trừ điểm, tạo redemption với mã 8 ký tự ngẫu nhiên và ghi vào sổ cái. "
        "Nếu điểm không đủ, hệ thống hiển thị thông báo lỗi rõ ràng."
    )
    _img(rb, "bao-cao/assets/screenshots/buoc-6-redeem-confirm.png",
         "Bước 6: Dialog xác nhận đổi quà — hiển thị điểm cần dùng và số dư sau đổi.")

    # ── Bước 7 ──────────────────────────────────
    rb.h3("Bước 7. Voucher xuất hiện trong ví")
    rb.p(
        "Sau khi đổi thành công, khách hàng được điều hướng về trang "
        "/member/vouchers — ví voucher. Redemption vừa tạo xuất hiện ở đầu "
        "danh sách với trạng thái PENDING (màu xanh). Mỗi voucher hiển thị: "
        "tên quà, tên đối tác, mã 8 ký tự, ngày hết hạn và trạng thái. "
        "Khách hàng bấm vào voucher để xem chi tiết và mã QR của voucher "
        "tại trang /member/vouchers/{id}."
    )
    _img(rb, "bao-cao/assets/screenshots/buoc-7-voucher-list.png",
         "Bước 7: Ví voucher tại /member/vouchers — redemption vừa đổi xuất hiện với status PENDING.")

    # ── Bước 8 ──────────────────────────────────
    rb.h3("Bước 8. Khách hàng đến cửa hàng và mở QR cá nhân")
    rb.p(
        "Khi đến cửa hàng đối tác, khách hàng mở app và bấm tab QR trên "
        "BottomNavBar để vào trang /member/qr. Trang này hiển thị mã QR cá nhân "
        "kích thước lớn, không có header/footer để tối đa diện tích hiển thị "
        "(BottomNavBar tự động ẩn trên trang /member/qr). Đây là mã QR nhân viên "
        "POS sẽ scan để xác nhận danh tính khách hàng khi tích điểm. Nếu muốn "
        "dùng voucher đã đổi, khách hàng mở trang /member/vouchers và đưa màn "
        "hình cho nhân viên xem mã 8 ký tự."
    )
    _img(rb, "bao-cao/assets/screenshots/buoc-8-member-qr.png",
         "Bước 8: Trang QR cá nhân tại /member/qr — mã QR hiển thị full-screen cho POS scan.")

    # ── Bước 9 ──────────────────────────────────
    rb.h3("Bước 9. Nhân viên POS scan QR và verify voucher")
    rb.p(
        "Nhân viên POS đăng nhập vào giao diện staff tại /staff. Để tích điểm "
        "cho khách: bấm tab Tích điểm, scan QR của khách hoặc nhập mã hóa đơn, "
        "nhập số tiền thanh toán và bấm Xác nhận. Hệ thống tính điểm và cộng "
        "vào ví của khách ngay lập tức. Để xác nhận voucher khi khách dùng quà: "
        "bấm tab Verify, nhập mã 8 ký tự từ voucher của khách, kiểm tra thông "
        "tin quà hiển thị và bấm Xác nhận đã giao. Redemption chuyển sang "
        "trạng thái USED, khách hàng nhận quà và giao dịch hoàn tất."
    )
    _img(rb, "bao-cao/assets/screenshots/buoc-9-staff-verify.png",
         "Bước 9: Giao diện POS staff tại /staff/verify — nhập mã redemption và xác nhận giao quà.")
