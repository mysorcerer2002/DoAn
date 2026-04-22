"""Định dạng STU 2025 — constants + style setup.

Ref: MAU_ThucTap_2025.docx (Khoa CNTT ĐH Công nghệ Sài Gòn).
- Times New Roman 13pt, line 1.3, paragraph spacing after 6pt
- H1 (Chương): 24pt IN HOA bold, canh phải, trang đầu không header
- H2 (1.1):    15pt IN HOA bold
- H3 (1.1.1): 14pt thường bold
- H4 (1.1.1.1): 13pt thường gạch dưới
- TOC title: 18pt IN HOA bold, canh giữa
- Header: "CHƯƠNG X: TÊN" IN HOA italic (khác nhau mỗi chương)
- Footer: "Đề tài: <TÊN ĐỀ TÀI>" IN HOA italic + số trang canh phải
"""
from __future__ import annotations

from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Cm, Pt, RGBColor

# === Constants ===
FONT_NAME = "Times New Roman"
BODY_SIZE = Pt(13)
LINE_SPACING = 1.3
PARA_SPACING_AFTER = Pt(6)

H1_SIZE = Pt(24)
H2_SIZE = Pt(15)
H3_SIZE = Pt(14)
H4_SIZE = Pt(13)
TOC_TITLE_SIZE = Pt(18)
HEADER_FOOTER_SIZE = Pt(11)

# Margins A4 — mặc định Word
MARGIN_TOP = Cm(2.0)
MARGIN_BOTTOM = Cm(2.0)
MARGIN_LEFT = Cm(3.0)
MARGIN_RIGHT = Cm(2.0)

# Màu bìa ĐH = XANH DƯƠNG (RGB tương đương #1F3A8A — phù hợp in giấy cứng)
COVER_BLUE = RGBColor(0x1F, 0x3A, 0x8A)


