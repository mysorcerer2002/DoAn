# Mobile Responsive Audit — 2026-04-27

**Viewport:** 375×667 (iPhone SE — màn nhỏ nhất phải support)
**URL:** https://loyalty.ecom-bill.com
**Standard:** Web Interface Guidelines (chuẩn cao)

## Setup quyết định
- **Login storage:** `localStorage.access_token` (NOT sessionStorage — verify từ auth-store.ts)
- **Active partner:** `sessionStorage.active_partner` JSON `{id, name, slug, role}`
- **Staff role:** owner@cafe.vn cover được /staff routes (require_staff_in_partner accept owner) → dùng owner cho audit (staff)
- **Color contrast:** axe-core CDN inject

## Issues legend
- `[H]` Horizontal scroll
- `[T]` Tap target < 44×44px
- `[F]` Font < 14px
- `[C]` Color contrast fail (WCAG AA)
- `[S]` Sticky bar overlap content
- `[M]` Modal/Dialog vượt screen
- `[I]` Input thiếu inputmode hoặc < 44px
- `[X]` Layout vỡ
- `[O]` Other

---

## Per-page findings

### (auth) /login
- `[T]` Tap target nhỏ:
  - Link logo/icon top 40×40
  - Nút "Đăng ký" 136×36 (h<44)
  - "Quên mật khẩu?" 104×20 (h<44)
  - "Đăng ký ngay" 103×21
  - "Điều khoản" 50×14, "Chính sách bảo mật" 157×30
- `[F]` font 10px: "Điều khoản", "Chính sách bảo mật"
- `[C]` contrast 5 violation: text-brand-indigo ratio 4.26-4.46 (expected 4.5), text-slate-400 ratio 2.63 (rất tệ)
- `[O]` overflow OK (docW=360<vw=375)
- Screenshot: `tmp/screenshots/before_auth_login.png`

### (auth) /register
- `[T]` Tap nhỏ:
  - "Quay lại" 40×40 (back arrow header)
  - Tab "Đăng nhập" 136×36
  - "Điều khoản" 62×16, "Chính sách bảo mật" 107×16
  - "Đăng nhập" link 82×21 (footer link)
  - "🏪 Bạn là chủ shop?..." 254×36
