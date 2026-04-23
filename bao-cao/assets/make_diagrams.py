"""Vẽ sơ đồ tuần tự (sequence) và sơ đồ activity bằng matplotlib."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
from matplotlib.patches import Polygon
import numpy as np

OUT = Path(__file__).parent

plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["font.size"] = 10


def _actor_box(ax, x, y, w, h, text, color="#DBEAFE", edge="#1E3A8A"):
    box = FancyBboxPatch((x - w/2, y - h/2), w, h,
                         boxstyle="round,pad=0.02",
                         linewidth=1.5, edgecolor=edge, facecolor=color)
    ax.add_patch(box)
    ax.text(x, y, text, ha="center", va="center", fontsize=10, fontweight="bold")


def _lifeline(ax, x, y_top, y_bot, color="#1E3A8A"):
    ax.plot([x, x], [y_top, y_bot], linestyle="--", color=color, linewidth=1, alpha=0.6)


def _activation(ax, x, y_top, y_bot, color="#93C5FD"):
    w = 0.12
    ax.add_patch(Rectangle((x - w/2, y_bot), w, y_top - y_bot,
                            linewidth=0.8, edgecolor="#1E3A8A", facecolor=color))


def _msg(ax, x1, x2, y, text, style="-", color="#111827"):
    arrow = "<|-" if style == "return" else "-|>"
    ax.annotate("", xy=(x2, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle=arrow, color=color,
                                linestyle=("--" if style == "return" else "-"),
                                linewidth=1.3))
    mid = (x1 + x2) / 2
    ax.text(mid, y + 0.18, text, ha="center", va="bottom", fontsize=9,
            color=color)


def _note(ax, x, y, w, h, text, color="#FEF3C7", edge="#D97706"):
    box = FancyBboxPatch((x - w/2, y - h/2), w, h,
                         boxstyle="round,pad=0.02",
                         linewidth=1, edgecolor=edge, facecolor=color)
    ax.add_patch(box)
    ax.text(x, y, text, ha="center", va="center", fontsize=8, style="italic")


# ---------------- Sequence 1: Claim voucher ----------------
def seq_claim_voucher():
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 10)
    ax.axis("off")

    # Actors
    actors = [
        (1.5, "Khách hàng\n(PWA /member)"),
        (4.0, "Frontend\n(Next.js)"),
        (6.5, "FastAPI\n/campaigns/claim"),
        (9.0, "VoucherService"),
        (11.0, "PostgreSQL"),
    ]
    for x, name in actors:
        _actor_box(ax, x, 9.3, 1.7, 0.7, name)
        _lifeline(ax, x, 9.0, 0.5)

    # Messages (y từ trên xuống)
    y = 8.3
    _msg(ax, 1.5, 4.0, y, "bấm \"Nhận ngay\"")
    y -= 0.6
    _msg(ax, 4.0, 6.5, y, "POST /campaigns/{id}/claim\n+ JWT, X-Tenant-Id")
    y -= 0.7
    _msg(ax, 6.5, 9.0, y, "claim(user_id, campaign_id)")
    y -= 0.5
    _activation(ax, 9.0, y + 0.2, y - 3.0)

    y -= 0.3
    _msg(ax, 9.0, 11.0, y, "BEGIN TRANSACTION")
    y -= 0.5
    _msg(ax, 9.0, 11.0, y, "pg_advisory_xact_lock(hash)")
    y -= 0.5
    _msg(ax, 9.0, 11.0, y, "UPDATE campaign SET issued_count=...\nWHERE issued_count < max_issuances")
    y -= 0.7
    _msg(ax, 11.0, 9.0, y, "rows_affected = 1", style="return")
    y -= 0.5
    _msg(ax, 9.0, 11.0, y, "INSERT INTO voucher (...)")
    y -= 0.5
    _msg(ax, 9.0, 11.0, y, "COMMIT")
    y -= 0.5
    _msg(ax, 11.0, 9.0, y, "voucher_id, code", style="return")

    y -= 0.6
    _msg(ax, 9.0, 6.5, y, "Voucher DTO", style="return")
    y -= 0.6
    _msg(ax, 6.5, 4.0, y, "201 Created\n+ voucher JSON", style="return")
    y -= 0.6
    _msg(ax, 4.0, 1.5, y, "hiển thị voucher mới", style="return")

    # Note: TOCTOU protection
    _note(ax, 10.0, 2.0, 3.0, 0.8,
          "Nếu rows_affected=0 → rollback, trả 409\n(quota đã hết — chống TOCTOU)")

    ax.set_title("Sơ đồ tuần tự — Khách hàng claim voucher (chống TOCTOU)",
                 fontsize=12, fontweight="bold", pad=15)
    plt.tight_layout()
    fig.savefig(OUT / "sequence_claim_voucher.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("OK sequence_claim_voucher.png")


# ---------------- Sequence 2: Đăng nhập + chọn tenant ----------------
def seq_login_tenant():
    fig, ax = plt.subplots(figsize=(12, 7.5))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 9)
    ax.axis("off")

    actors = [
        (1.5, "User\n(browser)"),
        (4.0, "Frontend\n(Next.js)"),
        (6.5, "FastAPI\n/auth/login"),
        (9.0, "AuthService"),
        (11.0, "PostgreSQL"),
    ]
    for x, name in actors:
        _actor_box(ax, x, 8.3, 1.7, 0.7, name)
        _lifeline(ax, x, 8.0, 0.5)

    y = 7.3
    _msg(ax, 1.5, 4.0, y, "nhập email + password")
    y -= 0.55
    _msg(ax, 4.0, 6.5, y, "POST /auth/login")
    y -= 0.55
    _msg(ax, 6.5, 9.0, y, "authenticate(email, pw)")
    y -= 0.5
    _msg(ax, 9.0, 11.0, y, "SELECT user, memberships")
    y -= 0.5
    _msg(ax, 11.0, 9.0, y, "user + tenant_ids", style="return")
    y -= 0.5
    _note(ax, 9.5, y - 0.2, 3.5, 0.5, "bcrypt.checkpw(pw, hashed)")
    y -= 0.8
    _msg(ax, 9.0, 6.5, y, "jwt_token (exp 1h)", style="return")
    y -= 0.55
    _msg(ax, 6.5, 4.0, y, "200 OK + access_token\n+ memberships", style="return")
    y -= 0.65

    _note(ax, 4.0, y, 3.5, 0.5, "Zustand tenant-store.setTenant(id)")
    y -= 0.6
    _msg(ax, 4.0, 6.5, y, "GET /members/me\nAuth: Bearer ... + X-Tenant-Id")
    y -= 0.55
    _note(ax, 6.5, y - 0.2, 3.5, 0.6, "require_customer_in_tenant\nhoặc require_owner_in_tenant")
    y -= 0.9
    _msg(ax, 6.5, 4.0, y, "member profile", style="return")
    y -= 0.6
    _msg(ax, 4.0, 1.5, y, "render dashboard", style="return")

    ax.set_title("Sơ đồ tuần tự — Đăng nhập JWT và chọn tenant",
                 fontsize=12, fontweight="bold", pad=15)
    plt.tight_layout()
    fig.savefig(OUT / "sequence_login_tenant.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("OK sequence_login_tenant.png")


# ---------------- Sequence 3: Redeem OTP với context_hash ----------------
def seq_redeem_otp():
    fig, ax = plt.subplots(figsize=(12, 8.5))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 10)
    ax.axis("off")

    actors = [
        (1.2, "Khách hàng"),
        (3.5, "Staff POS"),
        (6.0, "FastAPI\n/rewards/redeem"),
        (8.5, "RewardService"),
        (10.8, "PostgreSQL"),
    ]
    for x, name in actors:
        _actor_box(ax, x, 9.3, 1.7, 0.7, name)
        _lifeline(ax, x, 9.0, 0.5)

    y = 8.3
    _msg(ax, 3.5, 6.0, y, "POST /rewards/{id}/request-otp\nbody: reward_id, member_id")
    y -= 0.55
    _msg(ax, 6.0, 8.5, y, "request_otp(...)")
    y -= 0.5
    _note(ax, 8.5, y - 0.2, 3.5, 0.7,
          "context_hash = HMAC_SHA256(\nkey=secret, msg=reward_id|member_id|staff_id)")
    y -= 0.9
    _msg(ax, 8.5, 10.8, y, "INSERT otp (code, context_hash,\nexpires_at=now+3m)")
    y -= 0.55
    _msg(ax, 10.8, 8.5, y, "otp_id", style="return")
    y -= 0.5
    _msg(ax, 8.5, 6.0, y, "otp_code (6 digits)", style="return")
    y -= 0.5
    _msg(ax, 6.0, 3.5, y, "200 OK", style="return")
    y -= 0.55

    _msg(ax, 3.5, 1.2, y, "đọc mã OTP cho khách")
    y -= 0.55
    _msg(ax, 1.2, 3.5, y, "khách đọc lại mã")
    y -= 0.55
    _msg(ax, 3.5, 6.0, y, "POST /rewards/{id}/confirm-otp\nbody: otp, reward_id, member_id")
    y -= 0.6
    _msg(ax, 6.0, 8.5, y, "confirm_otp(otp, ...)")
    y -= 0.5
    _msg(ax, 8.5, 10.8, y, "SELECT otp WHERE code=? AND\ncontext_hash=? AND expires_at>now()")
    y -= 0.65

    _note(ax, 10.0, y - 0.2, 3.0, 0.6,
          "Nếu context bị sửa → hash\nkhác → không tìm thấy → 400")
    y -= 0.9
    _msg(ax, 10.8, 8.5, y, "otp row", style="return")
    y -= 0.45
    _msg(ax, 8.5, 10.8, y, "INSERT redemption, UPDATE points")
    y -= 0.5
    _msg(ax, 10.8, 8.5, y, "redemption_id", style="return")
    y -= 0.5
    _msg(ax, 8.5, 6.0, y, "redemption DTO", style="return")
    y -= 0.5
    _msg(ax, 6.0, 3.5, y, "200 OK — xác nhận", style="return")

    ax.set_title("Sơ đồ tuần tự — Đổi quà bằng OTP ràng buộc context_hash",
                 fontsize=12, fontweight="bold", pad=15)
    plt.tight_layout()
    fig.savefig(OUT / "sequence_redeem_otp.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("OK sequence_redeem_otp.png")


# ---------------- Activity 1: Campaign approval ----------------
def activity_campaign():
    fig, ax = plt.subplots(figsize=(11, 12))
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 14)
    ax.axis("off")

    def pill(x, y, w, h, text, color="#DBEAFE"):
        box = FancyBboxPatch((x - w/2, y - h/2), w, h,
                             boxstyle="round,pad=0.02,rounding_size=0.25",
                             linewidth=1.3, edgecolor="#1E3A8A", facecolor=color)
        ax.add_patch(box)
        ax.text(x, y, text, ha="center", va="center", fontsize=10)

    def diamond(x, y, w, h, text, color="#FEF3C7"):
        poly = Polygon([(x, y + h/2), (x + w/2, y), (x, y - h/2), (x - w/2, y)],
                       linewidth=1.3, edgecolor="#D97706", facecolor=color)
        ax.add_patch(poly)
        ax.text(x, y, text, ha="center", va="center", fontsize=9)

    def start_end(x, y, r, text, color="#6EE7B7"):
        circ = plt.Circle((x, y), r, linewidth=1.5, edgecolor="#065F46", facecolor=color)
        ax.add_patch(circ)
        ax.text(x, y, text, ha="center", va="center", fontsize=9, fontweight="bold")

    def arrow(x1, y1, x2, y2, label=None):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", color="#111827", linewidth=1.2))
        if label:
            mx, my = (x1 + x2)/2, (y1 + y2)/2
            ax.text(mx + 0.12, my, label, fontsize=8, style="italic", color="#374151")

    start_end(5.5, 13.3, 0.3, "Start")
    pill(5.5, 12.5, 4.5, 0.5, "Owner tạo campaign (draft)")
    pill(5.5, 11.5, 4.5, 0.5, "Hệ thống compute approval_tier")
    diamond(5.5, 10.3, 4.0, 1.0, "tier ≥ notify_so_ct?")
    pill(2.0, 9.0, 3.0, 0.5, "status = ready_to_activate", color="#DCFCE7")
    pill(8.5, 9.0, 3.5, 0.5, "Owner nộp hồ sơ Sở Công Thương")
    pill(8.5, 8.0, 3.5, 0.5, "status = pending_regulatory")
    pill(8.5, 7.0, 3.5, 0.5, "Super admin reviews")
    diamond(8.5, 5.8, 3.5, 1.0, "Hợp lệ?")
    pill(6.0, 4.5, 3.0, 0.5, "status = approved", color="#DCFCE7")
    pill(10.2, 4.5, 1.6, 0.5, "rejected", color="#FEE2E2")
    diamond(5.5, 3.3, 3.5, 1.0, "now ≥ start_at?")
    pill(5.5, 2.0, 3.5, 0.5, "status = active", color="#DCFCE7")
    pill(5.5, 1.0, 3.5, 0.5, "Khách claim/redeem voucher")
    diamond(5.5, -0.2, 3.5, 1.0, "now ≥ end_at?")
    pill(5.5, -1.4, 3.5, 0.5, "status = ended")
    pill(5.5, -2.4, 4.5, 0.5, "Xuất báo cáo hậu khuyến mại (NĐ81 Đ.20)")
    start_end(5.5, -3.3, 0.3, "End")

    # arrows
    arrow(5.5, 13.0, 5.5, 12.75)
    arrow(5.5, 12.25, 5.5, 11.75)
    arrow(5.5, 11.25, 5.5, 10.8)
    arrow(3.5, 10.3, 2.0, 9.25, label="No")
    arrow(7.5, 10.3, 8.5, 9.25, label="Yes")
    arrow(2.0, 8.75, 2.0, 3.3)
    arrow(2.0, 3.3, 3.75, 3.3, label="")
    arrow(8.5, 8.75, 8.5, 8.25)
    arrow(8.5, 7.75, 8.5, 7.25)
    arrow(8.5, 6.75, 8.5, 6.3)
    arrow(7.5, 5.8, 6.0, 4.75, label="Yes")
    arrow(9.5, 5.8, 10.2, 4.75, label="No")
    arrow(10.2, 4.25, 10.2, -3.0)
    arrow(10.2, -3.0, 5.8, -3.3, label="")
    arrow(6.0, 4.25, 5.5, 3.8)
    arrow(5.5, 2.75, 5.5, 2.25, label="Yes")
    arrow(3.75, 3.3, 3.0, 3.3)  # no path waits
    ax.text(3.2, 3.6, "No — chờ\nstart_at", fontsize=8, style="italic", color="#374151")
    arrow(5.5, 1.75, 5.5, 1.25)
    arrow(5.5, 0.75, 5.5, 0.3)
    arrow(5.5, -0.7, 5.5, -1.15, label="Yes")
    arrow(3.75, -0.2, 3.0, -0.2, label="No")
    ax.text(3.0, 0.1, "No — chờ", fontsize=8, style="italic", color="#374151")
    arrow(5.5, -1.65, 5.5, -2.15)
    arrow(5.5, -2.65, 5.5, -3.0)

    ax.set_title("Sơ đồ activity — Vòng đời chiến dịch khuyến mại theo Nghị định 81",
                 fontsize=12, fontweight="bold", pad=15)
    plt.tight_layout()
    fig.savefig(OUT / "activity_campaign_lifecycle.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("OK activity_campaign_lifecycle.png")


# ---------------- Activity 2: Voucher lifecycle ----------------
def activity_voucher():
    fig, ax = plt.subplots(figsize=(10, 9))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 11)
    ax.axis("off")

    def pill(x, y, w, h, text, color="#DBEAFE"):
        box = FancyBboxPatch((x - w/2, y - h/2), w, h,
                             boxstyle="round,pad=0.02,rounding_size=0.25",
                             linewidth=1.3, edgecolor="#1E3A8A", facecolor=color)
        ax.add_patch(box)
        ax.text(x, y, text, ha="center", va="center", fontsize=10)

    def diamond(x, y, w, h, text, color="#FEF3C7"):
        poly = Polygon([(x, y + h/2), (x + w/2, y), (x, y - h/2), (x - w/2, y)],
                       linewidth=1.3, edgecolor="#D97706", facecolor=color)
        ax.add_patch(poly)
        ax.text(x, y, text, ha="center", va="center", fontsize=9)

    def start_end(x, y, r, text, color="#6EE7B7"):
        circ = plt.Circle((x, y), r, linewidth=1.5, edgecolor="#065F46", facecolor=color)
        ax.add_patch(circ)
        ax.text(x, y, text, ha="center", va="center", fontsize=9, fontweight="bold")

    def arrow(x1, y1, x2, y2, label=None):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", color="#111827", linewidth=1.2))
        if label:
            mx, my = (x1 + x2)/2, (y1 + y2)/2
            ax.text(mx + 0.12, my, label, fontsize=8, style="italic", color="#374151")

    start_end(5.0, 10.3, 0.3, "Start")
    pill(5.0, 9.5, 5.0, 0.5, "Campaign active — khách đủ điều kiện")
    diamond(5.0, 8.3, 4.0, 1.0, "UPDATE quota OK?")
    pill(8.0, 8.3, 1.6, 0.5, "409", color="#FEE2E2")
    pill(5.0, 7.0, 5.0, 0.5, "INSERT voucher status=active")
    pill(5.0, 6.0, 5.0, 0.5, "Voucher hiển thị trong /member")
    diamond(5.0, 4.7, 4.0, 1.0, "Khách áp dụng tại POS?")
    pill(5.0, 3.4, 5.0, 0.5, "Staff quét QR, kiểm tra điều kiện")
    diamond(5.0, 2.2, 4.0, 1.0, "Áp dụng thành công?")
    pill(2.0, 1.0, 2.5, 0.5, "status=used", color="#DCFCE7")
    pill(8.0, 1.0, 2.5, 0.5, "voucher lỗi", color="#FEE2E2")
    pill(1.5, 4.7, 2.5, 0.5, "status=expired", color="#E5E7EB")
    start_end(5.0, 0.1, 0.3, "End")

    arrow(5.0, 10.0, 5.0, 9.75)
    arrow(5.0, 9.25, 5.0, 8.8)
    arrow(7.0, 8.3, 7.2, 8.3, label="No")
    arrow(5.0, 7.8, 5.0, 7.25, label="Yes")
    arrow(5.0, 6.75, 5.0, 6.25)
    arrow(5.0, 5.75, 5.0, 5.2)
    arrow(3.0, 4.7, 2.75, 4.7, label="cron: end_at qua")
    arrow(5.0, 4.2, 5.0, 3.65, label="Yes")
    arrow(5.0, 3.15, 5.0, 2.7)
    arrow(3.0, 2.2, 2.0, 1.25, label="Yes")
    arrow(7.0, 2.2, 8.0, 1.25, label="No")
    arrow(2.0, 0.75, 4.7, 0.3)
    arrow(8.0, 0.75, 5.3, 0.3)
    arrow(1.5, 4.45, 4.7, 0.3)

    ax.set_title("Sơ đồ activity — Vòng đời voucher",
                 fontsize=12, fontweight="bold", pad=15)
    plt.tight_layout()
    fig.savefig(OUT / "activity_voucher_lifecycle.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("OK activity_voucher_lifecycle.png")


if __name__ == "__main__":
    seq_claim_voucher()
    seq_login_tenant()
    seq_redeem_otp()
    activity_campaign()
    activity_voucher()
