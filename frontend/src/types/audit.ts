export interface AuditLogResponse {
  id: number;
  actor_user_id: number | null;
  actor_email: string | null;
  action: string;
  target_type: "user" | "partner";
  target_id: number | null;
  target_label: string | null;
  reason: string | null;
  before_snapshot: Record<string, unknown> | null;
  after_snapshot: Record<string, unknown> | null;
  created_at: string;
}

export interface AuditLogListResponse {
  items: AuditLogResponse[];
  total: number;
}

export type AuditAction =
  | "user_lock"
  | "user_unlock"
  | "user_role_change"
  | "partner_approve"
  | "partner_reject"
  | "partner_suspend"
  | "partner_unsuspend";
