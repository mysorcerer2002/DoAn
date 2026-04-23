"""Lời cảm ơn — 1 trang."""
from __future__ import annotations


def build(rb) -> None:
    rb.start_frontmatter("Lời cảm ơn")

    rb.p(
        "Trong suốt quá trình học tập và thực hiện đồ án tốt nghiệp tại "
        "Khoa Công nghệ Thông tin – Trường Đại học Công nghệ Sài Gòn, "
        "em đã nhận được rất nhiều sự giúp đỡ quý báu từ các thầy cô, "
        "gia đình và bạn bè."
    )
    rb.p(
        "Trước tiên, em xin gửi lời cảm ơn chân thành và sâu sắc nhất "
        "đến Ban Giám hiệu Nhà trường, Ban chủ nhiệm Khoa Công nghệ "
        "Thông tin cùng toàn thể quý thầy cô đã tận tình truyền đạt "
        "kiến thức chuyên môn, kỹ năng nghề nghiệp và tạo mọi điều "
        "kiện thuận lợi để em hoàn thành chương trình đại học."
    )
    rb.p(
        "Đặc biệt, em xin bày tỏ lòng biết ơn sâu sắc đến Thầy/Cô hướng "
        "dẫn đã dành thời gian quý báu, trực tiếp định hướng đề tài, "
        "góp ý, sửa chữa và hướng dẫn em trong suốt quá trình thực "
        "hiện đồ án. Những lời khuyên và nhận xét chi tiết của Thầy/Cô "
        "đã giúp em không chỉ hoàn thiện sản phẩm mà còn trưởng thành "
        "hơn trong tư duy kỹ thuật và phong cách làm việc chuyên nghiệp."
    )
    rb.p(
        "Em cũng xin gửi lời cảm ơn đến các doanh nghiệp SME đã đồng "
        "ý trao đổi về quy trình vận hành chương trình khách hàng thân "
        "thiết thực tế. Những chia sẻ về bài toán nghiệp vụ, vướng mắc "
        "pháp lý và mong muốn của chủ cửa hàng đã giúp đề tài mang "
        "tính ứng dụng cao thay vì chỉ dừng lại ở thử nghiệm học thuật."
    )
    rb.p(
        "Cuối cùng, em xin cảm ơn gia đình, người thân và bạn bè đã "
        "luôn ở bên, động viên và đồng hành trong suốt quá trình học "
        "tập và thực hiện đồ án."
    )
    rb.p(
        "Do giới hạn về thời gian và kinh nghiệm, báo cáo chắc chắn "
        "không tránh khỏi thiếu sót. Em rất mong nhận được những ý "
        "kiến đóng góp của quý thầy cô và Hội đồng để đề tài ngày càng "
        "hoàn thiện hơn."
    )
    rb.blank()
    p = rb.doc.add_paragraph("Em xin chân thành cảm ơn!")
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    from docx.shared import Pt
    for r in p.runs:
        r.font.name = "Times New Roman"
        r.font.size = Pt(13)
        r.font.italic = True
