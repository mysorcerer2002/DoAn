# Vocabulary of audit log action constants.
# Keep in sync with the CHECK constraint in the audit_logs migration.

ACTION_USER_LOCK = "user_lock"
ACTION_USER_UNLOCK = "user_unlock"
ACTION_USER_ROLE_CHANGE = "user_role_change"

ACTION_PARTNER_APPROVE = "partner_approve"
ACTION_PARTNER_REJECT = "partner_reject"
ACTION_PARTNER_SUSPEND = "partner_suspend"
ACTION_PARTNER_UNSUSPEND = "partner_unsuspend"
