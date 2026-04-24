"""rename tenant to partner

Revision ID: 162e25afc796
Revises: b0c1d2e3f4a5
Create Date: 2026-04-24 12:00:00

Phase 1 của Partner rename plan (2026-04-24-partner-rename-and-discovery-ux.md).
Đổi tên bảng tenants→partners, tenant_staff→partner_staff,
tenant_authorizations→partner_authorizations,
tenant_settings_audit→partner_settings_audit;
đổi cột tenant_id→partner_id trên tất cả bảng liên quan;
đổi tên index, constraint, sequence có chứa "tenant" → "partner".

Migration này chưa được apply — sẽ chạy ở Phase 2 Step 2.5.
"""
from alembic import op

revision = "162e25afc796"
down_revision = "b0c1d2e3f4a5"
branch_labels = None
depends_on = None


TABLE_RENAMES = [
    ("tenants",                "partners"),
    ("tenant_staff",           "partner_staff"),
    ("tenant_authorizations",  "partner_authorizations"),
    ("tenant_settings_audit",  "partner_settings_audit"),
]

COLUMN_RENAMES = [
    ("memberships",              "tenant_id", "partner_id"),
    ("transactions",             "tenant_id", "partner_id"),
    ("point_ledger",             "tenant_id", "partner_id"),
    ("point_rules",              "tenant_id", "partner_id"),
    ("tiers",                    "tenant_id", "partner_id"),
    ("rewards",                  "tenant_id", "partner_id"),
    ("redemptions",              "tenant_id", "partner_id"),
    ("vouchers",                 "tenant_id", "partner_id"),
    ("campaigns",                "tenant_id", "partner_id"),
    ("campaign_issuances",       "tenant_id", "partner_id"),
    ("campaign_service_fees",    "tenant_id", "partner_id"),
    ("notifications",            "tenant_id", "partner_id"),
    ("partner_staff",            "tenant_id", "partner_id"),
    ("partner_authorizations",   "tenant_id", "partner_id"),
    ("partner_settings_audit",   "tenant_id", "partner_id"),
]

# Indexes that are NOT backed by a pg_constraint entry.
# Includes: ix_* (all plain indexes), partial unique indexes (uq_* / ux_*
# that appear only in pg_indexes, not in pg_constraint).
# PK and constraint-backed UQ go in CONSTRAINT_RENAMES — PG cascades
# the backing index name automatically when the constraint is renamed.
INDEX_RENAMES = [
    # ix_* on non-renamed tables
    ("ix_campaign_issuances_tenant_active",         "ix_campaign_issuances_partner_active"),
    ("ix_campaign_service_fees_tenant_status",       "ix_campaign_service_fees_partner_status"),
    ("ix_campaigns_tenant_active",                   "ix_campaigns_partner_active"),
    ("ix_memberships_tenant_id",                     "ix_memberships_partner_id"),
    ("ix_point_ledger_tenant_created",               "ix_point_ledger_partner_created"),
    ("ix_point_rules_tenant_id",                     "ix_point_rules_partner_id"),
    ("ix_redemptions_tenant_status",                 "ix_redemptions_partner_status"),
    ("ix_rewards_tenant_id",                         "ix_rewards_partner_id"),
    ("ix_tiers_tenant_id",                           "ix_tiers_partner_id"),
    ("ix_tiers_tenant_min_points",                   "ix_tiers_partner_min_points"),
    ("ix_transactions_tenant_created",               "ix_transactions_partner_created"),
    # ix_* on renamed tables (use current PG name — already renamed above)
    ("ix_tenant_settings_audit_tenant_id",           "ix_partner_settings_audit_partner_id"),
    ("ix_tenant_settings_audit_user_id",             "ix_partner_settings_audit_user_id"),
    ("ix_tenant_staff_tenant_id",                    "ix_partner_staff_partner_id"),
    ("ix_tenant_staff_user_id",                      "ix_partner_staff_user_id"),
    ("ix_tenants_category",                          "ix_partners_category"),
    ("ix_tenants_owner_user_id",                     "ix_partners_owner_user_id"),
    ("ix_tenants_slug",                              "ix_partners_slug"),
    # partial unique indexes (not constraint-backed → ALTER INDEX, not ALTER CONSTRAINT)
    ("uq_campaigns_tenant_template_active_pending",  "uq_campaigns_partner_template_active_pending"),
    ("uq_point_rules_tenant_active",                 "uq_point_rules_partner_active"),
    ("ux_tenant_authorizations_active_per_campaign", "ux_partner_authorizations_active_per_campaign"),
]

