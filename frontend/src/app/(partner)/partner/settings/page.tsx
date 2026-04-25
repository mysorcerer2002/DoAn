"use client";

import { CheckCircle2, Loader2, Save } from "lucide-react";
import { useEffect, useState } from "react";

import {
  useMyPartner,
  useMyPartnerSettings,
  useUpdateSettings,
  useUpdateTenant,
} from "@/lib/hooks/use-partner";
import {
  useActivePointRule,
  usePartnerTiers,
} from "@/lib/hooks/use-partner-settings";
import { PointRuleForm, TierMultiplierRow } from "@/components/partner/settings-form";
import { usePartnerStore } from "@/lib/partner-store";

type TenantForm = {
  name: string;
  description: string;
  logo_url: string;
  banner_url: string;
  contact_phone: string;
  contact_email: string;
  address: string;
  tax_code: string;
  website: string;
  business_hours: string;
};

type SettingsForm = {
  points_on_gross: boolean;
  signup_bonus_points: string;
  redemption_default_ttl_days: string;
};

export default function MerchantSettingsPage() {
  const { data: tenant, isLoading: loadingTenant } = useMyPartner();
  const { data: settings, isLoading: loadingSettings } = useMyPartnerSettings();
  const { data: activeRule, isLoading: loadingRule } = useActivePointRule();
  const { data: tiers, isLoading: loadingTiers } = usePartnerTiers();
  const updateTenant = useUpdateTenant();
  const updateSettings = useUpdateSettings();
  const role = usePartnerStore((s) => s.activePartner?.role);

  const [tenantForm, setTenantForm] = useState<TenantForm>({
    name: "",
    description: "",
    logo_url: "",
    banner_url: "",
    contact_phone: "",
    contact_email: "",
    address: "",
    tax_code: "",
    website: "",
    business_hours: "",
  });
  const [settingsForm, setSettingsForm] = useState<SettingsForm>({
    points_on_gross: false,
    signup_bonus_points: "0",
    redemption_default_ttl_days: "14",
  });
  const [savedMessage, setSavedMessage] = useState<string | null>(null);

  useEffect(() => {
    if (tenant) {
      setTenantForm({
        name: tenant.name,
        description: tenant.description ?? "",
        logo_url: tenant.logo_url ?? "",
        banner_url: tenant.banner_url ?? "",
        contact_phone: tenant.contact_phone ?? "",
        contact_email: tenant.contact_email ?? "",
        address: tenant.address ?? "",
        tax_code: tenant.tax_code ?? "",
        website: tenant.website ?? "",
        business_hours: tenant.business_hours ?? "",
      });
    }
  }, [tenant]);

  useEffect(() => {
    if (settings) {
      setSettingsForm({
        points_on_gross: settings.points_on_gross,
        signup_bonus_points: String(settings.signup_bonus_points),
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
        banner_url: tenantForm.banner_url || null,
        contact_phone: tenantForm.contact_phone || null,
        contact_email: tenantForm.contact_email || null,
        address: tenantForm.address || null,
        tax_code: tenantForm.tax_code || null,
        website: tenantForm.website || null,
        business_hours: tenantForm.business_hours || null,
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
        redemption_default_ttl_days: Number(
          settingsForm.redemption_default_ttl_days
        ),
      });
      setSavedMessage("Đã cập nhật cấu hình");
    } catch {
      /* ignore */
    }
  };

  if (loadingTenant || loadingSettings || loadingRule || loadingTiers) {
    return (
      <main className="flex min-h-[60vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-brand-indigo" />
      </main>
    );
  }

  // Layout redirects staff → /staff, nhưng guard lại đây để tránh flash content
  if (role !== "owner") return null;

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
        {/* Partner info */}
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
            <Field label="Ảnh bìa (banner) URL">
              <input
                type="url"
                value={tenantForm.banner_url}
                onChange={(e) =>
                  setTenantForm({ ...tenantForm, banner_url: e.target.value })
                }
                placeholder="https://... (tỉ lệ 16:9, hiển thị ở đầu trang chi tiết)"
                className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
              />
            </Field>

            <div className="!mt-5 border-t border-dashed border-slate-200 pt-4">
              <h3 className="text-[12px] font-bold uppercase tracking-wider text-slate-500">
                Thông tin liên hệ
              </h3>
            </div>

            <Field label="Số điện thoại">
              <input
                type="tel"
                value={tenantForm.contact_phone}
                onChange={(e) =>
                  setTenantForm({
                    ...tenantForm,
                    contact_phone: e.target.value,
                  })
                }
                placeholder="VD: 0901234567"
                className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
              />
            </Field>

            <Field label="Email liên hệ">
              <input
                type="email"
                value={tenantForm.contact_email}
                onChange={(e) =>
                  setTenantForm({
                    ...tenantForm,
                    contact_email: e.target.value,
                  })
                }
                placeholder="hello@shop.vn"
                className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
              />
            </Field>

            <Field label="Địa chỉ">
              <textarea
                rows={2}
                value={tenantForm.address}
                onChange={(e) =>
                  setTenantForm({ ...tenantForm, address: e.target.value })
                }
                placeholder="Số nhà, đường, quận, thành phố"
                className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
              />
            </Field>

            <div className="!mt-5 border-t border-dashed border-slate-200 pt-4">
              <h3 className="text-[12px] font-bold uppercase tracking-wider text-slate-500">
                Thông tin kinh doanh
              </h3>
            </div>

            <Field label="Mã số thuế">
              <input
                type="text"
                value={tenantForm.tax_code}
                onChange={(e) =>
                  setTenantForm({ ...tenantForm, tax_code: e.target.value })
                }
                placeholder="VD: 0312345678"
                className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
              />
            </Field>

            <Field label="Website">
              <input
                type="url"
                value={tenantForm.website}
                onChange={(e) =>
                  setTenantForm({ ...tenantForm, website: e.target.value })
                }
                placeholder="https://shop.vn"
                className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
              />
            </Field>

            <Field label="Giờ mở cửa">
              <input
                type="text"
                value={tenantForm.business_hours}
                onChange={(e) =>
                  setTenantForm({
                    ...tenantForm,
                    business_hours: e.target.value,
                  })
                }
                placeholder="VD: 07:00 - 22:00 hàng ngày"
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
                  Mặc định: tính trên net_amount (= gross do MVP chưa có discount)
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

      {/* Quy tắc tích điểm */}
      {activeRule && (
        <div className="mt-6">
          <PointRuleForm rule={activeRule} />
        </div>
      )}

      {/* Hệ số tích điểm theo hạng */}
      {activeRule?.use_tiers && tiers && tiers.length > 0 && (
        <div className="mt-6">
          <section className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
            <h2 className="font-headline text-[18px] font-bold text-slate-800">
              Tỷ lệ tích điểm theo hạng
            </h2>
            <p className="mt-1 text-[12px] text-slate-500">
              Hệ số nhân áp dụng cho từng hạng thành viên (0.50 – 5.00)
            </p>
            <div className="mt-4 space-y-2">
              {[...tiers]
                .sort((a, b) => a.min_points - b.min_points)
                .map((tier) => (
                  <TierMultiplierRow key={tier.id} tier={tier} />
                ))}
            </div>
          </section>
        </div>
      )}
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
