"""Vẽ ERD 9 entity MVP bằng matplotlib.

Mỗi entity gộp sẵn created_at/updated_at từ TimestampMixin (Base/TimestampMixin
không phải bảng riêng — đó là Python mixin chỉ kế thừa các cột timestamp).
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = Path(__file__).parent / "uml"
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.family"] = "DejaVu Sans"

# --- Entity definitions ----------------------------------------------------
# Mỗi entity: tên bảng, fields. PK ⇒ "🔑", FK ⇒ "🔗" (sẽ render bằng prefix
# text vì matplotlib không hỗ trợ emoji ổn — dùng "PK"/"FK").
ENTITIES = {
    "users": dict(
        x=1, y=10, w=3.6, h=3.0,
        title="User (users)",
        fields=[
            "PK  id",
            "    email  (uniq)",
            "    phone  (uniq)",
            "    password_hash",
            "    full_name",
            "    birthday",
            "    system_role",
            "    points_balance ≥ 0",
            "    is_active",
            "    last_login_at",
            "    created_at",
            "    updated_at",
        ],
    ),
    "partners": dict(
        x=6.2, y=10, w=3.6, h=3.0,
        title="Partner (partners)",
        fields=[
            "PK  id",
            "FK  owner_user_id → users",
            "    name",
            "    slug  (uniq)",
            "    status",
            "    category",
            "    description / address",
            "    contact_phone / email",
            "    activated_at",
            "    created_at",
            "    updated_at",
        ],
    ),
    "partner_staff": dict(
        x=11.4, y=10, w=3.4, h=2.4,
        title="PartnerStaff (partner_staff)",
        fields=[
            "PK  id",
            "FK  partner_id → partners",
            "FK  user_id    → users (uniq)",
            "    is_active",
            "    created_at",
            "    updated_at",
        ],
    ),
    "memberships": dict(
        x=1, y=5.6, w=3.6, h=2.7,
        title="Membership (memberships)",
        fields=[
            "PK  id",
            "FK  partner_id → partners",
            "FK  user_id    → users",
            "    lifetime_earned ≥ 0",
            "    is_active",
            "    joined_at",
            "    last_activity_at",
            "    UNIQUE(partner_id,user_id)",
            "    created_at",
            "    updated_at",
        ],
    ),
    "rewards": dict(
        x=6.2, y=5.6, w=3.6, h=2.7,
        title="Reward (rewards)",
        fields=[
            "PK  id",
            "FK  partner_id → partners",
            "    name / description",
            "    image_url",
            "    points_cost > 0",
            "    stock (NULL = ∞)",
            "    offer_type / value / label",
            "    valid_until / terms",
            "    deleted_at",
            "    created_at",
            "    updated_at",
        ],
    ),
    "redemptions": dict(
        x=11.4, y=5.6, w=3.4, h=2.7,
        title="Redemption (redemptions)",
        fields=[
            "PK  id",
            "FK  partner_id → partners",
            "FK  user_id    → users",
            "FK  reward_id  → rewards",
            "    points_spent > 0",
            "    redemption_code (8)",
            "    status (PEN/USED/EXP)",
            "    redeemed_at / used_at",
            "    expires_at",
            "    created_at",
            "    updated_at",
        ],
    ),
    "transactions": dict(
        x=1, y=1.0, w=3.6, h=2.4,
        title="Transaction (transactions)",
        fields=[
            "PK  id",
            "FK  partner_id    → partners",
            "FK  membership_id → memberships",
            "    gross_amount / net_amount",
            "    points_earned",
            "    method / receipt_code",
            "    note",
            "    created_at",
            "    updated_at",
        ],
    ),
    "point_ledger": dict(
        x=6.2, y=1.0, w=3.6, h=2.4,
        title="PointLedger (point_ledger)\nappend-only — trigger chặn UPDATE/DELETE",
        fields=[
            "PK  id",
            "FK  partner_id    → partners",
            "FK  user_id       → users",
            "FK  actor_user_id → users (n)",
            "    delta",
            "    reason  (earn/redeem/adjust/expire/refund)",
            "    ref_type / ref_id",
            "    balance_after ≥ 0",
            "    created_at",
            "    updated_at",
        ],
    ),
    "login_log": dict(
        x=11.4, y=1.0, w=3.4, h=2.0,
        title="LoginLog (login_log)\naudit đăng nhập",
        fields=[
            "PK  id  (BigInt)",
            "FK  user_id → users (n)",
            "    identifier",
            "    ip / user_agent",
            "    success / failure_reason",
            "    created_at",
        ],
    ),
}

# --- Relationships (from-key, to-key, label) -------------------------------
RELATIONSHIPS = [
    ("partners", "users", "owner"),
    ("partner_staff", "partners", "1—N"),
    ("partner_staff", "users", "1—1"),
    ("memberships", "partners", "1—N"),
    ("memberships", "users", "1—N"),
    ("rewards", "partners", "1—N"),
    ("redemptions", "partners", "1—N"),
    ("redemptions", "users", "1—N"),
    ("redemptions", "rewards", "1—N"),
    ("transactions", "partners", "1—N"),
    ("transactions", "memberships", "1—N"),
    ("point_ledger", "partners", "1—N"),
    ("point_ledger", "users", "1—N"),
    ("login_log", "users", "1—N"),
]


def _draw_entity(ax, name, spec):
    x, y = spec["x"], spec["y"]
    w, h = spec["w"], spec["h"]
    title = spec["title"]
    fields = spec["fields"]

    # Outer box
    box = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.02,rounding_size=0.08",
        linewidth=1.4,
        edgecolor="#1E3A8A",
        facecolor="#EFF6FF",
    )
    ax.add_patch(box)

    # Title bar
    title_h = 0.5 if "\n" not in title else 0.7
    title_bar = FancyBboxPatch(
        (x, y + h - title_h),
        w,
        title_h,
        boxstyle="round,pad=0.0,rounding_size=0.08",
        linewidth=0,
        edgecolor="none",
        facecolor="#1E3A8A",
    )
    ax.add_patch(title_bar)
    ax.text(
        x + w / 2,
        y + h - title_h / 2,
        title,
        ha="center",
        va="center",
        color="white",
        fontsize=9,
        fontweight="bold",
    )

    # Field list
    line_h = (h - title_h - 0.15) / max(len(fields), 1)
    for i, f in enumerate(fields):
        ty = y + h - title_h - 0.10 - (i + 0.5) * line_h
        # PK fields bold
        weight = "bold" if f.startswith("PK") else "normal"
        color = "#7C2D12" if f.startswith("FK") else "#111827"
        if f.startswith("PK"):
            color = "#065F46"
        ax.text(
            x + 0.12,
            ty,
            f,
            ha="left",
            va="center",
            fontsize=7.5,
            family="monospace",
            color=color,
            fontweight=weight,
        )


def _entity_anchor(spec, side):
    x, y, w, h = spec["x"], spec["y"], spec["w"], spec["h"]
    if side == "top":
        return (x + w / 2, y + h)
    if side == "bottom":
        return (x + w / 2, y)
    if side == "left":
        return (x, y + h / 2)
    if side == "right":
        return (x + w, y + h / 2)
    raise ValueError(side)


def _best_anchors(a, b):
    """Pick anchors on closest sides."""
    ax_, ay = a["x"] + a["w"] / 2, a["y"] + a["h"] / 2
    bx_, by = b["x"] + b["w"] / 2, b["y"] + b["h"] / 2
    dx, dy = bx_ - ax_, by - ay
    if abs(dx) > abs(dy):
        return ("right", "left") if dx > 0 else ("left", "right")
    return ("top", "bottom") if dy > 0 else ("bottom", "top")


def _draw_relationship(ax, src, dst, label):
    sa, da = _best_anchors(src, dst)
    p1 = _entity_anchor(src, sa)
    p2 = _entity_anchor(dst, da)
    arrow = FancyArrowPatch(
        p1,
        p2,
        arrowstyle="-|>",
        mutation_scale=12,
        linewidth=1.0,
        color="#1F2937",
        connectionstyle="arc3,rad=0.0",
    )
    ax.add_patch(arrow)
    mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
    ax.text(
        mx,
        my,
        label,
        ha="center",
        va="center",
        fontsize=7,
        color="#1F2937",
        bbox=dict(facecolor="white", edgecolor="none", pad=0.5, alpha=0.85),
    )


def render_erd():
    fig, ax = plt.subplots(figsize=(15, 9))
    ax.set_xlim(0, 15.5)
    ax.set_ylim(0, 14)
    ax.axis("off")

    ax.text(
        7.75,
        13.5,
        "ERD — 9 thực thể MVP loyalty platform",
        ha="center",
        va="center",
        fontsize=14,
        fontweight="bold",
        color="#1E3A8A",
    )
    ax.text(
        7.75,
        13.05,
        "created_at / updated_at được kế thừa từ TimestampMixin (mixin Python — không phải bảng riêng)",
        ha="center",
        va="center",
        fontsize=8.5,
        style="italic",
        color="#374151",
    )

    for name, spec in ENTITIES.items():
        _draw_entity(ax, name, spec)

    for src_name, dst_name, label in RELATIONSHIPS:
        _draw_relationship(ax, ENTITIES[src_name], ENTITIES[dst_name], label)

    out = OUT / "erd.png"
    fig.savefig(out, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"[OK] {out}")


if __name__ == "__main__":
    render_erd()