# Constraint-backed entries (PK, UQ, FK, CK).
# PG cascades PK/UQ backing index name when constraint is renamed — no
# separate ALTER INDEX needed.
# "table_after_rename" = table name AFTER TABLE_RENAMES has run (use new
# name for the 4 renamed tables; unchanged name for everything else).
CONSTRAINT_RENAMES = [
    # PK (4)
    ("partners",              "pk_tenants",               "pk_partners"),
    ("partner_staff",         "pk_tenant_staff",          "pk_partner_staff"),
    ("partner_authorizations","pk_tenant_authorizations", "pk_partner_authorizations"),
    ("partner_settings_audit","pk_tenant_settings_audit", "pk_partner_settings_audit"),
    # UQ constraint-backed (4)
    ("memberships",           "uq_memberships_tenant_user",        "uq_memberships_partner_user"),
    ("redemptions",           "uq_redemptions_tenant_code",        "uq_redemptions_partner_code"),
    ("partner_staff",         "uq_tenant_staff_tenant_user",       "uq_partner_staff_partner_user"),
    ("vouchers",              "uq_vouchers_tenant_code",           "uq_vouchers_partner_code"),
    # CK on tenant_authorizations (5) — table now named partner_authorizations
    ("partner_authorizations", "ck_tenant_authorizations_ck_tenant_authorizations_per_c_ca9d",    "ck_partner_authorizations_ck_partner_authorizations_per_c_ca9d"),
    ("partner_authorizations", "ck_tenant_authorizations_ck_tenant_authorizations_retention_10y", "ck_partner_authorizations_ck_partner_authorizations_retention_10y"),
    ("partner_authorizations", "ck_tenant_authorizations_ck_tenant_authorizations_scope",         "ck_partner_authorizations_ck_partner_authorizations_scope"),
    ("partner_authorizations", "ck_tenant_authorizations_ck_tenant_authorizations_signa_5497",    "ck_partner_authorizations_ck_partner_authorizations_signa_5497"),
    ("partner_authorizations", "ck_tenant_authorizations_ck_tenant_authorizations_valid_window",  "ck_partner_authorizations_ck_partner_authorizations_valid_window"),
    # CK on tenants (1) — table now named partners
    ("partners",              "ck_tenants_ck_tenants_category_valid", "ck_partners_ck_partners_category_valid"),
    # FK where the tenant appears in the FK column name (column renamed to partner_id)
    ("campaign_issuances",   "fk_campaign_issuances_tenant_id_tenants",      "fk_campaign_issuances_partner_id_partners"),
    ("campaign_service_fees","fk_campaign_service_fees_tenant_id_tenants",   "fk_campaign_service_fees_partner_id_partners"),
    ("campaigns",            "fk_campaigns_tenant_id_tenants",               "fk_campaigns_partner_id_partners"),
    ("memberships",          "fk_memberships_tenant_id_tenants",             "fk_memberships_partner_id_partners"),
    ("notifications",        "fk_notifications_tenant_id_tenants",           "fk_notifications_partner_id_partners"),
    ("point_ledger",         "fk_point_ledger_tenant_id_tenants",            "fk_point_ledger_partner_id_partners"),
    ("point_rules",          "fk_point_rules_tenant_id_tenants",             "fk_point_rules_partner_id_partners"),
    ("redemptions",          "fk_redemptions_tenant_id_tenants",             "fk_redemptions_partner_id_partners"),
    ("rewards",              "fk_rewards_tenant_id_tenants",                 "fk_rewards_partner_id_partners"),
    ("tiers",                "fk_tiers_tenant_id_tenants",                   "fk_tiers_partner_id_partners"),
    ("transactions",         "fk_transactions_tenant_id_tenants",            "fk_transactions_partner_id_partners"),
    ("vouchers",             "fk_vouchers_tenant_id_tenants",                "fk_vouchers_partner_id_partners"),
    # FK on renamed tables where only the table-name segment changes (not column)
    ("partner_authorizations", "fk_tenant_authorizations_campaign_id_campaigns",     "fk_partner_authorizations_campaign_id_campaigns"),
    ("partner_authorizations", "fk_tenant_authorizations_signed_by_user_id_users",   "fk_partner_authorizations_signed_by_user_id_users"),
    ("partner_authorizations", "fk_tenant_authorizations_tenant_id_tenants",         "fk_partner_authorizations_partner_id_partners"),
    ("partner_settings_audit", "fk_tenant_settings_audit_tenant_id_tenants",         "fk_partner_settings_audit_partner_id_partners"),
    ("partner_settings_audit", "fk_tenant_settings_audit_user_id_users",             "fk_partner_settings_audit_user_id_users"),
    ("partner_staff",          "fk_tenant_staff_tenant_id_tenants",                  "fk_partner_staff_partner_id_partners"),
    ("partner_staff",          "fk_tenant_staff_user_id_users",                      "fk_partner_staff_user_id_users"),
    # FK on partners (was tenants)
    ("partners",               "fk_tenants_owner_user_id_users",                     "fk_partners_owner_user_id_users"),
]

SEQUENCE_RENAMES = [
    ("tenants_id_seq",                "partners_id_seq"),
    ("tenant_staff_id_seq",           "partner_staff_id_seq"),
    ("tenant_authorizations_id_seq",  "partner_authorizations_id_seq"),
    ("tenant_settings_audit_id_seq",  "partner_settings_audit_id_seq"),
]


def upgrade() -> None:
    op.execute("SET lock_timeout = '10s'")

    for old, new in TABLE_RENAMES:
        op.rename_table(old, new)

    for table, old_col, new_col in COLUMN_RENAMES:
        op.alter_column(table, old_col, new_column_name=new_col)

    for old, new in INDEX_RENAMES:
        op.execute(f"ALTER INDEX IF EXISTS {old} RENAME TO {new}")

    for table, old, new in CONSTRAINT_RENAMES:
        op.execute(f"ALTER TABLE {table} RENAME CONSTRAINT {old} TO {new}")

    for old, new in SEQUENCE_RENAMES:
        op.execute(f"ALTER SEQUENCE IF EXISTS {old} RENAME TO {new}")


def downgrade() -> None:
    op.execute("SET lock_timeout = '10s'")

    for old, new in SEQUENCE_RENAMES:
        op.execute(f"ALTER SEQUENCE IF EXISTS {new} RENAME TO {old}")

    for table, old, new in CONSTRAINT_RENAMES:
        op.execute(f"ALTER TABLE {table} RENAME CONSTRAINT {new} TO {old}")

    for old, new in INDEX_RENAMES:
        op.execute(f"ALTER INDEX IF EXISTS {new} RENAME TO {old}")

    for table, old_col, new_col in COLUMN_RENAMES:
        op.alter_column(table, new_col, new_column_name=old_col)

    for old, new in TABLE_RENAMES:
        op.rename_table(new, old)