def _set_run_font(run, size=None, bold=None, italic=None, underline=None, color=None):
    """Áp Times New Roman (kể cả east-asia) + các thuộc tính."""
    run.font.name = FONT_NAME
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.insert(0, rFonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rFonts.set(qn(attr), FONT_NAME)
    if size is not None:
        run.font.size = size
    if bold is not None:
        run.font.bold = bold
    if italic is not None:
        run.font.italic = italic
    if underline is not None:
        run.font.underline = underline
    if color is not None:
        run.font.color.rgb = color


def _set_paragraph_spacing(para, line=LINE_SPACING, after=PARA_SPACING_AFTER, before=None):
    pf = para.paragraph_format
    pf.line_spacing = line
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.space_after = after
    if before is not None:
        pf.space_before = before


def apply_document_defaults(doc):
    """Set font default toàn document + margins A4."""
    styles = doc.styles
    # Normal style
    normal = styles["Normal"]
    normal.font.name = FONT_NAME
    normal.font.size = BODY_SIZE
    # rFonts cho Normal
    rpr = normal.element.get_or_add_rPr()
    rFonts = rpr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rpr.insert(0, rFonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rFonts.set(qn(attr), FONT_NAME)

    # Paragraph format default
    pf = normal.paragraph_format
    pf.line_spacing = LINE_SPACING
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.space_after = PARA_SPACING_AFTER

    # Margins
    for section in doc.sections:
        section.top_margin = MARGIN_TOP
        section.bottom_margin = MARGIN_BOTTOM
        section.left_margin = MARGIN_LEFT
        section.right_margin = MARGIN_RIGHT


def style_heading_1(para):
    """Chương X — 24pt, IN HOA, bold, canh phải."""
    para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    _set_paragraph_spacing(para, before=Pt(12), after=Pt(18))
    for run in para.runs:
        _set_run_font(run, size=H1_SIZE, bold=True)


def style_heading_2(para):
    """1.1 — 15pt, IN HOA, bold."""
    para.alignment = WD_ALIGN_PARAGRAPH.LEFT
    _set_paragraph_spacing(para, before=Pt(12), after=Pt(6))
    for run in para.runs:
        _set_run_font(run, size=H2_SIZE, bold=True)


def style_heading_3(para):
    """1.1.1 — 14pt, thường, bold."""
    para.alignment = WD_ALIGN_PARAGRAPH.LEFT
    _set_paragraph_spacing(para, before=Pt(8), after=Pt(4))
    for run in para.runs:
        _set_run_font(run, size=H3_SIZE, bold=True)


def style_heading_4(para):
    """1.1.1.1 — 13pt, thường, gạch dưới."""
    para.alignment = WD_ALIGN_PARAGRAPH.LEFT
    _set_paragraph_spacing(para, before=Pt(6), after=Pt(2))
    for run in para.runs:
        _set_run_font(run, size=H4_SIZE, underline=True)


def style_body(para):
    """Body text — 13pt, line 1.3, first-line indent 0.5cm."""
    para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    _set_paragraph_spacing(para)
    para.paragraph_format.first_line_indent = Cm(0.5)
    for run in para.runs:
        _set_run_font(run, size=BODY_SIZE)


def style_caption(para):
    """Caption hình/bảng — canh giữa, bold italic phần số, underline."""
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _set_paragraph_spacing(para, before=Pt(4), after=Pt(8))
    for run in para.runs:
        _set_run_font(run, size=Pt(12), italic=True, underline=True, bold=True)


def style_toc_title(para):
    """MỤC LỤC — 18pt IN HOA bold canh giữa."""
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _set_paragraph_spacing(para, before=Pt(0), after=Pt(18))
    for run in para.runs:
        _set_run_font(run, size=TOC_TITLE_SIZE, bold=True)


def set_page_border_blue(section):
    """Viền xanh dương cho trang bìa. Word Page Border XML."""
    sectPr = section._sectPr
    existing = sectPr.find(qn("w:pgBorders"))
    if existing is not None:
        sectPr.remove(existing)
    pgBorders = OxmlElement("w:pgBorders")
    pgBorders.set(qn("w:offsetFrom"), "page")
    for edge in ("top", "left", "bottom", "right"):
        b = OxmlElement(f"w:{edge}")
        b.set(qn("w:val"), "single")
        b.set(qn("w:sz"), "24")  # 3pt
        b.set(qn("w:space"), "24")
        b.set(qn("w:color"), "1F3A8A")
        pgBorders.append(b)
    sectPr.append(pgBorders)


def add_page_number_field(paragraph):
    """Chèn field PAGE vào paragraph hiện tại."""
    run = paragraph.add_run()
    fldChar_begin = OxmlElement("w:fldChar")
    fldChar_begin.set(qn("w:fldCharType"), "begin")
    instrText = OxmlElement("w:instrText")
    instrText.set(qn("xml:space"), "preserve")
    instrText.text = "PAGE"
    fldChar_end = OxmlElement("w:fldChar")
    fldChar_end.set(qn("w:fldCharType"), "end")
    run._element.append(fldChar_begin)
    run._element.append(instrText)
    run._element.append(fldChar_end)
    _set_run_font(run, size=HEADER_FOOTER_SIZE, italic=True)


def add_toc_field(paragraph, switches='\\o "1-3" \\h \\z \\u'):
    """Chèn field TOC — Word sẽ tự tạo mục lục khi update field (F9)."""
    run = paragraph.add_run()
    fldChar_begin = OxmlElement("w:fldChar")
    fldChar_begin.set(qn("w:fldCharType"), "begin")
    instrText = OxmlElement("w:instrText")
    instrText.set(qn("xml:space"), "preserve")
    instrText.text = f' TOC {switches} '
    fldChar_sep = OxmlElement("w:fldChar")
    fldChar_sep.set(qn("w:fldCharType"), "separate")
    placeholder = OxmlElement("w:t")
    placeholder.text = "Nhấn F9 trong Word để cập nhật mục lục."
    fldChar_end = OxmlElement("w:fldChar")
    fldChar_end.set(qn("w:fldCharType"), "end")
    run._element.append(fldChar_begin)
    run._element.append(instrText)
    run._element.append(fldChar_sep)
    run._element.append(placeholder)
    run._element.append(fldChar_end)
    _set_run_font(run, size=BODY_SIZE)


def set_header_different_first_page(section):
    """Trang đầu mỗi section KHÔNG có header (quy định STU: trang đầu chương không header)."""
    section.different_first_page_header_footer = True
    sectPr = section._sectPr
    titlePg = sectPr.find(qn("w:titlePg"))
    if titlePg is None:
        titlePg = OxmlElement("w:titlePg")
        sectPr.append(titlePg)


def add_section_break(doc, page_break=True):
    """Thêm section break bắt đầu trang mới."""
    from docx.enum.section import WD_SECTION
    return doc.add_section(WD_SECTION.NEW_PAGE if page_break else WD_SECTION.CONTINUOUS)
