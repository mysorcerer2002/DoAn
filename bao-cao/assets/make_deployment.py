"""Vẽ sơ đồ kiến trúc triển khai (deployment architecture).

Element bắt buộc theo phản biện:
- Người dùng (desktop + mobile riêng).
- Cloudflare Edge (TLS termination, DDoS/WAF, X-Forwarded-For inject)
  TÁCH BIỆT khỏi cloudflared daemon.
- cloudflared daemon (remotely-managed, trong Docker host).
- 4 subdomain routing (member/merchant/admin/pos).
- Docker network boundary (loyalty-net).
- 3 container: frontend (Next.js SSR + reverse proxy /api/*),
  backend (FastAPI), postgres.
- Volume pg_data với annotation persistent.
- SMTP server external (Gmail SMTP) — optional path quên mật khẩu.
- Annotations: TLS termination, X-Forwarded-For inject.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = Path(__file__).parent / "uml"
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.family"] = "DejaVu Sans"


def _box(ax, x, y, w, h, title, lines, fill="#EFF6FF", edge="#1E3A8A",
         title_color="#1E3A8A", title_size=10.0, body_size=8.0,
         line_h=0.28):
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.08",
        linewidth=1.3, edgecolor=edge, facecolor=fill,
    )
    ax.add_patch(box)
    ax.text(x + w / 2, y + h - 0.28, title,
            ha="center", va="center", fontsize=title_size,
            fontweight="bold", color=title_color)
    for i, line in enumerate(lines):
        ax.text(x + 0.10, y + h - 0.62 - i * line_h, line,
                ha="left", va="center", fontsize=body_size,
                color="#111827")


def _wrap(ax, x, y, w, h, label, label_pos="top",
          edge="#374151", fill="#F3F4F6",
          dash=False):
    style = "round,pad=0.02,rounding_size=0.08"
    box = FancyBboxPatch(
        (x, y), w, h, boxstyle=style,
        linewidth=1.3, edgecolor=edge, facecolor=fill,
        linestyle="--" if dash else "-",
    )
    ax.add_patch(box)
    if label_pos == "top":
        ax.text(x + w / 2, y + h - 0.22, label,
                ha="center", va="center", fontsize=10.5,
                fontweight="bold", color=edge)
    else:
        ax.text(x + 0.15, y + 0.22, label,
                ha="left", va="center", fontsize=9.0,
                fontweight="bold", color=edge, style="italic")


def _arrow(ax, p1, p2, label="", color="#1F2937", style="-|>", rad=0.0,
           label_offset=(0, 0), label_size=7.5, dashed=False):
    arrow = FancyArrowPatch(
        p1, p2, arrowstyle=style, mutation_scale=14,
        linewidth=1.1, color=color,
        connectionstyle=f"arc3,rad={rad}",
        linestyle="--" if dashed else "-",
    )
    ax.add_patch(arrow)
    if label:
        mx = (p1[0] + p2[0]) / 2 + label_offset[0]
        my = (p1[1] + p2[1]) / 2 + label_offset[1]
        ax.text(mx, my, label, ha="center", va="center",
                fontsize=label_size, color=color,
                bbox=dict(facecolor="white", edgecolor="none",
                          pad=1.4, alpha=0.92))


def render():
    fig, ax = plt.subplots(figsize=(17, 10))
    ax.set_xlim(0, 17)
    ax.set_ylim(0, 10)
    ax.axis("off")

    # ── Title ──
    ax.text(8.5, 9.55, "Sơ đồ kiến trúc triển khai (Deployment)",
            ha="center", va="center", fontsize=15, fontweight="bold",
            color="#1E3A8A")
    ax.text(8.5, 9.18,
            "Stack production: Người dùng → Cloudflare Edge → "
            "cloudflared → Docker network → 3 container nghiệp vụ",
            ha="center", va="center", fontsize=9.5, style="italic",
            color="#374151")

    # ── 1. Người dùng (desktop + mobile) ──
    _wrap(ax, 0.2, 4.6, 2.4, 3.4, "Người dùng",
          edge="#92400E", fill="#FEF3C7")
    _box(ax, 0.4, 6.4, 2.0, 1.4, "Browser desktop",
         ["• Chrome / Edge / FF",
          "• Owner / Admin",
          "• Member portal"],
         fill="#FFFBEB", edge="#B45309", title_color="#B45309",
         title_size=9.0, body_size=7.5, line_h=0.26)
    _box(ax, 0.4, 4.8, 2.0, 1.4, "Browser mobile",
         ["• Chrome Android",
          "• Safari iOS",
          "• Member + Staff POS"],
         fill="#FFFBEB", edge="#B45309", title_color="#B45309",
         title_size=9.0, body_size=7.5, line_h=0.26)

    # ── 2. Cloudflare Edge (cloud) ──
    _box(ax, 3.1, 4.8, 3.2, 3.0, "Cloudflare Edge (cloud)",
         ["• TLS termination",
          "• DDoS / WAF",
          "• Inject X-Forwarded-For",
          "• Routing 4 subdomain:",
          "  member.ecom-bill.com",
          "  merchant.ecom-bill.com",
          "  admin.ecom-bill.com",
          "  pos.ecom-bill.com"],
         fill="#FFEDD5", edge="#C2410C", title_color="#C2410C",
         title_size=10.0, body_size=7.8, line_h=0.30)

    # ── 3. Docker host (large wrapper) ──
    _wrap(ax, 6.8, 0.4, 8.0, 7.6,
          "Docker host (loyalty-prod compose)",
          edge="#374151", fill="#F9FAFB")

    # 3a. cloudflared (in host but outside docker network)
    _box(ax, 7.05, 5.6, 3.0, 1.9, "loyalty-cloudflared",
         ["• cloudflared daemon",
          "• Remotely-managed",
          "  (config tại Cloudflare Edge)",
          "• Egress-only outbound",
          "• Forward 4 hostname → frontend"],
         fill="#FFF7ED", edge="#C2410C", title_color="#C2410C",
         title_size=9.5, body_size=7.6, line_h=0.27)

    # 3b. Docker network boundary (dashed) — chứa frontend/backend/postgres
    _wrap(ax, 10.3, 0.7, 4.4, 6.95,
          "Docker network: loyalty-net",
          edge="#1E3A8A", fill="#EFF6FF", label_pos="bot",
          dash=True)

    # 3c. Frontend
    _box(ax, 10.5, 5.5, 4.0, 2.0, "loyalty-frontend-prod",
         ["• Next.js 14 (App Router)",
          "• SSR — output: standalone",
          "• Reverse proxy /api/* →",
          "  http://backend:8000",
          "• Port 3000 (internal)"],
         fill="#DBEAFE", edge="#1E3A8A", title_size=9.5,
         body_size=7.6, line_h=0.27)

    # 3d. Backend
    _box(ax, 10.5, 3.0, 4.0, 2.3, "loyalty-backend-prod",
         ["• FastAPI + uvicorn (async)",
          "• Alembic auto-migrate (start)",
          "• APScheduler (jobs)",
          "• slowapi rate limit",
          "  key=X-Forwarded-For",
          "• Port 8000 (internal)"],
         fill="#DBEAFE", edge="#1E3A8A", title_size=9.5,
         body_size=7.6, line_h=0.27)

    # 3e. Postgres
    _box(ax, 10.5, 0.85, 4.0, 1.95, "loyalty-postgres-prod",
         ["• PostgreSQL 15",
          "• CHECK + trigger constraints",
          "• Port 5432 (internal-only)",
          "• Volume pg_data attached"],
         fill="#DCFCE7", edge="#15803D", title_color="#15803D",
         title_size=9.5, body_size=7.6, line_h=0.27)

    # ── 4. Volume pg_data (cylinder-style box, ngoài docker network) ──
    _box(ax, 7.05, 0.85, 3.0, 1.95, "Volume: pg_data",
         ["• Persistent — survive",
          "  container restart",
          "• Mount → /var/lib/postgresql/data",
          "• Backup thủ công bằng",
          "  pg_dump theo lịch"],
         fill="#F0FDF4", edge="#15803D", title_color="#15803D",
         title_size=9.5, body_size=7.6, line_h=0.27)

    # ── 5. SMTP external ──
    _box(ax, 15.0, 4.8, 1.9, 2.4, "SMTP\nexternal",
         ["• smtp.gmail.com",
          "• TLS 587",
          "• Forgot password",
          "• Fail-silent",
          "  (HTTP 200 cả",
          "   khi SMTP lỗi)"],
         fill="#F3E8FF", edge="#6D28D9", title_color="#6D28D9",
         title_size=9.5, body_size=7.4, line_h=0.27)

    # ───────── Arrows ─────────
    # User → Cloudflare Edge
    _arrow(ax, (2.6, 7.0), (3.1, 6.6), "HTTPS 443")
    _arrow(ax, (2.6, 5.5), (3.1, 5.5), "HTTPS 443")

    # Cloudflare Edge → cloudflared (label ở giữa, không đè box)
    _arrow(ax, (6.3, 6.3), (7.05, 6.55),
           "Tunnel TCP\n+ X-Forwarded-For",
           label_offset=(0.0, 0.30))

    # cloudflared → frontend (label phía trên cùng, không đè body)
    _arrow(ax, (10.05, 6.55), (10.5, 6.5),
           "→ frontend:3000",
           label_offset=(0.0, 0.30))

    # frontend → backend (arrow ngắn, không label — info ở bullet body)
    _arrow(ax, (12.5, 5.5), (12.5, 5.3), "")

    # backend → postgres (arrow ngắn, không label — info ở bullet body)
    _arrow(ax, (12.5, 3.0), (12.5, 2.8), "")

    # postgres ↔ volume (mount, dashed)
    _arrow(ax, (10.5, 1.7), (10.05, 1.7),
           "mount", dashed=True, label_offset=(0, 0.18))

    # backend → SMTP (dashed, optional, đi qua phía trên)
    _arrow(ax, (14.5, 4.5), (15.0, 5.0),
           "SMTP",
           dashed=True, rad=-0.20,
           label_offset=(0.30, -0.10))

    # ───────── Legend / Notes ─────────
    ax.text(0.2, 4.10, "Ghi chú", fontsize=10.5, fontweight="bold",
            color="#1E3A8A")
    notes = [
        "• Backend, Postgres KHÔNG bind port ra host → giảm bề mặt tấn công.",
        "  Chỉ cloudflared expose ra Internet thông qua egress tunnel.",
        "• cloudflared là remotely-managed (tunnel my-tunnel) — file",
        "  config.yml local không có hiệu lực; mọi thay đổi routing/ingress",
        "  phải qua Cloudflare API hoặc Zero Trust dashboard.",
        "• Cloudflare Edge tự động chèn header X-Forwarded-For chứa IP",
        "  thật của client; backend slowapi dùng header này làm key cho",
        "  rate limit (login 30/phút, register 20/phút).",
        "• Migration Alembic auto-run khi backend khởi động",
        "  (entrypoint: alembic upgrade head && uvicorn …).",
        "• Volume pg_data persist khi container bị xóa/tạo lại;",
        "  backup thủ công qua pg_dump (xem mục 5.3 hạn chế).",
        "• SMTP fail-silent: nếu Gmail SMTP timeout, backend vẫn trả",
        "  HTTP 200 — tránh leak email tồn tại / chưa tồn tại.",
    ]
    for i, n in enumerate(notes):
        ax.text(0.2, 3.80 - i * 0.28, n, fontsize=7.8,
                color="#111827")

    out = OUT / "deployment.png"
    fig.savefig(out, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"[OK] {out}")


if __name__ == "__main__":
    render()
