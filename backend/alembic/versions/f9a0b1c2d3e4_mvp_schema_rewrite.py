"""MVP schema rewrite (Phase 5)

Revision ID: f9a0b1c2d3e4
Revises: e7f8a9b0c1d2
Create Date: 2026-04-26 14:00:00.000000

Schema rewrite cuối cùng theo spec docs/superpowers/specs/cleanup-mvp-2026-04-25.md M5:
- users.points_balance (global wallet) ADD + backfill từ point_ledger.
- memberships RENAME total_points_earned → lifetime_earned, DROP points_balance + archived_at.
- point_ledger ADD user_id (backfill từ memberships), DROP membership_id; phải drop+restore
  trigger no_update_or_delete_point_ledger để backfill UPDATE chạy được.
- redemptions ADD user_id + snapshot_image_url, DROP membership_id.
- CREATE TABLE voucher_templates (Hybrid C+i — Admin upload PNG khung + JSONB layout).
- rewards expand columns: template_id, offer_type, offer_value, offer_label, valid_until,
  terms + CheckConstraint validate offer_value theo offer_type.

One-way migration (downgrade NotImplementedError) vì backfill có thể mất signup_bonus.
"""

import sqlalchemy as sa
from alembic import op


revision = "f9a0b1c2d3e4"
down_revision = "e7f8a9b0c1d2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. Drop append-only trigger để backfill point_ledger.user_id chạy được ──
    op.execute(
        "DROP TRIGGER IF EXISTS no_update_or_delete_point_ledger ON point_ledger;"
    )

    # ── 2. point_ledger: ADD user_id, backfill, NOT NULL, FK, DROP membership_id ──
    op.add_column(
        "point_ledger",
        sa.Column("user_id", sa.Integer(), nullable=True),
    )
    op.execute(
        """
        UPDATE point_ledger
        SET user_id = m.user_id
        FROM memberships m
        WHERE m.id = point_ledger.membership_id
        """
    )
    op.alter_column("point_ledger", "user_id", nullable=False)
    op.create_foreign_key(
        "fk_point_ledger_user_id_users",
        "point_ledger",
        "users",
        ["user_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_point_ledger_user_created",
        "point_ledger",
        ["user_id", "created_at"],
    )
    # Drop FK + index trước khi drop column (Postgres auto-cascade với DROP COLUMN
    # nhưng explicit để rõ ràng + naming convention).
    op.drop_index("ix_point_ledger_membership_created", table_name="point_ledger")
    op.drop_constraint(
        "fk_point_ledger_membership_id_memberships",
        "point_ledger",
        type_="foreignkey",
    )
    op.drop_column("point_ledger", "membership_id")

    # ── 3. Restore trigger (giữ nguyên function prevent_point_ledger_mutation) ──
    op.execute(
        """
        CREATE TRIGGER no_update_or_delete_point_ledger
        BEFORE UPDATE OR DELETE ON point_ledger
        FOR EACH ROW EXECUTE FUNCTION prevent_point_ledger_mutation();
        """
    )

    # ── 4. users.points_balance + backfill từ ledger sum ──
    op.add_column(
        "users",
        sa.Column(
            "points_balance",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.execute(
        """
        UPDATE users
        SET points_balance = COALESCE(
            (SELECT SUM(delta) FROM point_ledger WHERE point_ledger.user_id = users.id),
            0
        )
        """
    )

    # ── 5. memberships: RENAME total_points_earned → lifetime_earned + DROP cols ──
    # Tên constraint thực tế trong DB bị double-prefix do convention bug
    # (xem memory project_constraint_naming_convention_debt.md).
    op.execute(
        "ALTER TABLE memberships DROP CONSTRAINT ck_memberships_ck_memberships_total_nonneg"
    )
    op.execute(
        "ALTER TABLE memberships DROP CONSTRAINT ck_memberships_ck_memberships_balance_nonneg"
    )
    op.alter_column(
        "memberships", "total_points_earned", new_column_name="lifetime_earned"
    )
    # Dùng raw SQL để giữ exact tên (tránh convention double-prefix sinh
    # `ck_memberships_ck_memberships_lifetime_nonneg` lệch với suffix sạch).
    op.execute(
        "ALTER TABLE memberships ADD CONSTRAINT ck_memberships_lifetime_nonneg "
        "CHECK (lifetime_earned >= 0)"
    )
    op.drop_column("memberships", "points_balance")
    op.drop_column("memberships", "archived_at")

    # ── 6. redemptions: ADD user_id (backfill) + snapshot_image_url, DROP membership_id ──
    op.add_column(
        "redemptions",
        sa.Column("user_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "redemptions",
        sa.Column("snapshot_image_url", sa.String(length=500), nullable=True),
    )
    op.execute(
        """
        UPDATE redemptions
        SET user_id = m.user_id
        FROM memberships m
        WHERE m.id = redemptions.membership_id
        """
    )
    op.alter_column("redemptions", "user_id", nullable=False)
    op.create_foreign_key(
        "fk_redemptions_user_id_users",
        "redemptions",
        "users",
        ["user_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index("ix_redemptions_user_id", "redemptions", ["user_id"])
    op.drop_index("ix_redemptions_membership_id", table_name="redemptions")
    op.drop_constraint(
        "fk_redemptions_membership_id_memberships",
        "redemptions",
        type_="foreignkey",
    )
    op.drop_column("redemptions", "membership_id")

    # ── 7. CREATE TABLE voucher_templates ──
    op.create_table(
        "voucher_templates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("category", sa.String(length=20), nullable=False),
        sa.Column("frame_image_url", sa.String(length=500), nullable=False),
        sa.Column("text_layout_config", sa.JSON(), nullable=False),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        # Pass suffix; convention sẽ prepend `ck_voucher_templates_` → final
        # `ck_voucher_templates_valid_category`. (Pattern khớp với debt hiện hữu
        # nhưng không double-prefix vì model mới sẽ truyền suffix-only.)
        sa.CheckConstraint(
            "category IN ('CAFE','FOOD','RETAIL','BEAUTY','SEASONAL','OTHER')",
            name="valid_category",
        ),
    )

    # ── 8. rewards: ADD template_id + offer_* + valid_until + terms ──
    op.add_column(
        "rewards",
        sa.Column("template_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "rewards",
        sa.Column(
            "offer_type",
            sa.String(length=20),
            nullable=False,
            server_default="PERCENT_DISCOUNT",
        ),
    )
    op.add_column("rewards", sa.Column("offer_value", sa.Integer(), nullable=True))
    op.add_column(
        "rewards",
        sa.Column(
            "offer_label",
            sa.String(length=120),
            nullable=False,
            server_default="",
        ),
    )
    op.add_column("rewards", sa.Column("valid_until", sa.Date(), nullable=True))
    op.add_column("rewards", sa.Column("terms", sa.Text(), nullable=True))
    op.create_foreign_key(
        "fk_rewards_template_id_voucher_templates",
        "rewards",
        "voucher_templates",
        ["template_id"],
        ["id"],
        ondelete="SET NULL",
    )
    # Backfill offer_label = name cho rows hiện có để không trống
    op.execute(
        "UPDATE rewards SET offer_label = name WHERE offer_label = '' OR offer_label IS NULL"
    )
    # Backfill offer_type='ITEM_GIFT' cho rows hiện có (offer_value vẫn NULL).
    # Default 'PERCENT_DISCOUNT' khi ADD COLUMN sẽ vi phạm CK
    # (PERCENT_DISCOUNT cần offer_value BETWEEN 1..100). Reward seed/demo hiện
    # tại đều là quà hiện vật (cafe, sách...) → ITEM_GIFT semantically đúng;
    # admin chỉnh sang PERCENT/FIXED sau nếu cần.
    op.execute(
        "UPDATE rewards SET offer_type = 'ITEM_GIFT' WHERE offer_value IS NULL"
    )
    # Drop server_default sau khi backfill (chỉ cần default lúc ADD COLUMN)
    op.alter_column("rewards", "offer_label", server_default=None)
    op.alter_column("rewards", "offer_type", server_default=None)
    # Raw SQL để tránh convention double-prefix sinh `ck_rewards_ck_rewards_...`
    op.execute(
        "ALTER TABLE rewards ADD CONSTRAINT ck_rewards_offer_value_matches_type CHECK ("
        "(offer_type = 'PERCENT_DISCOUNT' AND offer_value BETWEEN 1 AND 100) OR "
        "(offer_type = 'FIXED_DISCOUNT'   AND offer_value > 0) OR "
        "(offer_type = 'ITEM_GIFT'        AND offer_value IS NULL)"
        ")"
    )


def downgrade() -> None:
    raise NotImplementedError(
        "Migration f9a0b1c2d3e4 (MVP schema rewrite Phase 5) là one-way: backfill "
        "user_id từ memberships có thể không invertible (memberships có thể bị "
        "modify sau migration). Restore từ DB snapshot pre-Phase-5 nếu cần rollback."
    )
