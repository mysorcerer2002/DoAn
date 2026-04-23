"""Tài liệu tham khảo."""
from __future__ import annotations


def build(rb) -> None:
    rb.start_frontmatter("Tài liệu tham khảo")

    rb.p(
        "Danh sách tài liệu dưới đây được tham khảo trong quá "
        "trình thực hiện đề tài, bao gồm văn bản pháp lý, tài "
        "liệu kỹ thuật và các bài báo cáo kỹ thuật. Thứ tự "
        "đánh số dùng cho phần trích dẫn trong các chương."
    )

    items = [
        "Chính phủ nước Cộng hoà Xã hội Chủ nghĩa Việt Nam, "
        "Nghị định 81/2018/NĐ-CP ngày 22/05/2018 quy định chi "
        "tiết Luật Thương mại về hoạt động xúc tiến thương "
        "mại, Hà Nội, 2018.",

        "Quốc hội nước Cộng hoà Xã hội Chủ nghĩa Việt Nam, "
        "Luật Thương mại số 36/2005/QH11, Hà Nội, 2005.",

        "Quốc hội nước Cộng hoà Xã hội Chủ nghĩa Việt Nam, "
        "Luật Kế toán số 88/2015/QH13, Hà Nội, 2015.",

        "Quốc hội nước Cộng hoà Xã hội Chủ nghĩa Việt Nam, "
        "Luật Thuế Giá trị gia tăng số 13/2008/QH12 và các văn "
        "bản sửa đổi, Hà Nội.",

        "Sebastián Ramírez, \"FastAPI Documentation\", "
        "https://fastapi.tiangolo.com, truy cập 04/2026.",

        "SQLAlchemy Team, \"SQLAlchemy 2.0 Documentation\", "
        "https://docs.sqlalchemy.org/en/20/, truy cập 04/2026.",

        "PostgreSQL Global Development Group, \"PostgreSQL 15 "
        "Manual – Explicit Locking\", "
        "https://www.postgresql.org/docs/15/explicit-locking.html.",

        "Vercel Inc., \"Next.js 14 App Router Documentation\", "
        "https://nextjs.org/docs/app, truy cập 04/2026.",

        "TanStack, \"TanStack Query (React Query) Documentation\", "
        "https://tanstack.com/query/latest/docs, truy cập 04/2026.",

        "Serwist Team, \"Serwist – Progressive Web Apps "
        "toolkit\", https://serwist.pages.dev, truy cập 04/2026.",

        "Tailwind Labs, \"Tailwind CSS v4 Documentation\", "
        "https://tailwindcss.com/docs, truy cập 04/2026.",

        "shadcn, \"shadcn/ui — Beautifully designed "
        "components\", https://ui.shadcn.com, truy cập 04/2026.",

        "OWASP Foundation, \"OWASP Application Security "
        "Verification Standard v4.0\", "
        "https://owasp.org/www-project-application-security-verification-standard/.",

        "IETF, RFC 7519 – JSON Web Token (JWT), 2015, "
        "https://datatracker.ietf.org/doc/html/rfc7519.",

        "IETF, RFC 2104 – HMAC: Keyed-Hashing for Message "
        "Authentication, 1997, "
        "https://datatracker.ietf.org/doc/html/rfc2104.",

        "Cloudflare Inc., \"Cloudflare Tunnel Documentation\", "
        "https://developers.cloudflare.com/cloudflare-one/"
        "connections/connect-networks/.",

        "Docker Inc., \"Docker Compose Specification\", "
        "https://docs.docker.com/compose/.",

        "Alembic Project, \"Alembic – Database Migrations\", "
        "https://alembic.sqlalchemy.org, truy cập 04/2026.",
    ]
    for i, text in enumerate(items, start=1):
        rb.p(f"[{i}] {text}")
