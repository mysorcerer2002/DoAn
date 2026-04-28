"""Vẽ 5 sơ đồ UML cho báo cáo MVP:
- 3 sơ đồ tuần tự: login JWT, POS tích điểm, đổi quà
- 2 sơ đồ hoạt động: đăng ký merchant, quên mật khẩu fail-silent

Output: bao-cao/assets/diagrams/*.png
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import (
    FancyArrowPatch,
    FancyBboxPatch,
    Polygon,
    Rectangle,
)

OUT = Path(__file__).parent / "diagrams"
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["font.size"] = 10


# ─────────────────── helpers chung ───────────────────
def _actor_box(ax, x, y, w, h, text, color="#DBEAFE", edge="#1E3A8A"):
    box = FancyBboxPatch(
        (x - w / 2, y - h / 2), w, h,
        boxstyle="round,pad=0.02",
        linewidth=1.4, edgecolor=edge, facecolor=color,
    )
    ax.add_patch(box)
    ax.text(x, y, text, ha="center", va="center",
            fontsize=9.5, fontweight="bold", color="#0F172A")


def _lifeline(ax, x, y_top, y_bot, color="#1E3A8A"):
    ax.plot([x, x], [y_top, y_bot], linestyle="--",
            color=color, linewidth=0.9, alpha=0.55)


def _activation(ax, x, y_top, y_bot, color="#93C5FD"):
    w = 0.10
    ax.add_patch(Rectangle(
        (x - w / 2, y_bot), w, y_top - y_bot,
        linewidth=0.8, edgecolor="#1E3A8A", facecolor=color,
    ))


def _msg(ax, x1, x2, y, text, kind="call", color="#0F172A"):
    """kind: call | return | self"""
    if kind == "self":
        # vẽ self-loop bên phải actor
        ax.plot([x1, x1 + 0.35], [y, y], color=color, linewidth=1.1)
        ax.plot([x1 + 0.35, x1 + 0.35], [y, y - 0.20], color=color,
                linewidth=1.1)
        ax.annotate("", xy=(x1, y - 0.20), xytext=(x1 + 0.35, y - 0.20),
                    arrowprops=dict(arrowstyle="-|>", color=color,
                                    linewidth=1.1))
        ax.text(x1 + 0.45, y - 0.05, text, ha="left", va="center",
                fontsize=8.5, color=color)
        return
    arrow_style = "-|>"
    line_style = "-"
    if kind == "return":
        arrow_style = "-|>"
        line_style = "--"
    ax.annotate("", xy=(x2, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle=arrow_style, color=color,
                                linestyle=line_style, linewidth=1.2))
    mid = (x1 + x2) / 2
    ax.text(mid, y + 0.12, text, ha="center", va="bottom",
            fontsize=8.5, color=color)


def _note(ax, cx, cy, w, h, text,
          color="#FEF3C7", edge="#D97706"):
    box = FancyBboxPatch(
        (cx - w / 2, cy - h / 2), w, h,
        boxstyle="round,pad=0.02",
        linewidth=1, edgecolor=edge, facecolor=color,
    )
    ax.add_patch(box)
    ax.text(cx, cy, text, ha="center", va="center",
            fontsize=8, style="italic", color="#92400E")


# Activity helpers
def _act_start(ax, cx, cy, label="Bắt đầu"):
    circ = plt.Circle((cx, cy), 0.18, color="#0F172A", zorder=3)
    ax.add_patch(circ)
    ax.text(cx + 0.32, cy, label, ha="left", va="center",
            fontsize=8.5, style="italic")


def _act_end(ax, cx, cy, label="Kết thúc"):
    outer = plt.Circle((cx, cy), 0.20, fill=False,
                       edgecolor="#0F172A", linewidth=1.3, zorder=3)
    inner = plt.Circle((cx, cy), 0.10, color="#0F172A", zorder=4)
    ax.add_patch(outer)
    ax.add_patch(inner)
    ax.text(cx + 0.32, cy, label, ha="left", va="center",
            fontsize=8.5, style="italic")


def _act_box(ax, cx, cy, w, h, text,
             fill="#DBEAFE", edge="#1E3A8A"):
    box = FancyBboxPatch(
        (cx - w / 2, cy - h / 2), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.18",
        linewidth=1.3, edgecolor=edge, facecolor=fill,
    )
    ax.add_patch(box)
    ax.text(cx, cy, text, ha="center", va="center",
            fontsize=9, color="#0F172A")


def _diamond(ax, cx, cy, w, h, text,
             fill="#FEF3C7", edge="#D97706"):
    pts = [(cx, cy + h / 2), (cx + w / 2, cy),
           (cx, cy - h / 2), (cx - w / 2, cy)]
    poly = Polygon(pts, closed=True, linewidth=1.4,
                   edgecolor=edge, facecolor=fill)
    ax.add_patch(poly)
    ax.text(cx, cy, text, ha="center", va="center",
            fontsize=8.5, color="#92400E")


def _arrow(ax, p1, p2, label="", color="#0F172A",
           rad=0.0, label_offset=(0, 0)):
    a = FancyArrowPatch(
        p1, p2, arrowstyle="-|>", mutation_scale=12,
        linewidth=1.1, color=color,
        connectionstyle=f"arc3,rad={rad}",
    )
    ax.add_patch(a)
    if label:
        mx = (p1[0] + p2[0]) / 2 + label_offset[0]
        my = (p1[1] + p2[1]) / 2 + label_offset[1]
        ax.text(mx, my, label, ha="center", va="center",
                fontsize=8, color=color, style="italic",
                bbox=dict(facecolor="white", edgecolor="none",
                          pad=1.2, alpha=0.9))


# ─────────────────── 1. Sequence: Login JWT ───────────────────
def seq_login():
    fig, ax = plt.subplots(figsize=(13, 8.5))
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 10)
    ax.axis("off")

    ax.text(6.5, 9.65, "Sơ đồ tuần tự — Đăng nhập JWT",
            ha="center", va="center", fontsize=13,
            fontweight="bold", color="#1E3A8A")

    actors = [
        (1.3, "Người dùng\n(Browser)"),
        (3.8, "Frontend\n(Next.js)"),
        (6.5, "Backend\n/auth/login"),
        (9.2, "AuthService\n+ bcrypt"),
        (11.6, "PostgreSQL\n(users,\nlogin_logs)"),
    ]
    for x, name in actors:
        _actor_box(ax, x, 8.95, 1.9, 0.85, name)
        _lifeline(ax, x, 8.5, 0.5)

    y = 8.0
    _msg(ax, 1.3, 3.8, y, "Submit form (email/phone, password)")
    y -= 0.55
    _msg(ax, 3.8, 6.5, y, "POST /auth/login (JSON body)")
    y -= 0.55
    _msg(ax, 6.5, 9.2, y, "authenticate(identifier, password)")
    _activation(ax, 9.2, y + 0.15, y - 2.8)
    y -= 0.55
    _msg(ax, 9.2, 11.6, y, "SELECT * FROM users WHERE email=$1")
    y -= 0.45
    _msg(ax, 11.6, 9.2, y, "user row (password_hash)", kind="return")
    y -= 0.50
    _msg(ax, 9.2, 9.2, y, "bcrypt.checkpw(password, hash)",
         kind="self")
    y -= 0.55
    _msg(ax, 9.2, 11.6, y,
         "INSERT login_logs (success=true, ip, ua)")
    y -= 0.45
    _msg(ax, 11.6, 9.2, y, "OK", kind="return")
    y -= 0.50
    _msg(ax, 9.2, 6.5, y,
         "user object", kind="return")
    y -= 0.55
    _msg(ax, 6.5, 6.5, y,
         "jwt.encode(user_id+role, exp=24h, HS256)",
         kind="self")
    y -= 0.55
    _msg(ax, 6.5, 3.8, y,
         "200 { access_token, refresh_token, user }",
         kind="return")
    y -= 0.55
    _msg(ax, 3.8, 3.8, y,
         "localStorage.set(token); axios interceptor",
         kind="self")
    y -= 0.55
    _msg(ax, 3.8, 1.3, y, "Redirect → /member (or /merchant)",
         kind="return")

    _note(ax, 9.2, 1.0, 4.5, 0.6,
          "Nếu password sai: INSERT login_logs success=false → "
          "raise InvalidCredentials → HTTP 401")

    out = OUT / "seq-login.png"
    fig.savefig(out, dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"[OK] {out}")


# ─────────────────── 2. Sequence: POS earn ───────────────────
def seq_pos_earn():
    fig, ax = plt.subplots(figsize=(13.5, 9))
    ax.set_xlim(0, 13.5)
    ax.set_ylim(0, 10)
    ax.axis("off")

    ax.text(6.75, 9.65, "Sơ đồ tuần tự — POS tích điểm",
            ha="center", va="center", fontsize=13,
            fontweight="bold", color="#1E3A8A")

    actors = [
        (1.0, "Khách hàng\n/member/qr"),
        (3.3, "Staff POS\n/staff"),
        (5.6, "Frontend"),
        (8.0, "Backend\n/staff/\ntransactions"),
        (10.4, "Transaction\nService"),
        (12.5, "PostgreSQL\n(users, txn,\nledger)"),
    ]
    for x, name in actors:
        _actor_box(ax, x, 8.95, 1.85, 0.95, name)
        _lifeline(ax, x, 8.4, 0.4)

    y = 7.9
    _msg(ax, 1.0, 1.0, y,
         "render QR (payload = user_id JSON)", kind="self")
    y -= 0.55
    _msg(ax, 1.0, 3.3, y, "Hiển thị QR cho staff scan")
    y -= 0.55
    _msg(ax, 3.3, 5.6, y,
         "scan QR → decode user_id → nhập gross_amount")
    y -= 0.55
    _msg(ax, 5.6, 8.0, y,
         "POST /staff/transactions\n+ X-Partner-Id, JWT")
    y -= 0.65
    _msg(ax, 8.0, 10.4, y,
         "create_transaction(user_id, partner_id, gross)")
    _activation(ax, 10.4, y + 0.15, y - 3.3)
    y -= 0.55
    _msg(ax, 10.4, 12.5, y,
         "SELECT membership(partner_id, user_id)")
    y -= 0.40
    _msg(ax, 12.5, 10.4, y, "membership", kind="return")
    y -= 0.50
    _msg(ax, 10.4, 10.4, y,
         "earned = floor(net / 10000)", kind="self")
    y -= 0.55
    _msg(ax, 10.4, 12.5, y,
         "INSERT transactions (gross, net, earned)")
    y -= 0.40
    _msg(ax, 10.4, 12.5, y,
         "INSERT point_ledger (delta=+earned, reason=earn)")
    y -= 0.40
    _msg(ax, 10.4, 12.5, y,
         "UPDATE users SET points_balance += earned RETURNING")
    y -= 0.40
    _msg(ax, 12.5, 10.4, y, "new_balance", kind="return")
    y -= 0.55
    _msg(ax, 10.4, 8.0, y, "TransactionResponse", kind="return")
    y -= 0.55
    _msg(ax, 8.0, 5.6, y, "200 { txn, points_earned, balance }",
         kind="return")
    y -= 0.55
    _msg(ax, 5.6, 3.3, y, "Hiển thị xác nhận tích điểm",
         kind="return")

    _note(ax, 11.4, 0.65, 4.0, 0.7,
          "Tất cả 3 thao tác DB nằm trong cùng 1 transaction; "
          "rollback toàn bộ nếu bất kỳ bước nào fail.")

    out = OUT / "seq-pos-earn.png"
    fig.savefig(out, dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"[OK] {out}")


# ─────────────────── 3. Sequence: Redeem ───────────────────
def seq_redeem():
    fig, ax = plt.subplots(figsize=(13.5, 9))
    ax.set_xlim(0, 13.5)
    ax.set_ylim(0, 10)
    ax.axis("off")

    ax.text(6.75, 9.65, "Sơ đồ tuần tự — Đổi quà từ trang đối tác",
            ha="center", va="center", fontsize=13,
            fontweight="bold", color="#1E3A8A")

    actors = [
        (1.3, "Khách hàng\n/member/\npartners/{slug}"),
        (4.2, "Frontend"),
        (7.0, "Backend\n/partners/{id}/\nrewards/{rid}/\nredeem"),
        (9.7, "Redemption\nService"),
        (12.4, "PostgreSQL\n(users,\nrewards,\nredemptions,\nledger)"),
    ]
    for x, name in actors:
        _actor_box(ax, x, 8.85, 2.2, 1.05, name)
        _lifeline(ax, x, 8.3, 0.4)

    y = 7.7
    _msg(ax, 1.3, 4.2, y, "Bấm \"Đổi quà\" → dialog confirm")
    y -= 0.55
    _msg(ax, 1.3, 4.2, y, "Bấm Xác nhận")
    y -= 0.55
    _msg(ax, 4.2, 7.0, y,
         "POST /redeem + X-Partner-Id, JWT")
    y -= 0.60
    _msg(ax, 7.0, 9.7, y, "redeem(user_id, reward_id)")
    _activation(ax, 9.7, y + 0.15, y - 3.6)
    y -= 0.55
    _msg(ax, 9.7, 12.4, y,
         "SELECT reward (active, not deleted, stock>0)")
    y -= 0.40
    _msg(ax, 12.4, 9.7, y, "reward", kind="return")
    y -= 0.55
    _msg(ax, 9.7, 12.4, y,
         "UPDATE rewards SET stock = stock - 1\n"
         "WHERE id=$1 AND stock > 0 RETURNING")
    y -= 0.55
    _msg(ax, 9.7, 12.4, y,
         "INSERT redemptions (status=PENDING,\ncode=random_8_chars)")
    y -= 0.55
    _msg(ax, 9.7, 12.4, y,
         "INSERT point_ledger (delta=-cost, reason=redeem)")
    y -= 0.45
    _msg(ax, 9.7, 12.4, y,
         "UPDATE users SET points_balance = balance - cost\n"
         "WHERE id=$1 AND balance >= cost RETURNING")
    y -= 0.55
    _msg(ax, 12.4, 9.7, y,
         "new_balance | None (race lost)", kind="return")
    y -= 0.55
    _msg(ax, 9.7, 9.7, y,
         "if None → raise InsufficientPointsError",
         kind="self")
    y -= 0.60
    _msg(ax, 9.7, 7.0, y, "RedemptionResponse", kind="return")
    y -= 0.55
    _msg(ax, 7.0, 4.2, y, "200 { redemption, code, balance }",
         kind="return")
    y -= 0.55
    _msg(ax, 4.2, 1.3, y, "Điều hướng → /member/vouchers",
         kind="return")

    _note(ax, 10.2, 0.6, 5.5, 0.55,
          "Mệnh đề WHERE balance >= cost biến UPDATE thành "
          "atomic check-and-write — chống race condition.")

    out = OUT / "seq-redeem.png"
    fig.savefig(out, dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"[OK] {out}")


# ─────────────────── 4. Activity: Merchant register ─────────
def act_merchant_register():
    fig, ax = plt.subplots(figsize=(11, 11))
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 13)
    ax.axis("off")

    ax.text(5.5, 12.55, "Sơ đồ hoạt động — Đăng ký và duyệt merchant",
            ha="center", va="center", fontsize=13,
            fontweight="bold", color="#1E3A8A")

    # Lane labels
    ax.text(2.0, 12.0, "Owner", ha="center", va="center",
            fontsize=10.5, fontweight="bold", color="#92400E")
    ax.text(5.5, 12.0, "Hệ thống (Backend)", ha="center", va="center",
            fontsize=10.5, fontweight="bold", color="#1E3A8A")
    ax.text(9.0, 12.0, "Admin", ha="center", va="center",
            fontsize=10.5, fontweight="bold", color="#15803D")

    # vertical lane separators
    ax.plot([3.6, 3.6], [0.4, 11.7], color="#9CA3AF",
            linewidth=0.8, linestyle=":")
    ax.plot([7.4, 7.4], [0.4, 11.7], color="#9CA3AF",
            linewidth=0.8, linestyle=":")

    # Owner lane
    _act_start(ax, 2.0, 11.4)
    _act_box(ax, 2.0, 10.5, 2.6, 0.7,
             "Mở /register/merchant",
             fill="#FEF3C7", edge="#92400E")
    _act_box(ax, 2.0, 9.5, 2.6, 0.9,
             "Điền form: tên, mã số\nthuế, địa chỉ, owner info",
             fill="#FEF3C7", edge="#92400E")
    _act_box(ax, 2.0, 8.4, 2.6, 0.7,
             "Bấm \"Đăng ký\"",
             fill="#FEF3C7", edge="#92400E")

    # Backend lane
    _act_box(ax, 5.5, 7.3, 3.0, 0.9,
             "INSERT partner\nstatus = PENDING")
    _act_box(ax, 5.5, 6.2, 3.0, 0.7,
             "Trả thông báo\n\"Chờ admin duyệt\"")

    # Admin lane
    _act_box(ax, 9.0, 5.0, 2.6, 0.9,
             "Mở /admin/partners\nxem danh sách PENDING",
             fill="#DCFCE7", edge="#15803D")
    _act_box(ax, 9.0, 3.9, 2.6, 0.7,
             "Xem chi tiết hồ sơ",
             fill="#DCFCE7", edge="#15803D")

    # Decision diamond ở trục giữa
    _diamond(ax, 5.5, 2.6, 2.4, 1.1, "Approve\nhay\nReject?")

    # Two branches from diamond
    _act_box(ax, 2.0, 1.1, 2.6, 1.0,
             "UPDATE status=ACTIVE\nINSERT ledger seed\n+1.000.000 điểm")
    _act_box(ax, 9.0, 1.1, 2.6, 1.0,
             "UPDATE status=REJECTED\nLưu lý do từ chối",
             fill="#FEE2E2", edge="#B91C1C")

    _act_end(ax, 2.0, 0.30)
    _act_end(ax, 9.0, 0.30)

    # Arrows
    _arrow(ax, (2.0, 11.22), (2.0, 10.85))
    _arrow(ax, (2.0, 10.15), (2.0, 9.95))
    _arrow(ax, (2.0, 9.05), (2.0, 8.75))
    _arrow(ax, (2.0, 8.05), (5.5, 7.75),
           label="POST /partners/register",
           label_offset=(0.2, 0.10))
    _arrow(ax, (5.5, 6.85), (5.5, 6.55))
    _arrow(ax, (5.5, 5.85), (9.0, 5.45),
           label="(notify admin)",
           label_offset=(0.2, 0.05))
    _arrow(ax, (9.0, 4.55), (9.0, 4.25))
    _arrow(ax, (9.0, 3.55), (5.5, 3.15),
           label="POST /admin/partners/{id}/review",
           label_offset=(-0.1, 0.10))
    _arrow(ax, (4.5, 2.4), (3.3, 1.6),
           label="Approve", label_offset=(-0.20, 0.20))
    _arrow(ax, (6.5, 2.4), (7.7, 1.6),
           label="Reject", label_offset=(0.20, 0.20))
    _arrow(ax, (2.0, 0.6), (2.0, 0.55))
    _arrow(ax, (9.0, 0.6), (9.0, 0.55))

    out = OUT / "act-merchant-register.png"
    fig.savefig(out, dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"[OK] {out}")


# ─────────────────── 5. Activity: Forgot password ────────────
def act_forgot_password():
    fig, ax = plt.subplots(figsize=(10, 12))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 14)
    ax.axis("off")

    ax.text(5.0, 13.55,
            "Sơ đồ hoạt động — Quên mật khẩu (fail-silent SMTP)",
            ha="center", va="center", fontsize=12.5,
            fontweight="bold", color="#1E3A8A")

    _act_start(ax, 2.0, 12.8)
    _act_box(ax, 2.0, 12.0, 3.0, 0.7,
             "Mở /forgot-password",
             fill="#FEF3C7", edge="#92400E")
    _act_box(ax, 2.0, 11.0, 3.0, 0.7,
             "Nhập email + Submit",
             fill="#FEF3C7", edge="#92400E")

    _act_box(ax, 5.0, 9.9, 3.6, 0.8,
             "POST /auth/forgot-password\n{ email }")
    _diamond(ax, 5.0, 8.6, 3.0, 1.1,
             "User tồn tại\nvới email này?")

    # Branch: not found
    _act_box(ax, 8.5, 7.5, 2.6, 1.0,
             "(Không tạo gì\ntrong DB)",
             fill="#E5E7EB", edge="#6B7280")

    # Branch: found
    _act_box(ax, 5.0, 6.7, 3.6, 0.9,
             "Generate temp password\n12 ký tự alphanum")
    _act_box(ax, 5.0, 5.6, 3.6, 0.9,
             "bcrypt.hash(temp_pw)\nUPDATE users.password_hash")

    _act_box(ax, 5.0, 4.4, 3.6, 0.9,
             "aiosmtplib.send(\nemail, subject, temp_pw)")
    _diamond(ax, 5.0, 3.1, 2.8, 1.1, "SMTP\nthành công?")

    _act_box(ax, 2.0, 1.9, 2.4, 0.9,
             "Log INFO\n\"email sent\"",
             fill="#DCFCE7", edge="#15803D")
    _act_box(ax, 8.0, 1.9, 2.4, 0.9,
             "Log WARNING\n\"smtp failed\"",
             fill="#FEE2E2", edge="#B91C1C")

    # Tất cả các nhánh hợp về cùng response
    _act_box(ax, 5.0, 0.85, 4.5, 0.7,
             "Trả HTTP 200 — message trung lập\n"
             "(fail-silent: không lộ tồn tại email / lỗi SMTP)",
             fill="#EFF6FF", edge="#1E3A8A")

    _act_end(ax, 5.0, 0.20)

    # Arrows
    _arrow(ax, (2.0, 12.62), (2.0, 12.35))
    _arrow(ax, (2.0, 11.65), (2.0, 11.35))
    _arrow(ax, (2.0, 10.65), (5.0, 10.30),
           label="(submit)", label_offset=(0.0, 0.10))
    _arrow(ax, (5.0, 9.50), (5.0, 9.15))
    _arrow(ax, (6.5, 8.6), (8.0, 8.0),
           label="No (không tìm thấy)",
           label_offset=(0.0, 0.30))
    _arrow(ax, (5.0, 8.05), (5.0, 7.15),
           label="Yes", label_offset=(0.20, 0.0))
    _arrow(ax, (5.0, 6.25), (5.0, 6.05))
    _arrow(ax, (5.0, 5.15), (5.0, 4.85))
    _arrow(ax, (5.0, 3.95), (5.0, 3.65))
    _arrow(ax, (3.5, 3.1), (2.5, 2.35),
           label="Yes", label_offset=(-0.15, 0.20))
    _arrow(ax, (6.5, 3.1), (7.5, 2.35),
           label="No (timeout/error)",
           label_offset=(0.20, 0.20))
    # 3 ngả gộp về response box
    _arrow(ax, (2.0, 1.45), (4.2, 1.10), color="#1E3A8A")
    _arrow(ax, (8.0, 1.45), (5.8, 1.10), color="#1E3A8A")
    _arrow(ax, (8.5, 7.0), (5.5, 1.10),
           color="#6B7280", rad=-0.30,
           label="(không tìm thấy)",
           label_offset=(0.50, 2.50))
    _arrow(ax, (5.0, 0.50), (5.0, 0.40))

    out = OUT / "act-forgot-password.png"
    fig.savefig(out, dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"[OK] {out}")


def main():
    seq_login()
    seq_pos_earn()
    seq_redeem()
    act_merchant_register()
    act_forgot_password()
    print("\n[ALL DONE]")


if __name__ == "__main__":
    main()
