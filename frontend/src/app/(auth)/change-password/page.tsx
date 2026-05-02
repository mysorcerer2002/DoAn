"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { authApi } from "@/lib/api";

export default function ChangePasswordPage() {
  const router = useRouter();
  const [currentPwd, setCurrent] = useState("");
  const [newPwd, setNew] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await authApi.changePassword({
        current_password: currentPwd,
        new_password: newPwd,
      });
      router.replace("/member");
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setError(err.response?.data?.detail ?? "Lỗi không xác định");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="max-w-md mx-auto p-6">
      <h1 className="text-2xl font-bold mb-2">Đổi mật khẩu</h1>
      <p className="mb-4 text-gray-600">
        Bạn cần đổi mật khẩu trước khi tiếp tục sử dụng hệ thống.
      </p>
      <form onSubmit={submit} className="space-y-4">
        <input
          type="password"
          placeholder="Mật khẩu hiện tại"
          value={currentPwd}
          onChange={(e) => setCurrent(e.target.value)}
          required
          className="w-full border rounded p-2"
        />
        <input
          type="password"
          placeholder="Mật khẩu mới (≥ 8 ký tự)"
          value={newPwd}
          onChange={(e) => setNew(e.target.value)}
          required
          minLength={8}
          className="w-full border rounded p-2"
        />
        {error && <p className="text-red-600">{error}</p>}
        <button
          type="submit"
          disabled={submitting}
          className="w-full bg-blue-600 text-white p-2 rounded disabled:opacity-60"
        >
          {submitting ? "Đang đổi..." : "Đổi mật khẩu"}
        </button>
      </form>
    </main>
  );
}
