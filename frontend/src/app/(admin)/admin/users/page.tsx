"use client";

import {
  Copy,
  Eye,
  Key,
  Lock,
  MoreVertical,
  Search,
  ShieldAlert,
  ShieldCheck,
  Store,
  Unlock,
  UserCog,
  UserRound,
  Users,
  X,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";

import {
  useAdminUserDetail,
  useAdminUsers,
  useResetAdminUserPassword,
  useUpdateAdminUser,
} from "@/lib/hooks/use-partner";
import { useMe } from "@/lib/hooks/use-me";
import type {
  AdminResetPasswordResponse,
  AdminUserRow,
} from "@/types/partner";

// SystemRole: giá trị field thực ở DB (User.system_role) — RoleEditModal
// chỉ chỉnh sửa được 3 giá trị này.
type SystemRole = "regular" | "admin" | "super_admin";

// RoleFilter: superset cho filter buttons — bổ sung owner/staff/customer
// suy ra từ Partner.owner_user_id và PartnerStaff.user_id.
type RoleFilter = SystemRole | "owner" | "staff" | "customer";

// Hiển thị 1 badge duy nhất theo thứ tự ưu tiên:
// super_admin > admin > chủ shop > nhân viên > khách hàng.
// Mục đích: ở /admin/users user có nhiều "vai trò" (vd vừa là owner partner A
// vừa là staff partner B) nhưng UI cần 1 badge để đọc nhanh.
function roleBadge(systemRole: string, partnerRole: string | null) {
  if (systemRole === "super_admin")
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-red-50 px-2.5 py-0.5 text-[11px] font-bold text-red-600">
        <ShieldAlert className="h-3 w-3" />
        Super Admin
      </span>
    );
  if (systemRole === "admin")
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-indigo-50 px-2.5 py-0.5 text-[11px] font-bold text-brand-indigo">
        <ShieldCheck className="h-3 w-3" />
        Admin
      </span>
    );
  if (partnerRole === "owner")
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-0.5 text-[11px] font-bold text-amber-700">
        <Store className="h-3 w-3" />
        Chủ shop
      </span>
    );
  if (partnerRole === "staff")
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-[11px] font-bold text-emerald-700">
        <UserCog className="h-3 w-3" />
        Nhân viên
      </span>
    );
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-0.5 text-[11px] font-medium text-slate-600">
      <UserRound className="h-3 w-3" />
      Khách hàng
    </span>
  );
}

function fmtDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

