"use client";

import { CheckCircle2, Loader2, Save } from "lucide-react";
import { useEffect, useState } from "react";

import {
  useMyTenant,
  useMyTenantSettings,
  useUpdateSettings,
  useUpdateTenant,
} from "@/lib/hooks/use-merchant";

type TenantForm = {
  name: string;
  description: string;
  logo_url: string;
};

type SettingsForm = {
  points_on_gross: boolean;
  signup_bonus_points: string;
  voucher_default_ttl_days: string;
  redemption_default_ttl_days: string;
};

export default function MerchantSettingsPage() {
  const { data: tenant, isLoading: loadingTenant } = useMyTenant();
  const { data: settings, isLoading: loadingSettings } = useMyTenantSettings();
  const updateTenant = useUpdateTenant();
  const updateSettings = useUpdateSettings();

  const [tenantForm, setTenantForm] = useState<TenantForm>({
    name: "",
    description: "",
    logo_url: "",
  });
  const [settingsForm, setSettingsForm] = useState<SettingsForm>({
    points_on_gross: false,
    signup_bonus_points: "0",
    voucher_default_ttl_days: "14",
    redemption_default_ttl_days: "14",
  });
  const [savedMessage, setSavedMessage] = useState<string | null>(null);

  useEffect(() => {
    if (tenant) {
      setTenantForm({
        name: tenant.name,
        description: tenant.description ?? "",
        logo_url: tenant.logo_url ?? "",
      });
    }
  }, [tenant]);

  useEffect(() => {
    if (settings) {
      setSettingsForm({
        points_on_gross: settings.points_on_gross,
        signup_bonus_points: String(settings.signup_bonus_points),
        voucher_default_ttl_days: String(settings.voucher_default_ttl_days),
        redemption_default_ttl_days: String(
          settings.redemption_default_ttl_days
        ),
      });
    }
  }, [settings]);

  const handleSaveTenant = async () => {
    setSavedMessage(null);
    try {
      await updateTenant.mutateAsync({
        name: tenantForm.name,
        description: tenantForm.description || null,
        logo_url: tenantForm.logo_url || null,
      });
      setSavedMessage("Đã cập nhật thông tin cửa hàng");
    } catch {
      /* ignore */
    }
  };

  const handleSaveSettings = async () => {
    setSavedMessage(null);
    try {
      await updateSettings.mutateAsync({
        points_on_gross: settingsForm.points_on_gross,
        signup_bonus_points: Number(settingsForm.signup_bonus_points),
        voucher_default_ttl_days: Number(
          settingsForm.voucher_default_ttl_days
        ),
        redemption_default_ttl_days: Number(
          settingsForm.redemption_default_ttl_days
        ),
      });
      setSavedMessage("Đã cập nhật cấu hình");
    } catch {
      /* ignore */
    }
  };

  if (loadingTenant || loadingSettings) {
    return (
      <main className="flex min-h-[60vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-brand-indigo" />
      </main>
    );
  }

  return (
    <main className="px-4 py-5 md:px-8 md:py-6">
      <header>
        <h1 className="font-headline text-[32px] font-bold text-slate-800">
          Cài đặt cửa hàng
        </h1>
        <p className="mt-1 text-[14px] text-slate-500">
          Quản lý thông tin và quy tắc tích điểm
        </p>
      </header>

      {savedMessage && (
        <div className="mt-4 flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-[13px] text-emerald-700">
          <CheckCircle2 className="h-4 w-4" />
          {savedMessage}
        </div>
      )}

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Tenant info */}
        <section className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
          <h2 className="font-headline text-[18px] font-bold text-slate-800">
            Thông tin cửa hàng
          </h2>
          <div className="mt-4 space-y-3">
            <Field label="Tên cửa hàng">
              <input
                type="text"
                value={tenantForm.name}
                onChange={(e) =>
                  setTenantForm({ ...tenantForm, name: e.target.value })
                }
                className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
              />
            </Field>
            <Field label="Slug (URL)">
              <input
                type="text"
                value={tenant?.slug ?? ""}
                disabled
                className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-100 px-3 py-2 text-[13px] text-slate-500"
              />
            </Field>
            <Field label="Mô tả">
              <textarea
                rows={3}
                value={tenantForm.description}
                onChange={(e) =>
                  setTenantForm({
                    ...tenantForm,
                    description: e.target.value,
                  })
                }
                className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
              />
            </Field>
            <Field label="Logo URL">
              <input
                type="url"
                value={tenantForm.logo_url}
                onChange={(e) =>
                  setTenantForm({ ...tenantForm, logo_url: e.target.value })
                }
                placeholder="https://..."
                className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
              />
            </Field>
          </div>
          <button
            type="button"
            onClick={handleSaveTenant}
            disabled={updateTenant.isPending}
            className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-brand-indigo to-brand-violet py-2.5 text-[13px] font-bold text-white shadow-lg shadow-indigo-200 active:scale-95 disabled:opacity-60"
          >
            {updateTenant.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Save className="h-4 w-4" />
            )}
            Lưu thông tin
          </button>
        </section>

        {/* Settings */}
        <section className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
          <h2 className="font-headline text-[18px] font-bold text-slate-800">
            Cấu hình điểm thưởng
          </h2>
          <div className="mt-4 space-y-3">
            <label className="flex items-center justify-between rounded-xl bg-slate-50 px-3 py-3">
              <div>
                <p className="text-[13px] font-bold text-slate-800">
                  Tính điểm trên giá gốc
                </p>
                <p className="text-[11px] text-slate-500">
                  Mặc định: tính trên giá sau voucher
                </p>
              </div>
              <input
                type="checkbox"
                checked={settingsForm.points_on_gross}
                onChange={(e) =>
                  setSettingsForm({
                    ...settingsForm,
                    points_on_gross: e.target.checked,
                  })
                }
                className="h-5 w-5 rounded border-slate-300 text-brand-indigo"
              />
            </label>

            <Field label="Điểm thưởng khi đăng ký">
              <input
                type="number"
                min="0"
                value={settingsForm.signup_bonus_points}
                onChange={(e) =>
                  setSettingsForm({
                    ...settingsForm,
                    signup_bonus_points: e.target.value,
                  })
                }
                className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
              />
            </Field>

            <Field label="Thời hạn voucher mặc định (ngày)">
              <input
                type="number"
                min="1"
                max="365"
                value={settingsForm.voucher_default_ttl_days}
                onChange={(e) =>
                  setSettingsForm({
                    ...settingsForm,
                    voucher_default_ttl_days: e.target.value,
                  })
                }
                className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
              />
            </Field>

            <Field label="Thời hạn đổi quà mặc định (ngày)">
              <input
                type="number"
                min="1"
                max="365"
                value={settingsForm.redemption_default_ttl_days}
                onChange={(e) =>
                  setSettingsForm({
                    ...settingsForm,
                    redemption_default_ttl_days: e.target.value,
                  })
                }
                className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
              />
            </Field>
          </div>
          <button
            type="button"
            onClick={handleSaveSettings}
            disabled={updateSettings.isPending}
            className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-brand-indigo to-brand-violet py-2.5 text-[13px] font-bold text-white shadow-lg shadow-indigo-200 active:scale-95 disabled:opacity-60"
          >
            {updateSettings.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Save className="h-4 w-4" />
            )}
            Lưu cấu hình
          </button>
        </section>
      </div>
    </main>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="text-[12px] font-medium text-slate-500">{label}</label>
      {children}
    </div>
  );
}
