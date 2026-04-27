"use client";

import {
  Ban,
  Check,
  Coins,
  Crown,
  Download,
  Eye,
  Loader2,
  Pencil,
  Search,
  Users,
  X,
} from "lucide-react";
import { useMemo, useState } from "react";

import {
  useAdjustMemberPoints,
  useMemberLedger,
  useMembers,
  useUpdateMember,
} from "@/lib/hooks/use-partner";
import type { MemberResponse } from "@/types/partner";

function formatRelative(iso: string | null): string {
  if (!iso) return "Chưa có";
  const d = new Date(iso);
  const diff = Date.now() - d.getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "Vừa xong";
  if (mins < 60) return `${mins} phút trước`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} giờ trước`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days} ngày trước`;
  return d.toLocaleDateString("vi-VN", { day: "2-digit", month: "2-digit" });
}

function getInitials(name: string | null): string {
  if (!name) return "?";
  const parts = name.trim().split(/\s+/);
  return parts
    .slice(-2)
    .map((p) => p[0]?.toUpperCase() ?? "")
    .join("");
}

function tierGradient(tier: string | null): string {
  if (!tier) return "from-slate-400 to-slate-300";
  const map: Record<string, string> = {
    "Hạng Đồng": "from-amber-700 to-amber-500",
    "Hạng Bạc": "from-slate-400 to-slate-300",
    "Hạng Vàng": "from-amber-500 to-orange-400",
    "Hạng Bạch Kim": "from-violet-500 to-brand-indigo",
  };
  return map[tier] ?? "from-slate-400 to-slate-300";
}

function getErrorMessage(err: unknown, fallback: string): string {
  if (err && typeof err === "object" && "response" in err) {
    const resp = (err as { response?: { data?: { detail?: string } } }).response;
    if (resp?.data?.detail) return resp.data.detail;
  }
  return fallback;
}