export default function AdminUsersPage() {
  const [search, setSearch] = useState("");
  const [role, setRole] = useState<RoleFilter | "">("");
  const [detailId, setDetailId] = useState<number | null>(null);
  const [roleEdit, setRoleEdit] = useState<AdminUserRow | null>(null);
  const [resetConfirm, setResetConfirm] = useState<AdminUserRow | null>(null);
  const [resetResult, setResetResult] =
    useState<AdminResetPasswordResponse | null>(null);
  const [lockTarget, setLockTarget] = useState<AdminUserRow | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { data: me } = useMe();
  const { data, isLoading } = useAdminUsers({
    q: search.trim() || undefined,
    role: role || undefined,
    limit: 100,
  });

  const updateMut = useUpdateAdminUser();
  const resetMut = useResetAdminUserPassword();

  const handleToggleActive = (u: AdminUserRow, reason?: string) => {
    setError(null);
    updateMut.mutate(
      { id: u.id, data: { is_active: !u.is_active, reason: reason ?? null } },
      {
        onError: (e: unknown) => {
          const msg =
            (e as { response?: { data?: { detail?: string } } })?.response
              ?.data?.detail ?? "Không cập nhật được";
          setError(msg);
        },
      },
    );
  };

  const handleResetPassword = () => {
    if (!resetConfirm) return;
    const target = resetConfirm;
    setResetConfirm(null);
    setError(null);
    resetMut.mutate(target.id, {
      onSuccess: (res) => setResetResult(res.data),
      onError: (e: unknown) => {
        const msg =
          (e as { response?: { data?: { detail?: string } } })?.response?.data
            ?.detail ?? "Không reset được mật khẩu";
        setError(msg);
      },
    });
  };

  return (
    <main className="px-4 py-5 md:px-8 md:py-6">
      <header className="flex flex-col items-start gap-4 md:flex-row md:justify-between">
        <div>
          <p className="text-[12px] text-slate-400">Hệ thống / Người dùng</p>
          <h1 className="mt-1 font-headline text-[32px] font-bold text-slate-800">
            Người dùng platform
          </h1>
          <p className="mt-1 text-[14px] text-slate-500">
            Tổng {data?.total ?? 0} tài khoản
          </p>
        </div>
      </header>

      {error && (
        <div className="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-[13px] text-red-700">
          {error}
        </div>
      )}

      <section className="mt-6 flex flex-col gap-3 rounded-2xl border border-slate-100 bg-white p-4 shadow-sm md:flex-row md:items-center">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute inset-y-0 left-3 my-auto h-5 w-5 text-slate-400" />
          <input
            type="text"
            placeholder="Tìm theo email, tên hoặc số điện thoại"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="block w-full rounded-xl border border-slate-200 bg-slate-50 py-3 pl-10 pr-3 outline-none transition-all placeholder:text-slate-400 focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo"
          />
        </div>
        <div className="flex flex-wrap gap-2">
          {(
            [
              { id: "", label: "Tất cả" },
              { id: "super_admin", label: "Super Admin" },
              { id: "admin", label: "Admin" },
              { id: "owner", label: "Chủ shop" },
              { id: "staff", label: "Nhân viên" },
              { id: "customer", label: "Khách hàng" },
            ] as const
          ).map((opt) => (
            <button
              key={opt.id || "all"}
              type="button"
              onClick={() => setRole(opt.id)}
              className={
                role === opt.id
                  ? "rounded-lg bg-brand-indigo px-4 py-2 text-[12px] font-bold text-white"
                  : "rounded-lg border border-slate-200 bg-white px-4 py-2 text-[12px] font-medium text-slate-600 hover:bg-slate-50"
              }
            >
              {opt.label}
            </button>
          ))}
        </div>
      </section>

      <section className="mt-6 overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-sm">
        {isLoading ? (
          <div className="flex min-h-[30vh] items-center justify-center text-slate-400">
            Đang tải danh sách...
          </div>
        ) : !data || data.items.length === 0 ? (
          <div className="flex flex-col items-center justify-center px-8 py-16 text-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-50 text-brand-indigo">
              <Users className="h-8 w-8" />
            </div>
            <p className="mt-4 font-headline text-[16px] font-bold text-slate-700">
              Không có người dùng nào
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[980px] text-left text-[13px]">
              <thead className="bg-slate-50 text-[11px] uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-6 py-3">Người dùng</th>
                  <th className="px-6 py-3">Liên hệ</th>
                  <th className="px-6 py-3">Vai trò</th>
                  <th className="px-6 py-3">Trạng thái</th>
                  <th className="px-6 py-3">Đăng ký</th>
                  <th className="px-6 py-3">Lần cuối</th>
                  <th className="px-6 py-3 text-right">Thao tác</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data.items.map((u: AdminUserRow) => {
                  const isSelf = me?.id === u.id;
                  return (
                    <tr key={u.id} className="hover:bg-slate-50">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-indigo-100 to-violet-100 font-bold text-brand-indigo">
                            {(u.full_name || u.email || "?")[0]?.toUpperCase()}
                          </div>
                          <div>
                            <p className="font-bold text-slate-800">
                              {u.full_name || "—"}
                              {isSelf && (
                                <span className="ml-2 rounded bg-amber-100 px-1.5 py-0.5 text-[10px] font-medium text-amber-700">
                                  bạn
                                </span>
                              )}
                            </p>
                            <p className="text-[11px] text-slate-400">
                              #{u.id}
                            </p>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-slate-600">
                        <p>{u.email || "—"}</p>
                        {u.phone && (
                          <p className="text-[11px] text-slate-400">
                            {u.phone}
                          </p>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        {roleBadge(u.system_role, u.partner_role ?? null)}
                      </td>
                      <td className="px-6 py-4">
                        {u.is_active ? (
                          <span className="inline-flex items-center rounded-full bg-green-50 px-2.5 py-0.5 text-[11px] font-medium text-green-700">
                            Hoạt động
                          </span>
                        ) : (
                          <span className="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-[11px] font-medium text-slate-500">
                            Khoá
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-slate-500">
                        {fmtDate(u.created_at)}
                      </td>
                      <td className="px-6 py-4 text-slate-500">
                        {fmtDate(u.last_login_at)}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <ActionMenu
                          user={u}
                          isSelf={isSelf}
                          onDetail={() => setDetailId(u.id)}
                          onToggleActive={() => setLockTarget(u)}
                          onEditRole={() => setRoleEdit(u)}
                          onResetPassword={() => setResetConfirm(u)}
                          busy={updateMut.isPending || resetMut.isPending}
                        />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {detailId != null && (
        <UserDetailModal
          userId={detailId}
          onClose={() => setDetailId(null)}
        />
      )}

      {roleEdit && (
        <RoleEditModal
          user={roleEdit}
          onClose={() => setRoleEdit(null)}
          onSubmit={(newRole) => {
            setError(null);
            updateMut.mutate(
              { id: roleEdit.id, data: { system_role: newRole } },
              {
                onSuccess: () => setRoleEdit(null),
                onError: (e: unknown) => {
                  const msg =
                    (e as { response?: { data?: { detail?: string } } })
                      ?.response?.data?.detail ?? "Không đổi được vai trò";
                  setError(msg);
                  setRoleEdit(null);
                },
              },
            );
          }}
          submitting={updateMut.isPending}
        />
      )}

      {lockTarget && (
        <LockReasonModal
          user={lockTarget}
          onCancel={() => setLockTarget(null)}
          onConfirm={(reason) => {
            const target = lockTarget;
            setLockTarget(null);
            handleToggleActive(target, reason);
          }}
          submitting={updateMut.isPending}
        />
      )}

      {resetConfirm && (
        <ConfirmModal
          title="Reset mật khẩu?"
          description={`Mật khẩu hiện tại của "${resetConfirm.full_name || resetConfirm.email || `#${resetConfirm.id}`}" sẽ bị thay bằng mật khẩu ngẫu nhiên. Gửi mật khẩu mới cho người dùng qua kênh an toàn.`}
          confirmLabel="Reset mật khẩu"
          onCancel={() => setResetConfirm(null)}
          onConfirm={handleResetPassword}
          tone="danger"
        />
      )}

      {resetResult && (
        <ResetResultModal
          data={resetResult}
          onClose={() => setResetResult(null)}
        />
      )}
    </main>
  );
}

function ActionMenu({
  user,
  isSelf,
  onDetail,
  onToggleActive,
  onEditRole,
  onResetPassword,
  busy,
}: {
  user: AdminUserRow;
  isSelf: boolean;
  onDetail: () => void;
  onToggleActive: () => void;
  onEditRole: () => void;
  onResetPassword: () => void;
  busy: boolean;
}) {
  const [open, setOpen] = useState(false);
  const wrapRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [open]);

  const close = () => setOpen(false);

  return (
    <div ref={wrapRef} className="relative inline-block text-left">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        disabled={busy}
        className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100 disabled:opacity-40"
        aria-label="Mở menu thao tác"
      >
        <MoreVertical className="h-4 w-4" />
      </button>

      {open && (
        <div className="absolute right-0 z-10 mt-1 w-52 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-lg">
          <button
            type="button"
            onClick={() => {
              close();
              onDetail();
            }}
            className="flex w-full items-center gap-2.5 px-3 py-2.5 text-left text-[12px] text-slate-700 hover:bg-slate-50"
          >
            <Eye className="h-4 w-4 text-slate-500" /> Xem chi tiết
          </button>
          <button
            type="button"
            onClick={() => {
              close();
              onToggleActive();
            }}
            disabled={isSelf}
            className="flex w-full items-center gap-2.5 px-3 py-2.5 text-left text-[12px] text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:text-slate-300 disabled:hover:bg-transparent"
            title={isSelf ? "Không thể tự khoá mình" : undefined}
          >
            {user.is_active ? (
              <>
                <Lock className="h-4 w-4 text-amber-600" />
                Khoá tài khoản
              </>
            ) : (
              <>
                <Unlock className="h-4 w-4 text-emerald-600" />
                Mở khoá
              </>
            )}
          </button>
          <button
            type="button"
            onClick={() => {
              close();
              onEditRole();
            }}
            disabled={isSelf}
            className="flex w-full items-center gap-2.5 px-3 py-2.5 text-left text-[12px] text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:text-slate-300 disabled:hover:bg-transparent"
            title={isSelf ? "Không thể tự đổi vai trò" : undefined}
          >
            <UserCog className="h-4 w-4 text-indigo-600" /> Đổi vai trò
          </button>
          <button
            type="button"
            onClick={() => {
              close();
              onResetPassword();
            }}
            disabled={isSelf}
            className="flex w-full items-center gap-2.5 border-t border-slate-100 px-3 py-2.5 text-left text-[12px] text-red-600 hover:bg-red-50 disabled:cursor-not-allowed disabled:text-slate-300 disabled:hover:bg-transparent"
            title={isSelf ? "Dùng trang tài khoản để đổi mật khẩu chính mình" : undefined}
          >
            <Key className="h-4 w-4" /> Reset mật khẩu
          </button>
        </div>
      )}
    </div>
  );
}

function UserDetailModal({
  userId,
  onClose,
}: {
  userId: number;
  onClose: () => void;
}) {
  const { data, isLoading } = useAdminUserDetail(userId);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 px-4 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl"
      >
        <div className="flex items-center justify-between">
          <h3 className="font-headline text-[18px] font-bold text-slate-800">
            Chi tiết người dùng
          </h3>
          <button
            type="button"
            onClick={onClose}
            className="flex h-8 w-8 items-center justify-center rounded-full text-slate-400 hover:bg-slate-100"
            aria-label="Đóng"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {isLoading || !data ? (
          <div className="flex min-h-[30vh] items-center justify-center text-slate-400">
            Đang tải...
          </div>
        ) : (
          <div className="mt-5 space-y-5">
            <div className="flex items-center gap-4">
              <div className="flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-indigo-100 to-violet-100 text-xl font-bold text-brand-indigo">
                {(data.full_name || data.email || "?")[0]?.toUpperCase()}
              </div>
              <div>
                <p className="font-headline text-[18px] font-bold text-slate-800">
                  {data.full_name || "—"}
                </p>
                <p className="text-[12px] text-slate-500">
                  #{data.id} • {data.email || "không có email"}
                </p>
                <div className="mt-1 flex items-center gap-2">
                  {roleBadge(data.system_role, data.partner_role ?? null)}
                  {data.is_active ? (
                    <span className="inline-flex rounded-full bg-green-50 px-2 py-0.5 text-[10px] font-medium text-green-700">
                      Hoạt động
                    </span>
                  ) : (
                    <span className="inline-flex rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-500">
                      Khoá
                    </span>
                  )}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 text-[12px]">
              <Info label="Số điện thoại" value={data.phone || "—"} />
              <Info label="Đăng ký" value={fmtDate(data.created_at)} />
              <Info
                label="Đăng nhập cuối"
                value={fmtDate(data.last_login_at)}
              />
            </div>

            <div>
              <p className="mb-2 font-headline text-[14px] font-bold text-slate-700">
                Membership ({data.memberships.length})
              </p>
              {data.memberships.length === 0 ? (
                <p className="rounded-lg bg-slate-50 px-3 py-4 text-center text-[12px] text-slate-500">
                  Chưa tham gia shop nào
                </p>
              ) : (
                <div className="overflow-hidden rounded-xl border border-slate-200">
                  <table className="w-full text-left text-[12px]">
                    <thead className="bg-slate-50 text-[10px] uppercase tracking-wide text-slate-500">
                      <tr>
                        <th className="px-3 py-2">Shop</th>
                        <th className="px-3 py-2">Hạng</th>
                        <th className="px-3 py-2 text-right">Điểm</th>
                        <th className="px-3 py-2">Tham gia</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {data.memberships.map((m) => (
                        <tr key={m.tenant_id}>
                          <td className="px-3 py-2">
                            <p className="font-medium text-slate-800">
                              {m.tenant_name}
                              {m.archived && (
                                <span className="ml-2 text-[10px] text-slate-400">
                                  (đã lưu trữ)
                                </span>
                              )}
                            </p>
                            <p className="text-[10px] text-slate-400">
                              {m.tenant_slug}
                            </p>
                          </td>
                          <td className="px-3 py-2 text-slate-600">
                            {m.current_tier_name || "—"}
                          </td>
                          <td className="px-3 py-2 text-right font-bold text-brand-orange">
                            {m.points_balance.toLocaleString("vi-VN")}
                          </td>
                          <td className="px-3 py-2 text-slate-500">
                            {fmtDate(m.joined_at)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-slate-50 px-3 py-2">
      <p className="text-[10px] uppercase tracking-wide text-slate-400">
        {label}
      </p>
      <p className="mt-0.5 font-medium text-slate-700">{value}</p>
    </div>
  );
}

function RoleEditModal({
  user,
  onClose,
  onSubmit,
  submitting,
}: {
  user: AdminUserRow;
  onClose: () => void;
  onSubmit: (role: SystemRole) => void;
  submitting: boolean;
}) {
  const [role, setRole] = useState<SystemRole>(user.system_role);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const options: { value: SystemRole; label: string; desc: string }[] = [
    {
      value: "regular",
      label: "Người dùng",
      desc: "Khách hàng / merchant thông thường",
    },
    {
      value: "admin",
      label: "Admin",
      desc: "Quản trị viên có quyền hạn chế",
    },
    {
      value: "super_admin",
      label: "Super Admin",
      desc: "Toàn quyền trên platform",
    },
  ];

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 px-4 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl"
      >
        <div className="flex items-center justify-between">
          <h3 className="font-headline text-[18px] font-bold text-slate-800">
            Đổi vai trò
          </h3>
          <button
            type="button"
            onClick={onClose}
            className="flex h-8 w-8 items-center justify-center rounded-full text-slate-400 hover:bg-slate-100"
            aria-label="Đóng"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <p className="mt-2 text-[12px] text-slate-500">
          Tài khoản:{" "}
          <span className="font-medium text-slate-700">
            {user.full_name || user.email || `#${user.id}`}
          </span>
        </p>

        <div className="mt-4 space-y-2">
          {options.map((opt) => (
            <label
              key={opt.value}
              className={`flex cursor-pointer items-start gap-3 rounded-xl border p-3 transition-colors ${
                role === opt.value
                  ? "border-brand-indigo bg-indigo-50"
                  : "border-slate-200 hover:bg-slate-50"
              }`}
            >
              <input
                type="radio"
                name="role"
                value={opt.value}
                checked={role === opt.value}
                onChange={() => setRole(opt.value)}
                className="mt-0.5"
              />
              <div>
                <p className="text-[13px] font-bold text-slate-800">
                  {opt.label}
                </p>
                <p className="text-[11px] text-slate-500">{opt.desc}</p>
              </div>
            </label>
          ))}
        </div>

        <div className="mt-6 flex gap-3">
          <button
            type="button"
            onClick={onClose}
            className="flex-1 rounded-xl border border-slate-200 bg-white py-3 font-headline text-[14px] font-bold text-slate-600 hover:bg-slate-50"
          >
            Huỷ
          </button>
          <button
            type="button"
            disabled={submitting || role === user.system_role}
            onClick={() => onSubmit(role)}
            className="flex-1 rounded-xl bg-gradient-to-r from-brand-indigo to-brand-violet py-3 font-headline text-[14px] font-bold text-white shadow-lg active:scale-[0.98] disabled:opacity-60"
          >
            {submitting ? "Đang lưu..." : "Xác nhận"}
          </button>
        </div>
      </div>
    </div>
  );
}

function ConfirmModal({
  title,
  description,
  confirmLabel,
  onCancel,
  onConfirm,
  tone = "primary",
}: {
  title: string;
  description: string;
  confirmLabel: string;
  onCancel: () => void;
  onConfirm: () => void;
  tone?: "primary" | "danger";
}) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onCancel();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onCancel]);

  const confirmClass =
    tone === "danger"
      ? "bg-gradient-to-r from-red-500 to-red-600"
      : "bg-gradient-to-r from-brand-indigo to-brand-violet";

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 px-4 backdrop-blur-sm"
      onClick={onCancel}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl"
      >
        <h3 className="font-headline text-[18px] font-bold text-slate-800">
          {title}
        </h3>
        <p className="mt-2 text-[13px] leading-relaxed text-slate-600">
          {description}
        </p>
        <div className="mt-6 flex gap-3">
          <button
            type="button"
            onClick={onCancel}
            className="flex-1 rounded-xl border border-slate-200 bg-white py-3 font-headline text-[14px] font-bold text-slate-600 hover:bg-slate-50"
          >
            Huỷ
          </button>
          <button
            type="button"
            onClick={onConfirm}
            className={`flex-1 rounded-xl py-3 font-headline text-[14px] font-bold text-white shadow-lg active:scale-[0.98] ${confirmClass}`}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

function LockReasonModal({
  user,
  onCancel,
  onConfirm,
  submitting,
}: {
  user: AdminUserRow;
  onCancel: () => void;
  onConfirm: (reason?: string) => void;
  submitting: boolean;
}) {
  const [reason, setReason] = useState("");

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onCancel();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onCancel]);

  const isLocking = user.is_active;
  const title = isLocking ? "Khoá tài khoản?" : "Mở khoá tài khoản?";
  const desc = isLocking
    ? `Người dùng "${user.full_name || user.email || `#${user.id}`}" sẽ không đăng nhập được nữa.`
    : `Người dùng "${user.full_name || user.email || `#${user.id}`}" sẽ được đăng nhập trở lại.`;
  const confirmClass = isLocking
    ? "bg-gradient-to-r from-red-500 to-red-600"
    : "bg-gradient-to-r from-emerald-500 to-emerald-600";

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 px-4 backdrop-blur-sm"
      onClick={onCancel}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl"
      >
        <h3 className="font-headline text-[18px] font-bold text-slate-800">
          {title}
        </h3>
        <p className="mt-2 text-[13px] leading-relaxed text-slate-600">
          {desc}
        </p>
        <div className="mt-4">
          <label className="block text-[12px] font-medium text-slate-600 mb-1">
            Lý do <span className="text-slate-400">(tùy chọn)</span>
          </label>
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            maxLength={500}
            rows={3}
            placeholder="Nhập lý do khoá / mở khoá..."
            className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo resize-none"
          />
          <p className="mt-1 text-[11px] text-slate-400 text-right">
            {reason.length}/500
          </p>
        </div>
        <div className="mt-5 flex gap-3">
          <button
            type="button"
            onClick={onCancel}
            className="flex-1 rounded-xl border border-slate-200 bg-white py-3 font-headline text-[14px] font-bold text-slate-600 hover:bg-slate-50"
          >
            Huỷ
          </button>
          <button
            type="button"
            disabled={submitting}
            onClick={() => onConfirm(reason.trim() || undefined)}
            className={`flex-1 rounded-xl py-3 font-headline text-[14px] font-bold text-white shadow-lg active:scale-[0.98] disabled:opacity-60 ${confirmClass}`}
          >
            {submitting ? "Đang lưu..." : "Xác nhận"}
          </button>
        </div>
      </div>
    </div>
  );
}

function ResetResultModal({
  data,
  onClose,
}: {
  data: AdminResetPasswordResponse;
  onClose: () => void;
}) {
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(data.temporary_password);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 px-4 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl"
      >
        <h3 className="font-headline text-[18px] font-bold text-slate-800">
          Mật khẩu tạm thời
        </h3>
        <p className="mt-2 text-[12px] text-slate-500">
          Mật khẩu này chỉ hiển thị một lần. Hãy sao chép và gửi cho người dùng
          qua kênh an toàn.
        </p>

        <div className="mt-4 flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 p-3">
          <code className="flex-1 break-all font-mono text-[16px] font-bold text-slate-800">
            {data.temporary_password}
          </code>
          <button
            type="button"
            onClick={copy}
            className="flex items-center gap-1 rounded-lg bg-brand-indigo px-3 py-2 text-[12px] font-bold text-white hover:opacity-90"
          >
            <Copy className="h-4 w-4" />
            {copied ? "Đã chép" : "Chép"}
          </button>
        </div>

        <button
          type="button"
          onClick={onClose}
          className="mt-6 w-full rounded-xl bg-slate-100 py-3 font-headline text-[14px] font-bold text-slate-700 hover:bg-slate-200"
        >
          Đóng
        </button>
      </div>
    </div>
  );
}