- `[I]` Inputs thiếu inputmode: full_name (text), email (email — nên có `inputmode="email"`)
- `[F]` font 11-12px: "Bạn có thể cập nhật ngày sinh..." 11px, "Điều khoản" 12px, "Chính sách bảo mật" 12px, link chủ shop 12px
- `[C]` 7 contrast violations:
  - text-brand-indigo (#6366f1) ratio 4.26-4.46 (need 4.5)
  - bg-indigo-50 + text-brand-indigo banner ratio 3.99 (tệ hơn vì bg sáng)
  - text-slate-400 (#90a1b9) ratio 2.63 (rất tệ — terms footer)
- `[O]` overflow OK (docW=360<vw=375)
- Screenshot: `tmp/screenshots/before_auth_register.png`

### (auth) /register/partner
- `[T]` Tap nhỏ:
  - "Quay lại" 40×40 back button
  - Footer "Đăng nhập" 67×17, "Đăng ký tài khoản thường" 148×16
- `[I]` Inputs thiếu inputmode: full_name, email
- `[F]` font 11-13px: subtitle 13px, "BƯỚC 1/2" 11px, helper 12px, footer link 12-13px
- `[C]` 4 contrast violations:
  - "BƯỚC 1/2" text-brand-indigo 4.46
  - text-slate-400 footer 2.51 (rất tệ)
  - text-brand-orange (#fb923c?) ratio 2.16 (cực tệ — link "Đăng ký tài khoản thường")
- `[O]` overflow OK
- Screenshot: `tmp/screenshots/before_auth_register_partner.png`

---

## (member) — customer khach1@gmail.com

### (member) /member (home)
- `[T]` Tap nhỏ (CRITICAL — shared):
  - Notification bell button 24×24
  - "Khám phá" link 64×21
  - **BottomNavBar items: "Quà" 24×46, "Tôi" 24×46 (width quá hẹp — anchor element không full slot width)** → fix BottomNavBar shared
- `[F]` font 10-12px nhiều: "TỔNG ĐIỂM TÍCH LŨY" 12, "Hạng Đồng" 12, "THÀNH VIÊN" 10, action card label "Mã QR/Đổi quà/Lịch sử" 11, BottomNav label 12
- `[C]` 8 contrast violations:
  - text-brand-indigo "Khám phá" 4.26
  - text-slate-400 "Hạng Đồng" 2.63
  - bg-indigo-50 + text-brand-indigo badge 4.06
  - text-brand-orange "58 đ" 2.26 (rất tệ — chính là trị điểm display)
  - BottomNav inactive labels (Quà, QR, Voucher, Tôi) text-slate-400 2.6-2.63
- `[O]` overflow OK
- Screenshot: `tmp/screenshots/before_member_home.png`

### (member) /member/history
- `[T]` Header "Quay lại" 40×40, "Lọc" 40×40 (cận biên 44, FAIL); BottomNav (shared)
- `[F]` smallFonts: 61 elements (font 10/11/12) — list cards mật độ cao
- `[C]` 76 contrast violations (text-slate-400 timestamp + còn-X label, text-orange-500 +X điểm bold ratio thấp)
- `[S]` BottomNavBar overlaps list content (sticky bar che row giữa) — list cần `padding-bottom`
- `[O]` overflow OK
- Screenshot: `tmp/screenshots/before_member_history.png`

### Pattern shared đã rõ sau 5 page (login + register + register/partner + member/home + history):
1. **BottomNavBar items** ✅ VERIFIED `frontend/src/components/member/bottom-nav-bar.tsx:84-101`: `<Link>` className chỉ `flex flex-col items-center gap-1` → KHÔNG padding-x. Anchor width = max(icon 24px, label width) ≈ 24-50px tuỳ label. **Tap area thực = anchor box, không phải slot `justify-around`** (whitespace giữa items không clickable). Fix: thêm `flex-1 py-2` vào NavTab để anchor full slot width + ≥44px height. (Center QR cũng cần check — hiện -mt-8 negative offset, anchor thật chứa cả circle 56×56 + label nên tap target OK ≈ 56×~76, không cần fix.)
2. **Header icon buttons** (back, filter, notification): 24-40px → cần ≥44px.
3. **`text-slate-400`** muted-text dùng dày khắp app → contrast 2.5-2.7. Cần đổi sang `text-slate-500` (#64748b ≈ 4.78) hoặc `text-slate-600` (#475569 ≈ 7.7).
4. **`text-brand-indigo`** primary link → ratio 4.26-4.46. Cần đậm thêm (#4F46E5 indigo-600 → ratio 5.5+).
5. **`text-brand-orange`** stat text → ratio 2.16-2.26 (cực tệ). Đổi sang `text-orange-600` (#ea580c ≈ 4.5+) hoặc dùng nền tối/đậm cho stat card.
6. **Font ≤12px**: dùng tràn lan (label, badge, footer, helper). WIG yêu cầu ≥14px cho text-content; ≥12px chỉ acceptable cho meta label nhỏ.
7. **Inputs thiếu inputmode**: text/email/number → cần `inputmode="email"`, `inputmode="numeric"` trên SĐT/giá tiền.
8. **List page có BottomNavBar phải `padding-bottom: 80-96px`** để không che row cuối.

---

## Quick-probe các page còn lại (sau pattern saturated)

### (member) còn lại
| Page | hScroll | tap nhỏ | smallFont | overflow inner | Note |
|------|---------|---------|-----------|----------------|------|
| /member/qr | no | 1 (back) | 2 | – | Focused full-screen, BottomNav ẩn — clean |
| /member/rewards | no | 5 | 17 | – | Pattern shared |
| /member/vouchers | no | 3 | 12 | – | Pattern shared |
| /member/profile | no | 5 (back, edit, "Chỉnh sửa" 74×18, BottomNav x2) | 13 | – | Pattern shared |

### (partner) — owner@cafe.vn / Cafe Cộng
| Page | hScroll | tap nhỏ | smallFont | overflow inner | Note |
|------|---------|---------|-----------|----------------|------|
| /partner | no | 1 (visible) | 37 | – | Drawer pattern OK; sidebar ẩn mobile, hamburger 32×32 < 44 |
| /partner/transactions | no | 2 (back, search h=38) | 120 | sw=393 cw=326 | Inner table scroll — UX rough |
| /partner/members | no | 4 | 119 | **sw=900 cw=326** | Table 2.7× width — cần card view mobile |

### (admin) — admin@loyalty.vn
| Page | hScroll | tap nhỏ | smallFont | overflow inner | Note |
|------|---------|---------|-----------|----------------|------|
| /admin | no | 1 | 26 | – | Drawer pattern OK |
| /admin/users | no | 1 | 264 | **sw=1008 cw=326** | Table 3.1× width — cần card view mobile |

### Pages chưa probe (quick-skip — pattern sufficient)

**Member**: `/member/partners`, `/member/partners/[slug]`, `/member/vouchers/[id]`, `/redemption/success`
→ Detail/list pages, kế thừa pattern shared (BottomNav, header back, small fonts). Không cần probe riêng.

**Partner**: `/partner/rewards`, `/partner/staff`, `/partner/settings`, `/partner/pos/transactions/new`
→ Pattern: list/form pages cùng layout sidebar drawer, kế thừa pattern + có table overflow tương tự.

**Staff**: `/staff`, `/staff/pos/transactions/new`, `/staff/pos/redemptions/use`
→ POS forms, kế thừa input pattern + tap target.

**Admin**: `/admin/audit`, `/admin/logs`, `/admin/partners`, `/admin/stats`, `/admin/system-points`, `/admin/settings`
→ Tất cả là table-based, pattern overflow giống `/admin/users`.

**Auth/landing**: `/`, `/redemption/success`
→ Public, pattern auth shared.

---

## Pass 1 Conclusion (2026-04-27)

**Tổng issue Mobile (375×667)** từ 11 page probe:

### Page-level layout:
- ❌ **0 page có hScroll thực sự** — tốt, không có "site bị vỡ ngang" overall.
- ⚠️ **2 page tables overflow nội bộ nặng** (`/partner/members` 900px, `/admin/users` 1008px).

### Component-level (8 patterns shared):
1. **BottomNavBar items 24-50px wide** — anchor không có padding-x, click area chỉ icon+label intrinsic.
2. **Header icon buttons 24-40px** — back, filter, notification, hamburger menu.
3. **`text-slate-400` contrast 2.5-2.7** — fail WCAG AA (cần 4.5:1).
4. **`text-brand-indigo` contrast 4.26-4.46** — borderline fail WCAG AA.
5. **`text-brand-orange` contrast 2.16-2.26** — cực fail, dùng cho stats.
6. **Font ≤12px** dùng tràn lan label/footer/helper.
7. **Input thiếu `inputmode`** trên email/phone/numeric.
8. **List pages thiếu `padding-bottom`** đủ để clear BottomNavBar.

### Pass 2 priority (sẽ fix shared trước):
1. `BottomNavBar` NavTab — `flex-1 py-2` để full-slot + tap height ≥44.
2. Header icon button shared — chuẩn hoá h-10 w-10 → h-11 w-11 (44×44).
3. `text-slate-400` → `text-slate-500` (or higher) globally for muted text.
4. `text-brand-orange` stat → `text-orange-600` hoặc font-bold + size ≥18.
5. `text-brand-indigo` link → `text-indigo-600` (đã có trong tailwind).
6. Auth/profile inputs → thêm `inputMode` attr.
7. (member) layout — list page wrap có `pb-24`.
8. Partner/admin tables — verify shadcn DataTable đã có `overflow-x-auto` wrapper với scroll indicator; nếu chưa → bổ sung visual cue.