export default function MerchantMembersPage() {
  const [search, setSearch] = useState("");
  const { data: members, isLoading, isError } = useMembers({ limit: 100 });

  const [detailMember, setDetailMember] = useState<MemberResponse | null>(null);
  const [adjustMember, setAdjustMember] = useState<MemberResponse | null>(null);
  const [toggleMember, setToggleMember] = useState<MemberResponse | null>(null);

  const filtered = useMemo(() => {
    if (!members) return [];
    if (!search) return members;
    const q = search.toLowerCase();
    return members.filter(
      (m) =>
        m.user_full_name?.toLowerCase().includes(q) ||
        m.user_phone?.toLowerCase().includes(q) ||
        m.user_email?.toLowerCase().includes(q)
    );
  }, [members, search]);

  const total = members?.length ?? 0;
  const active30d = members
    ? members.filter(
        (m) =>
          m.last_activity_at &&
          Date.now() - new Date(m.last_activity_at).getTime() <
            30 * 24 * 60 * 60 * 1000
      ).length
    : 0;
  const totalPoints = members
    ? members.reduce((s, m) => s + m.points_balance, 0)
    : 0;

  return (
    <main className="px-4 py-5 md:px-8 md:py-6">
      <header className="flex flex-col items-start gap-4 md:flex-row md:justify-between">
        <div>
          <h1 className="font-headline text-[32px] font-bold text-slate-800">
            Danh sách thành viên
          </h1>
          <p className="mt-1 text-[14px] text-slate-500">
            Quản lý {total} thành viên
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            type="button"
            className="flex items-center gap-2 rounded-xl border border-brand-indigo bg-white px-4 py-2.5 text-[13px] font-bold text-brand-indigo hover:bg-brand-indigo/5"
          >
            <Download className="h-4 w-4" />
            Xuất Excel
          </button>
        </div>
      </header>

      {/* KPI strip */}
      <section className="mt-6 grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard
          icon={Users}
          label="Tổng thành viên"
          value={total.toLocaleString("vi-VN")}
          tone="indigo"
        />
        <StatCard
          icon={Users}
          label="Hoạt động 30 ngày"
          value={active30d.toLocaleString("vi-VN")}
          tone="green"
        />
        <StatCard
          icon={Coins}
          label="Tổng điểm hiện có"
          value={totalPoints.toLocaleString("vi-VN")}
          tone="orange"
        />
        <StatCard
          icon={Crown}
          label="Hoạt động / Tổng"
          value={total > 0 ? `${Math.round((active30d / total) * 100)}%` : "0%"}
          tone="indigo"
        />
      </section>

      <section className="mt-5 rounded-xl border border-slate-100 bg-white p-3 shadow-sm">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute inset-y-0 left-3 my-auto h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Tìm theo tên, SĐT, email..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-lg border border-slate-200 bg-slate-50 py-2 pl-9 pr-3 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
          />
        </div>
      </section>

      <section className="mt-5 overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-sm">
        {isLoading ? (
          <div className="flex h-48 items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-brand-indigo" />
          </div>
        ) : isError ? (
          <div className="p-6 text-center text-red-600">
            Không tải được danh sách thành viên
          </div>
        ) : filtered.length === 0 ? (
          <div className="p-16 text-center">
            <Users className="mx-auto h-12 w-12 text-slate-300" />
            <p className="mt-4 font-bold text-slate-700">
              {search ? "Không tìm thấy thành viên" : "Chưa có thành viên"}
            </p>
            <p className="mt-2 text-[13px] text-slate-500">
              {search
                ? "Thử tìm với từ khoá khác"
                : "Khách sẽ xuất hiện sau khi tích điểm lần đầu"}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
          <table className="w-full min-w-[900px]">
            <thead className="border-b border-slate-100 bg-slate-50">
              <tr className="text-left text-[11px] font-bold uppercase text-slate-500">
                <th scope="col" className="px-4 py-3">#</th>
                <th scope="col" className="px-4 py-3">Khách hàng</th>
                <th scope="col" className="px-4 py-3">Liên hệ</th>
                <th scope="col" className="px-4 py-3 text-center">Hạng</th>
                <th scope="col" className="px-4 py-3 text-right">Điểm</th>
                <th scope="col" className="px-4 py-3 text-right">Tích lũy</th>
                <th scope="col" className="px-4 py-3 text-right">Lần cuối GD</th>
                <th scope="col" className="px-4 py-3 text-right">Hành động</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((m: MemberResponse, idx) => (
                <tr
                  key={m.membership_id}
                  className={`border-b border-slate-50 last:border-b-0 hover:bg-slate-50/50 ${
                    !m.is_active ? "bg-slate-50/40 opacity-70" : ""
                  }`}
                >
                  <td className="px-4 py-3 text-[12px] text-slate-400">
                    {idx + 1}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2.5">
                      <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-indigo-200 to-violet-200 text-[12px] font-bold text-indigo-700">
                        {getInitials(m.user_full_name)}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <p className="text-[13px] font-bold text-slate-800">
                            {m.user_full_name ?? "Chưa đặt tên"}
                          </p>
                          {!m.is_active && (
                            <span className="rounded-full bg-red-50 px-2 py-0.5 text-[10px] font-bold text-red-600">
                              Đã khoá
                            </span>
                          )}
                        </div>
                        <p className="text-[10px] font-mono text-slate-400">
                          M-{m.membership_id}
                        </p>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <p className="text-[12px] font-medium text-slate-700">
                      {m.user_phone ?? "—"}
                    </p>
                    <p className="text-[10px] text-slate-400">
                      {m.user_email ?? "—"}
                    </p>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex justify-center">
                      {m.current_tier_name ? (
                        <span
                          className={`flex items-center gap-1 rounded-full bg-gradient-to-r ${tierGradient(
                            m.current_tier_name
                          )} px-2 py-0.5 text-[11px] font-bold text-white`}
                        >
                          <Crown className="h-2.5 w-2.5" fill="white" />
                          {m.current_tier_name}
                        </span>
                      ) : (
                        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] text-slate-500">
                          Chưa phân
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right font-headline text-[14px] font-bold text-brand-orange">
                    {m.points_balance.toLocaleString("vi-VN")}
                  </td>
                  <td className="px-4 py-3 text-right text-[12px] text-slate-600">
                    {m.lifetime_earned.toLocaleString("vi-VN")}
                  </td>
                  <td className="px-4 py-3 text-right text-[12px] text-slate-500">
                    {formatRelative(m.last_activity_at)}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-1">
                      <button
                        type="button"
                        aria-label="Xem chi tiết"
                        title="Xem chi tiết"
                        onClick={() => setDetailMember(m)}
                        className="flex h-11 w-11 items-center justify-center rounded-lg text-brand-indigo hover:bg-indigo-50"
                      >
                        <Eye className="h-5 w-5" />
                      </button>
                      <button
                        type="button"
                        aria-label="Chỉnh sửa điểm"
                        title="Chỉnh sửa điểm"
                        onClick={() => setAdjustMember(m)}
                        className="flex h-11 w-11 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100"
                      >
                        <Pencil className="h-5 w-5" />
                      </button>
                      <button
                        type="button"
                        aria-label={m.is_active ? "Khoá thành viên" : "Mở lại"}
                        title={m.is_active ? "Khoá thành viên" : "Mở lại"}
                        onClick={() => setToggleMember(m)}
                        className={`flex h-11 w-11 items-center justify-center rounded-lg ${
                          m.is_active
                            ? "text-red-500 hover:bg-red-50"
                            : "text-emerald-600 hover:bg-emerald-50"
                        }`}
                      >
                        {m.is_active ? (
                          <Ban className="h-5 w-5" />
                        ) : (
                          <Check className="h-5 w-5" />
                        )}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        )}
      </section>

      {detailMember && (
        <DetailModal
          member={detailMember}
          onClose={() => setDetailMember(null)}
        />
      )}
      {adjustMember && (
        <AdjustPointsModal
          member={adjustMember}
          onClose={() => setAdjustMember(null)}
        />
      )}
      {toggleMember && (
        <ToggleActiveModal
          member={toggleMember}
          onClose={() => setToggleMember(null)}
        />
      )}
    </main>
  );
}

function StatCard({
  icon: Icon,
  label,
  value,
  tone,
}: {
  icon: typeof Users;
  label: string;
  value: string;
  tone: "indigo" | "orange" | "green";
}) {
  const toneClass =
    tone === "orange"
      ? "bg-orange-50 text-brand-orange"
      : tone === "green"
      ? "bg-emerald-50 text-emerald-600"
      : "bg-indigo-50 text-brand-indigo";
  const valueClass =
    tone === "orange" ? "text-brand-orange" : "text-slate-800";
  return (
    <article className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
      <div className="flex items-center gap-3">
        <div
          className={`flex h-10 w-10 items-center justify-center rounded-xl ${toneClass}`}
        >
          <Icon className="h-5 w-5" />
        </div>
        <p className="text-[12px] text-slate-400">{label}</p>
      </div>
      <p
        className={`mt-3 font-headline text-[26px] font-bold ${valueClass}`}
      >
        {value}
      </p>
    </article>
  );
}

function ModalShell({
  title,
  onClose,
  children,
}: {
  title: string;
  onClose: () => void;
  children: React.ReactNode;
}) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 px-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-lg rounded-2xl bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
          <h2 className="font-headline text-[18px] font-bold text-slate-800">
            {title}
          </h2>
          <button
            type="button"
            aria-label="Đóng"
            onClick={onClose}
            className="flex h-9 w-9 items-center justify-center rounded-lg text-slate-400 hover:bg-slate-100"
          >
            <X className="h-5 w-5" />
          </button>
        </header>
        {children}
      </div>
    </div>
  );
}

function DetailModal({
  member,
  onClose,
}: {
  member: MemberResponse;
  onClose: () => void;
}) {
  const { data: ledger, isLoading } = useMemberLedger(member.membership_id, 30);
  return (
    <ModalShell title="Chi tiết thành viên" onClose={onClose}>
      <div className="max-h-[70vh] overflow-y-auto px-5 py-4">
        <div className="grid grid-cols-2 gap-3 text-[13px]">
          <Field label="Họ tên" value={member.user_full_name ?? "Chưa đặt tên"} />
          <Field label="SĐT" value={member.user_phone ?? "—"} />
          <Field label="Email" value={member.user_email ?? "—"} />
          <Field label="Hạng" value={member.current_tier_name ?? "Chưa phân"} />
          <Field
            label="Điểm hiện có"
            value={member.points_balance.toLocaleString("vi-VN")}
          />
          <Field
            label="Điểm tích luỹ"
            value={member.lifetime_earned.toLocaleString("vi-VN")}
          />
          <Field
            label="Tham gia"
            value={new Date(member.joined_at).toLocaleDateString("vi-VN")}
          />
          <Field
            label="Trạng thái"
            value={member.is_active ? "Đang hoạt động" : "Đã khoá"}
          />
        </div>

        <h3 className="mt-5 mb-2 text-[13px] font-bold text-slate-700">
          Lịch sử điểm gần đây
        </h3>
        {isLoading ? (
          <div className="flex h-24 items-center justify-center">
            <Loader2 className="h-5 w-5 animate-spin text-brand-indigo" />
          </div>
        ) : !ledger || ledger.length === 0 ? (
          <p className="rounded-lg bg-slate-50 p-3 text-[12px] text-slate-500">
            Chưa có giao dịch nào.
          </p>
        ) : (
          <ul className="space-y-1.5">
            {ledger.map((row) => (
              <li
                key={row.id}
                className="flex items-center justify-between rounded-lg border border-slate-100 px-3 py-2 text-[12px]"
              >
                <div>
                  <p className="font-medium text-slate-700">
                    {row.description ?? row.reason}
                  </p>
                  <p className="text-[10px] text-slate-400">
                    {new Date(row.created_at).toLocaleString("vi-VN")}
                  </p>
                </div>
                <span
                  className={`font-headline font-bold ${
                    row.delta > 0 ? "text-emerald-600" : "text-red-500"
                  }`}
                >
                  {row.delta > 0 ? "+" : ""}
                  {row.delta.toLocaleString("vi-VN")}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
      <footer className="flex justify-end gap-2 border-t border-slate-100 bg-slate-50 px-5 py-3">
        <button
          type="button"
          onClick={onClose}
          className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-[13px] font-bold text-slate-700 hover:bg-slate-100"
        >
          Đóng
        </button>
      </footer>
    </ModalShell>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[10px] font-bold uppercase text-slate-400">{label}</p>
      <p className="mt-0.5 text-[13px] font-medium text-slate-800">{value}</p>
    </div>
  );
}

function AdjustPointsModal({
  member,
  onClose,
}: {
  member: MemberResponse;
  onClose: () => void;
}) {
  const [delta, setDelta] = useState<string>("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);
  const adjust = useAdjustMemberPoints();

  const deltaNum = Number(delta);
  const isValid =
    Number.isFinite(deltaNum) &&
    Number.isInteger(deltaNum) &&
    deltaNum !== 0 &&
    description.trim().length >= 3;
  const newBalance = isValid ? member.points_balance + deltaNum : null;
  const wouldGoNegative = newBalance != null && newBalance < 0;

  const handleSubmit = () => {
    if (!isValid) return;
    if (wouldGoNegative) {
      setError("Số dư của khách không đủ để trừ điểm.");
      return;
    }
    setError(null);
    adjust.mutate(
      {
        id: member.membership_id,
        delta: deltaNum,
        description: description.trim(),
      },
      {
        onSuccess: () => {
          onClose();
        },
        onError: (err) => {
          setError(getErrorMessage(err, "Cập nhật điểm thất bại."));
        },
      }
    );
  };

  return (
    <ModalShell title="Chỉnh sửa điểm" onClose={onClose}>
      <div className="px-5 py-4">
        <p className="text-[13px] text-slate-500">
          Khách: <span className="font-bold text-slate-800">
            {member.user_full_name ?? member.user_phone ?? "—"}
          </span>
        </p>
        <p className="mt-1 text-[12px] text-slate-500">
          Số dư hiện tại:{" "}
          <span className="font-headline font-bold text-brand-orange">
            {member.points_balance.toLocaleString("vi-VN")} điểm
          </span>
        </p>

        <label className="mt-4 block">
          <span className="text-[12px] font-bold text-slate-700">
            Số điểm cộng/trừ
          </span>
          <input
            type="number"
            inputMode="numeric"
            placeholder="VD: 100 hoặc -50"
            value={delta}
            onChange={(e) => {
              setDelta(e.target.value);
              setError(null);
            }}
            className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-[14px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
          />
          <span className="mt-1 block text-[11px] text-slate-400">
            Số dương = cộng, số âm = trừ. Khác 0.
          </span>
        </label>

        <label className="mt-3 block">
          <span className="text-[12px] font-bold text-slate-700">
            Lý do điều chỉnh
          </span>
          <textarea
            rows={3}
            value={description}
            onChange={(e) => {
              setDescription(e.target.value);
              setError(null);
            }}
            placeholder="VD: Bù điểm sai sót, tặng thưởng dịp đặc biệt..."
            className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
          />
          <span className="mt-1 block text-[11px] text-slate-400">
            Tối thiểu 3 ký tự. Sẽ lưu vào sổ điểm để đối soát.
          </span>
        </label>

        {newBalance != null && (
          <div
            className={`mt-3 rounded-lg p-3 text-[13px] ${
              wouldGoNegative
                ? "bg-red-50 text-red-600"
                : "bg-slate-50 text-slate-700"
            }`}
          >
            Số dư sau điều chỉnh:{" "}
            <span className="font-headline font-bold">
              {newBalance.toLocaleString("vi-VN")} điểm
            </span>
            {wouldGoNegative && " — không cho phép âm"}
          </div>
        )}

        {error && (
          <p className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-[13px] text-red-600">
            {error}
          </p>
        )}
      </div>
      <footer className="flex justify-end gap-2 border-t border-slate-100 bg-slate-50 px-5 py-3">
        <button
          type="button"
          onClick={onClose}
          className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-[13px] font-bold text-slate-700 hover:bg-slate-100"
        >
          Huỷ
        </button>
        <button
          type="button"
          disabled={!isValid || wouldGoNegative || adjust.isPending}
          onClick={handleSubmit}
          className="flex items-center gap-2 rounded-lg bg-gradient-to-r from-brand-indigo to-brand-violet px-5 py-2 text-[13px] font-bold text-white shadow disabled:cursor-not-allowed disabled:opacity-50"
        >
          {adjust.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
          Xác nhận
        </button>
      </footer>
    </ModalShell>
  );
}

function ToggleActiveModal({
  member,
  onClose,
}: {
  member: MemberResponse;
  onClose: () => void;
}) {
  const [error, setError] = useState<string | null>(null);
  const update = useUpdateMember();
  const willDisable = member.is_active;

  const handleConfirm = () => {
    setError(null);
    update.mutate(
      { id: member.membership_id, is_active: !member.is_active },
      {
        onSuccess: () => onClose(),
        onError: (err) =>
          setError(getErrorMessage(err, "Cập nhật trạng thái thất bại.")),
      }
    );
  };

  return (
    <ModalShell
      title={willDisable ? "Khoá thành viên" : "Mở lại thành viên"}
      onClose={onClose}
    >
      <div className="px-5 py-4 text-[13px] text-slate-700">
        <p>
          Bạn có chắc muốn {willDisable ? "khoá" : "mở lại"} thẻ thành viên của{" "}
          <span className="font-bold">
            {member.user_full_name ?? member.user_phone ?? "—"}
          </span>{" "}
          tại đối tác này?
        </p>
        {willDisable ? (
          <p className="mt-3 rounded-lg bg-amber-50 p-3 text-[12px] text-amber-700">
            Khi bị khoá, hệ thống sẽ từ chối tích điểm cho khách này. Khách
            vẫn xem được lịch sử điểm cũ. Bạn có thể mở lại bất cứ lúc nào.
          </p>
        ) : (
          <p className="mt-3 rounded-lg bg-emerald-50 p-3 text-[12px] text-emerald-700">
            Mở lại sẽ cho phép tích điểm bình thường.
          </p>
        )}
        {error && (
          <p className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-[13px] text-red-600">
            {error}
          </p>
        )}
      </div>
      <footer className="flex justify-end gap-2 border-t border-slate-100 bg-slate-50 px-5 py-3">
        <button
          type="button"
          onClick={onClose}
          className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-[13px] font-bold text-slate-700 hover:bg-slate-100"
        >
          Huỷ
        </button>
        <button
          type="button"
          disabled={update.isPending}
          onClick={handleConfirm}
          className={`flex items-center gap-2 rounded-lg px-5 py-2 text-[13px] font-bold text-white shadow disabled:cursor-not-allowed disabled:opacity-50 ${
            willDisable
              ? "bg-red-500 hover:bg-red-600"
              : "bg-emerald-600 hover:bg-emerald-700"
          }`}
        >
          {update.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
          {willDisable ? "Khoá" : "Mở lại"}
        </button>
      </footer>
    </ModalShell>
  );
}
