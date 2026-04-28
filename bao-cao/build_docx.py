"""Orchestrator — build bao-cao-final.docx từ content modules.

Usage:
    python build_docx.py           # build full (khi content đủ)
    python build_docx.py --smoke   # smoke test bìa + 1 chương mẫu để xem format
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Bảo đảm import relative hoạt động khi chạy từ thư mục bao-cao/
sys.path.insert(0, str(Path(__file__).parent))

from builder import ReportBuilder

TITLE = "XÂY DỰNG WEBSITE TÍCH ĐIỂM THÀNH VIÊN CHO DOANH NGHIỆP VỪA VÀ NHỎ"
SV_PLACEHOLDER = "Nguyễn Hải Đăng"
MSSV_PLACEHOLDER = "[MSSV]"
GVHD_PLACEHOLDER = "[HỌ TÊN GVHD]"
YEAR_PLACEHOLDER = "2025-2026"

OUTPUT = Path(__file__).parent / "bao-cao-mvp.docx"


def build_smoke() -> None:
    """Smoke: bìa + mục lục + mục lục hình + Chương 1 demo với H1/H2/H3/H4, bảng, list."""
    rb = ReportBuilder(title=TITLE)
    rb.add_cover(sv=SV_PLACEHOLDER, mssv=MSSV_PLACEHOLDER,
                 gvhd=GVHD_PLACEHOLDER, year=YEAR_PLACEHOLDER)

    # Lời cảm ơn (demo 1 trang)
    rb.doc.add_section_break = None  # no-op
    # Dùng TOC section
    rb.add_toc()
    rb.add_list_of_figures()

    # Chương 1 demo
    rb.start_chapter("Chương 1", "Giới thiệu")
    rb.h2("1.1. Đặt vấn đề, mục tiêu luận văn")
    rb.p("Trong bối cảnh các doanh nghiệp vừa và nhỏ (SME) tại Việt Nam — đặc "
         "biệt là các chuỗi cà phê, nhà hàng, cửa hàng bán lẻ — việc xây dựng "
         "chương trình khách hàng thân thiết thường gặp nhiều khó khăn về "
         "chi phí phát triển và tuân thủ pháp lý khuyến mại. Luận văn này "
         "đề xuất một hệ thống multi-tenant cho phép nhiều doanh nghiệp "
         "chia sẻ chung hạ tầng tích điểm, đồng thời hỗ trợ công ty vận hành "
         "thay mặt SME nộp hồ sơ khuyến mại theo Nghị định 81/2018/NĐ-CP.")

    rb.h3("1.1.1. Bối cảnh thị trường")
    rb.p("Các nền tảng tương tự hiện có (Got It, Urbox, Loyverse) hoặc "
         "không hỗ trợ pháp lý Việt Nam, hoặc yêu cầu chi phí đầu tư lớn "
         "không phù hợp với quy mô SME.")

    rb.h4("1.1.1.1. Đối tượng phục vụ")
    rb.p("Đối tượng chính gồm chuỗi cà phê 2-10 chi nhánh, nhà hàng nhỏ, "
         "shop thời trang và làm đẹp có tần suất giao dịch lặp lại cao.")

    rb.h2("1.4. Kết quả cần đạt")
    rb.p("Bảng dưới tóm tắt các mục tiêu đo lường được của đề tài:")
    rb.table(
        headers=["STT", "Mục tiêu", "Tiêu chí đo"],
        rows=[
            ["1", "Hệ thống multi-tenant hoạt động ổn định", "≥ 5 tenant demo + pytest pass"],
            ["2", "Tuân thủ NĐ 81/2018/NĐ-CP", "4 tier approval_tier có unit test"],
            ["3", "Chống TOCTOU voucher claim", "Concurrent test 50 req không over-issuance"],
            ["4", "PWA offline-ready", "Lighthouse PWA score ≥ 80"],
            ["5", "CI/CD tự động", "Docker Compose dev+prod chạy clean"],
        ],
        caption="Bảng mục tiêu cần đạt."
    )

    rb.save(OUTPUT)
    print(f"[OK] Smoke build: {OUTPUT}")


def build_full() -> None:
    """Full build — sẽ gọi content.chuong_1.build(rb), chuong_2.build(rb), …"""
    rb = ReportBuilder(title=TITLE)
    rb.add_cover(sv=SV_PLACEHOLDER, mssv=MSSV_PLACEHOLDER,
                 gvhd=GVHD_PLACEHOLDER, year=YEAR_PLACEHOLDER)
    rb.add_toc()
    rb.add_list_of_figures()

    # Import từng chương — các module này sẽ được viết ở các bước tiếp theo
    try:
        from content import loi_cam_on, chuong_1, chuong_2, chuong_3, chuong_4, chuong_5, phu_luc, tltk
        loi_cam_on.build(rb)
        chuong_1.build(rb)
        chuong_2.build(rb)
        chuong_3.build(rb)
        chuong_4.build(rb)
        chuong_5.build(rb)
        phu_luc.build(rb)
        tltk.build(rb)
    except ImportError as e:
        print(f"[WARN] Chưa đủ content modules: {e}. Fallback smoke.")
        build_smoke()
        return

    rb.save(OUTPUT)
    print(f"[OK] Full build: {OUTPUT}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true", help="Smoke test với 1 chương demo")
    args = parser.parse_args()
    if args.smoke:
        build_smoke()
    else:
        build_full()


if __name__ == "__main__":
    main()
