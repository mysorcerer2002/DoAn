"""Lời cảm ơn — 1 trang."""
from __future__ import annotations


def build(rb) -> None:
    rb.start_frontmatter("LỜI CẢM ƠN")

    rb.p(
        "Trong suốt quá trình học tập và thực hiện đồ án thực tập tốt nghiệp tại "
        "Khoa Công nghệ Thông tin – Trường Đại học Công nghệ Sài Gòn, "
        "em đã nhận được rất nhiều sự giúp đỡ quý báu từ quý thầy cô, "
        "gia đình và bạn bè. Nhân đây, em xin gửi lời cảm ơn chân thành "
        "đến tất cả những người đã đồng hành và tạo điều kiện để em hoàn thành "
        "đề tài này."
    )
    rb.p(
        "Trước tiên, em xin gửi lời cảm ơn sâu sắc đến Ban Giám hiệu Nhà trường, "
        "Ban chủ nhiệm Khoa Công nghệ Thông tin cùng toàn thể quý thầy cô đã "
        "tận tình truyền đạt kiến thức chuyên môn và kỹ năng nghề nghiệp trong "
        "suốt bốn năm học vừa qua. Những nền tảng lý thuyết và thực hành "
        "mà nhà trường cung cấp là hành trang không thể thiếu để em tiếp cận "
        "và giải quyết bài toán kỹ thuật thực tế trong đề tài này."
    )
    rb.p(
        "Đặc biệt, em xin bày tỏ lòng biết ơn sâu sắc đến Thầy/Cô "
        "[ĐIỀN GVHD] — giảng viên hướng dẫn đề tài — đã dành nhiều thời gian "
        "quý báu để định hướng chủ đề, góp ý chi tiết về kiến trúc hệ thống, "
        "phương pháp nghiên cứu và cách trình bày báo cáo. Những nhận xét cụ thể "
        "và thẳng thắn của Thầy/Cô đã giúp em không chỉ nâng cao chất lượng sản "
        "phẩm mà còn trưởng thành hơn trong tư duy kỹ thuật và phong cách "
        "làm việc có kỷ luật."
    )
    rb.p(
        "Em cũng xin gửi lời cảm ơn đến gia đình, người thân và bạn bè "
        "đã luôn ở bên, động viên và chia sẻ khó khăn trong suốt quá trình "
        "thực hiện đề tài. Sự ủng hộ tinh thần đó là nguồn động lực quan trọng "
        "giúp em vượt qua những thời điểm áp lực nhất trong quá trình nghiên cứu "
        "và phát triển hệ thống."
    )
    rb.p(
        "Do giới hạn về thời gian và kinh nghiệm thực tế, báo cáo chắc chắn "
        "còn nhiều thiếu sót. Em rất mong nhận được ý kiến đóng góp quý báu "
        "từ quý thầy cô và Hội đồng phản biện để đề tài ngày càng hoàn thiện "
        "hơn. Em xin cam đoan nội dung báo cáo này là kết quả nghiên cứu "
        "trung thực của bản thân, không sao chép từ bất kỳ công trình nào "
        "mà không có trích dẫn rõ ràng."
    )
    rb.blank()
    p = rb.doc.add_paragraph("TP. Hồ Chí Minh, tháng 04 năm 2026\n\nSinh viên thực hiện\n\n\n\nNguyễn Hải Đăng")
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    from docx.shared import Pt
    for r in p.runs:
        r.font.name = "Times New Roman"
        r.font.size = Pt(13)
        r.font.italic = True
