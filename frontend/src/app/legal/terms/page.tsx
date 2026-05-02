import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Điều khoản dịch vụ | Loyalty Platform",
};

export default function TermsPage() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-12 text-slate-800">
      <h1 className="mb-1 text-3xl font-bold">Điều khoản dịch vụ</h1>
      <p className="mb-8 text-sm text-slate-500">Phiên bản v1.0 — Cập nhật: 02/05/2026</p>

      <section className="space-y-6 text-[15px] leading-relaxed">
        <div>
          <h2 className="mb-2 text-xl font-semibold">1. Phạm vi áp dụng</h2>
          <p>
            Điều khoản này áp dụng cho tất cả đối tác (cửa hàng) đăng ký và sử dụng
            nền tảng Loyalty Platform để triển khai chương trình tích điểm khách hàng.
            Bằng cách nhấn &quot;Đồng ý&quot; trong quá trình đăng ký, đối tác xác nhận
            đã đọc, hiểu và chấp thuận toàn bộ nội dung điều khoản này.
          </p>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold">2. Quyền và nghĩa vụ của đối tác</h2>
          <ul className="list-inside list-disc space-y-1 pl-2">
            <li>Cung cấp thông tin chính xác và đầy đủ khi đăng ký.</li>
            <li>Tuân thủ quy định về bảo mật tài khoản và không chia sẻ thông tin đăng nhập.</li>
            <li>Không sử dụng nền tảng cho các mục đích vi phạm pháp luật.</li>
            <li>Thông báo kịp thời cho Loyalty Platform khi phát hiện vi phạm hoặc sự cố.</li>
            <li>Chịu trách nhiệm về nội dung chương trình khuyến mại đăng tải trên nền tảng.</li>
          </ul>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold">3. Phí dịch vụ</h2>
          <p>
            Trong giai đoạn thử nghiệm (pilot), dịch vụ được cung cấp miễn phí.
            Bất kỳ thay đổi nào về chính sách phí sẽ được thông báo trước ít nhất
            30 ngày qua email đã đăng ký.
          </p>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold">4. Xử lý vi phạm</h2>
          <p>
            Loyalty Platform có quyền tạm ngưng hoặc chấm dứt tài khoản đối tác
            trong trường hợp vi phạm điều khoản, bao gồm nhưng không giới hạn:
            cung cấp thông tin giả mạo, lạm dụng hệ thống điểm thưởng, hoặc
            các hành vi gian lận ảnh hưởng đến khách hàng.
          </p>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold">5. Chấm dứt hợp đồng</h2>
          <p>
            Đối tác có thể yêu cầu chấm dứt tài khoản bất kỳ lúc nào bằng cách
            liên hệ bộ phận hỗ trợ. Dữ liệu khách hàng sẽ được lưu giữ theo
            quy định pháp luật hiện hành trong tối đa 2 năm sau khi chấm dứt.
          </p>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold">6. Liên hệ</h2>
          <p>
            Mọi thắc mắc về điều khoản dịch vụ, vui lòng liên hệ:{" "}
            <a href="mailto:support@loyalty.ecom-bill.com" className="text-indigo-600 underline">
              support@loyalty.ecom-bill.com
            </a>
          </p>
        </div>
      </section>
    </main>
  );
}
