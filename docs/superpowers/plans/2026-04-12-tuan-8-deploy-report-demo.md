# Tuần 8 — Deploy chính thức, Báo cáo PDF, Slide demo & Bảo vệ nháp

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development.
>
> **NGUYÊN TẮC TUẦN 8 (KỶ LUẬT NGHIÊM NGẶT):**
> - **TUYỆT ĐỐI KHÔNG code feature mới**
> - Chỉ hotfix bug **blocker cho demo** (vd: crash, không login được, không hiển thị data)
> - Mọi feature không hoàn thiện được note vào **"Future Work"** trong báo cáo, KHÔNG cố làm xong
> - Buffer cho deploy issues + báo cáo + chuẩn bị bảo vệ
> - Cuối tuần phải có: deploy URL chạy được, báo cáo PDF in được, slide demo, demo scenario chuẩn bị xong, milestone review #4 với giảng viên

**Goal:** Deploy hệ thống lên môi trường demo công khai (Docker + ngrok hoặc VPS). Viết báo cáo PDF đầy đủ ~30-50 trang theo template trường (chương 1-5: giới thiệu, phân tích, thiết kế, cài đặt, kết luận). Tạo slide demo 10-15 slides. Chuẩn bị demo scenario 15-20 phút cho buổi bảo vệ. Milestone Review #4 với giảng viên hướng dẫn (bảo vệ nháp).

**Cuối tuần phải có:**
- Demo URL public chạy được (https://... hoặc https://[ngrok-id].ngrok.io)
- File `bao-cao.pdf` ~30-50 trang
- File `slide-demo.pdf` (hoặc .pptx) 10-15 slides
- File `demo-scenario.md` script 15-20 phút
- Milestone review #4 với giảng viên xong + feedback ghi nhận
- Tag `tuan-8-final` + push lên GitHub
- README hoàn thiện cho người chấm có thể tự reproduce

**Acceptance criteria:**
- Mở demo URL → đăng nhập admin/owner/staff/customer được
- Chạy demo scenario 15 phút end-to-end không lỗi
- Báo cáo PDF có:
  - Trang bìa
  - Mục lục
  - Chương 1: Mở đầu (lý do chọn đề tài, mục tiêu, phạm vi, công nghệ)
  - Chương 2: Phân tích thiết kế (use case, ERD, sequence diagrams)
  - Chương 3: Cài đặt (kiến trúc, modules, code highlights)
  - Chương 4: Kết quả thử nghiệm (screenshots, test results, performance)
  - Chương 5: Kết luận và hướng phát triển
  - Tài liệu tham khảo
- Slide demo có structure: Title → Tổng quan → Vấn đề → Giải pháp → Demo → Kiến trúc → Kết quả → Hướng phát triển → Q&A
- Giảng viên feedback positive về demo nháp (hoặc note items cần fix)

---

## Tổng quan các phase

| Phase | Tasks | Mô tả |
|---|---|---|
| 1 | 1-3 | Chuẩn bị deploy + demo data |
| 2 | 4-7 | Deploy production (Option A: Docker + ngrok HOẶC Option B: VPS) |
| 3 | 8-10 | Smoke test trên deploy URL + fix blockers |
| 4 | 11-15 | Viết báo cáo PDF — 5 chương |
| 5 | 16-19 | Tạo slide demo + demo scenario script |
| 6 | 20-22 | Diagrams cho báo cáo (use case, ERD, sequence) |
| 7 | 23-25 | Milestone Review #4 với giảng viên + ghi nhận feedback |
| 8 | 26-28 | Final cleanup + tag + push CI |

**Total:** 28 tasks · không có LOC code mới · ~50 trang báo cáo + 15 slides

---

## File Structure (tuần 8)

```
D:/DoAn/
├── docs/
│   ├── bao-cao/
│   │   ├── bao-cao.md             # Markdown source
│   │   ├── bao-cao.pdf            # Final PDF
│   │   ├── images/                # Screenshots + diagrams
│   │   │   ├── usecase.png
│   │   │   ├── erd.png
│   │   │   ├── sequence-luong-c.png
│   │   │   ├── sequence-luong-d.png
│   │   │   ├── architecture.png
│   │   │   ├── screen-pos.png
│   │   │   ├── screen-merchant-dashboard.png
│   │   │   ├── screen-member-qr.png
│   │   │   └── ...
│   │   └── tham-khao.md
│   ├── slide-demo/
│   │   ├── slide-demo.md          # Markdown source (Marp / Slidev)
│   │   ├── slide-demo.pdf         # Final PDF
│   │   └── slide-demo.pptx        # Optional Microsoft PowerPoint
│   ├── demo-scenario.md           # Script 15-20 phút
│   └── milestone-4-feedback.md    # Ghi nhận feedback giảng viên
└── README.md                      # MODIFY (add demo URL)
```

---

## PHASE 1 — Chuẩn bị deploy + demo data

### Task 1: Reset môi trường + verify từ scratch

```bash
cd D:/DoAn
docker compose down -v  # CONFIRM: xoá hết
docker compose up -d --build
make seed-fresh
```

- [ ] **Step 1:** Verify backend `/health` OK
- [ ] **Step 2:** Verify frontend `http://localhost:3000` mở được
- [ ] **Step 3:** Verify seed counts đầy đủ (10 users + 2 tenants + ~100 transactions + ...)
- [ ] **Step 4:** Manual smoke test 5 phút: login admin → owner → staff → customer

---

### Task 2: Tạo seed v3 với data realistic cho demo

**Files:**
- Modify: `D:/DoAn/backend/scripts/seed.py`

> **Mục tiêu:** Demo data đẹp mắt — tên thật, ảnh thật, transactions phân bố theo thời gian (không random hoàn toàn).

- [ ] **Step 1:** Update `seed.py`:
  - 2 tenant: "The Coffee House" + "Pizza 4P's" với mô tả + logo URL
  - 5 hạng mỗi tenant
  - 5 rewards mỗi tenant với ảnh URL (Unsplash)
  - 3 campaigns mỗi tenant: "Khai trương 30%", "Sinh nhật 20%", "Cuối tuần 10%"
  - 30 customers với họ tên Việt Nam thật
  - 200 transactions phân bố theo 30 ngày qua (5-10 giao dịch/ngày)

- [ ] **Step 2:** Verify seed chạy thành công + ledger invariant pass

```bash
cd D:/DoAn
make seed-fresh
docker compose exec postgres psql -U loyalty -d loyalty -c "SELECT COUNT(*) FROM transactions;"
```

- [ ] **Step 3:** Commit

```bash
git add backend/scripts/seed.py
git commit -m "feat(backend): seed v3 với demo data realistic (200 transactions)"
```

---

### Task 3: Tạo file `docs/demo-scenario.md` script demo

**Files:**
- Create: `D:/DoAn/docs/demo-scenario.md`

- [ ] **Step 1: Tạo file**

```markdown
# Demo Scenario — Loyalty Platform

**Thời lượng:** 15-20 phút

## Setup trước demo
- [ ] Browser sạch (incognito)
- [ ] Demo URL: https://...
- [ ] Có 2 device sẵn (laptop + điện thoại Android) hoặc 2 browser windows
- [ ] Đã chuẩn bị credentials trên giấy/note:
  - Admin: admin@loyalty.local / admin12345
  - Owner: owner1@loyalty.local / owner12345
  - Staff: staff1a@loyalty.local / staff12345
  - Customer: 0901234567 / claim flow

## Phần 1 — Tổng quan & Super Admin (3 phút)

1. Mở demo URL — landing page
2. Login `admin@loyalty.local` → /admin
3. Giải thích role Super Admin + multi-tenant architecture
4. Vào /admin/tenants → show 2 tenants active + giải thích flow approve

## Phần 2 — Owner workflow (5 phút)

1. Logout, login `owner1@loyalty.local` → /merchant
2. Show dashboard với 6 charts:
   - Member count
   - Transactions chart 30 days
   - Revenue
   - Tier distribution pie
   - Campaign ROI
3. Vào /merchant/tiers → show 5 hạng (Bronze → Diamond)
4. Vào /merchant/point-rules → show rule "1 điểm / 1000 VND"
5. Vào /merchant/staff → show list nhân viên
6. Vào /merchant/campaigns → show 3 campaigns active
7. Vào /merchant/rewards → show catalog quà

## Phần 3 — Tích điểm tại quầy (POS) (3 phút)

1. Login staff trong tab khác `staff1a@loyalty.local`
2. Vào /pos/transactions/new
3. Nhập SĐT khách thật `0987654321` + 50000 VND → tích điểm thành công
4. Show success card với balance + tier

## Phần 4 — Customer & QR scan (4 phút)

1. Login khách trên điện thoại (qua claim flow)
2. /member → show điểm + tier + danh sách shop
3. /member/qr → show QR rolling
4. Quay lại staff laptop → /pos/transactions/scan → quét QR
5. Tích điểm thành công → khách thấy notification

## Phần 5 — Đổi quà + Voucher (3 phút)

1. Khách /member/rewards → đổi 1 quà → nhận code
2. Staff /merchant/redemptions/use → nhập code → success
3. Khách /member/vouchers/available → claim 1 voucher
4. Khách đưa code → staff /pos/transactions/new → áp voucher → discount

## Phần 6 — Q&A (2 phút)

- Cross-tenant isolation tests
- Architecture decisions
- Tech stack choices

## Tổng kết

- Multi-tenant + auth + JWT
- 3 cách tích điểm + ledger append-only
- Lazy claim voucher chống TOCTOU
- PWA cho khách hàng
- 180+ tests pass
- CI/CD GitHub Actions
```

- [ ] **Step 2:** Commit

```bash
git add docs/demo-scenario.md
git commit -m "docs: thêm demo scenario 15-20 phút cho bảo vệ"
```

---

## PHASE 2 — Deploy Production

### Tasks 4-7: Deploy theo Option A (Docker + ngrok) HOẶC Option B (VPS)

> Sinh viên chọn 1 option dựa vào budget + thời gian.

### **Option A — Docker + ngrok (Khuyến nghị nếu thiếu thời gian)**

- [ ] **Task 4A:** Cài ngrok
  - Download từ https://ngrok.com/download
  - Đăng ký account (free), lấy authtoken
  - `ngrok config add-authtoken <token>`

- [ ] **Task 5A:** Run docker-compose + expose ports

```bash
cd D:/DoAn
docker compose up -d --build
make seed-fresh

# Terminal 1: expose backend
ngrok http 8000

# Terminal 2: expose frontend
ngrok http 3000
```

- [ ] **Task 6A:** Cập nhật env để frontend gọi backend qua ngrok URL

```bash
# Cập nhật frontend/.env.local
echo "NEXT_PUBLIC_API_URL=https://abc-123.ngrok-free.app" > frontend/.env.local

# Restart frontend container
docker compose restart frontend
```

- [ ] **Task 7A:** Verify URL public hoạt động

Mở `https://abc-123-frontend.ngrok-free.app` từ máy khác → verify login + dashboard load được.

> **Lưu ý ngrok free:** URL đổi mỗi lần restart. Cần ghi note URL hiện tại trên slide. Nếu muốn URL ổn định, dùng `cloudflared tunnel` (free, custom subdomain) hoặc upgrade ngrok.

### **Option B — VPS (Khuyến nghị nếu có $5-10/tháng + thời gian)**

- [ ] **Task 4B:** Mua VPS DigitalOcean / Vultr / Linode ~$6/tháng
  - Ubuntu 22.04 LTS
  - 1 CPU, 2GB RAM minimum
  - Firewall: 22, 80, 443 only

- [ ] **Task 5B:** Setup server
  - SSH với key
  - Cài Docker + Docker Compose
  - Clone repo: `git clone https://github.com/.../loyalty-platform`
  - Cài Caddy (reverse proxy + auto HTTPS)

```bash
# Caddyfile
yourdomain.com {
    reverse_proxy frontend:3000
}

api.yourdomain.com {
    reverse_proxy backend:8000
}
```

- [ ] **Task 6B:** Trỏ DNS A record về VPS IP (nếu có domain) hoặc dùng nip.io / sslip.io cho IP-based domain

- [ ] **Task 7B:** Verify HTTPS hoạt động + auto cert từ Let's Encrypt

```bash
git commit -m "chore(deploy): add Caddyfile cho VPS deployment"
```

---

## PHASE 3 — Smoke Test Deploy URL

### Tasks 8-10: Test deploy + fix blockers

- [ ] **Task 8:** Smoke test demo URL (cần backend public URL OK)
  - Login 4 roles
  - Dashboard hiển thị data
  - QR + scan flow (cần PWA install nếu có HTTPS)
  - Đổi quà
  - Claim voucher

- [ ] **Task 9:** Fix blockers nếu có (chỉ blocker cho demo, không làm feature):
  - **CORS issue:** fix `FRONTEND_ORIGINS` env trong backend `.env` thêm ngrok frontend URL
  - **HTTPS mixed content:** ngrok free tier auto HTTPS — đảm bảo cả 2 URL đều `https://`. Frontend `NEXT_PUBLIC_API_URL=https://...` không có `http://`
  - **Cookie SameSite issue (★ FIX I7 review):** **TRÁNH đổi `SameSite=None`** vì:
    - `SameSite=None` BẮT BUỘC `Secure=true` → cookie không hoạt động qua `http://localhost`
    - Phá CSRF protection (`SameSite=Strict` từ tuần 1)
  - **Cách an toàn:** Dùng **1 ngrok tunnel duy nhất** cho cả frontend + backend qua subpath:
    ```
    https://xyz.ngrok-free.app/        → frontend (Next.js)
    https://xyz.ngrok-free.app/api/    → backend (FastAPI behind reverse proxy)
    ```
    Cùng origin → `SameSite=Strict` vẫn hoạt động, không cần đổi.
  - Hoặc dùng `cloudflared tunnel` (free, có custom subdomain ổn định) thay vì 2 ngrok URLs riêng biệt
  - **Nếu BẮT BUỘC phải dùng 2 ngrok URLs riêng:** thêm env flag `COOKIE_SAMESITE=none` (default `lax`/`strict`), enforce HTTPS, document rõ trong báo cáo "demo dùng cross-site cookie cho ngrok 2 tunnels — production sẽ dùng same-origin"

- [ ] **Task 9.5 (★ NEW — fix I6 review): Security smoke test sau deploy**

```bash
# 1. Verify HTTPS hoạt động (không mixed content)
curl -I https://your-demo-url.ngrok-free.app

# 2. Verify CORS chỉ allow whitelisted origins
curl -X POST https://your-demo-url.ngrok-free.app/auth/login \
  -H "Origin: https://evil.example.com" \
  -H "Content-Type: application/json" \
  -d '{"email":"test","password":"test"}' \
  -i | grep -i 'access-control'
# Expected: KHÔNG có Access-Control-Allow-Origin: * hoặc evil.example.com

# 3. Verify rate limit login hoạt động
for i in {1..10}; do
  curl -X POST https://your-demo-url.ngrok-free.app/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"wrong","password":"wrong"}' \
    -o /dev/null -w "Attempt $i: %{http_code}\n"
done
# Expected: Attempts 1-5: 401 → Attempts 6-10: 429

# 4. Verify cross-tenant isolation (cần 2 tokens)
TOKEN_A=$(curl -s -X POST .../auth/login -d '{"email":"owner1@..."}' | jq -r .access_token)
TOKEN_B_TENANT_ID=2  # Tenant của owner2
curl -X GET https://.../merchant/tiers \
  -H "Authorization: Bearer $TOKEN_A" \
  -H "X-Tenant-Id: $TOKEN_B_TENANT_ID" \
  -w "\nStatus: %{http_code}\n"
# Expected: 403

# 5. Verify stack trace KHÔNG leak ở production
curl https://your-demo-url.ngrok-free.app/api/non-existent-endpoint -i
# Expected: 404 với generic message, KHÔNG có Python traceback
```

Verify checklist:
- [ ] HTTPS active (không http://)
- [ ] CORS reject unknown origin
- [ ] Rate limit 429 sau attempt thứ 6
- [ ] Cross-tenant 403
- [ ] Error response không có stack trace (DEBUG=false)

- [ ] **Task 10:** Commit fix nếu có

```bash
git commit -m "fix(deploy): CORS + ngrok same-origin tunnel + security smoke test"
```

---

## PHASE 4 — Viết Báo Cáo PDF

### Tasks 11-15: 5 chương báo cáo

> **Tool khuyến nghị:** Markdown + Pandoc → PDF (đơn giản, version control). Hoặc Microsoft Word nếu trường yêu cầu template.

- [ ] **Task 11:** Setup template báo cáo
  - Create `docs/bao-cao/bao-cao.md`
  - Trang bìa với info: tên đề tài, sinh viên, MSSV, giảng viên hướng dẫn, năm
  - Mục lục auto-gen

- [ ] **Task 12:** **Chương 1 — Mở đầu** (~5 trang)
  - 1.1. Lý do chọn đề tài
  - 1.2. Mục tiêu
  - 1.3. Phạm vi (MVP 8 tuần + hướng phát triển luận văn)
  - 1.4. Đối tượng người dùng (4 vai trò)
  - 1.5. Phương pháp nghiên cứu

- [ ] **Task 13:** **Chương 2 — Phân tích & Thiết kế** (~10-15 trang)
  - 2.1. Phân tích nghiệp vụ (loyalty program là gì, vì sao SME cần)
  - 2.2. Use Case Diagram (4 actors, 38 use cases — copy từ `docs/mo-ta-so-do.md`)
  - 2.3. ERD (14 entities — copy từ spec)
  - 2.4. Sequence Diagrams cho 5 luồng quan trọng:
    - Luồng B (tạo thành viên qua SĐT)
    - Luồng C (tích điểm qua QR)
    - Luồng D (đổi điểm lấy quà)
    - Luồng E (claim voucher)
    - Luồng F (voucher sinh nhật)
  - 2.5. Multi-tenant architecture diagram

- [ ] **Task 14:** **Chương 3 — Cài đặt** (~10-15 trang)
  - 3.1. Công nghệ sử dụng (FastAPI, SQLAlchemy, Next.js, PostgreSQL, Tailwind, ...)
  - 3.2. Kiến trúc hệ thống (3 tầng: Frontend / Backend / Database)
  - 3.3. Cơ sở dữ liệu (14 bảng + indexes + DB trigger append-only)
  - 3.4. API endpoints (list ~80 endpoints)
  - 3.5. Bảo mật:
    - JWT + refresh token rotation
    - bcrypt password
    - HMAC verification code
    - Rate limiting với slowapi
    - Cross-tenant isolation
    - DB trigger append-only point_ledger
  - 3.6. Frontend modules (4 routes: /admin, /merchant, /pos, /member)
  - 3.7. Code highlights (5-10 đoạn code quan trọng nhất)

- [ ] **Task 15:** **Chương 4 — Kết quả thử nghiệm** (~10 trang) + **Chương 5 — Kết luận** (~3 trang)
  - 4.1. Môi trường thử nghiệm
  - 4.2. Kết quả test (180+ tests pass với pytest screenshots)
  - 4.3. Performance benchmark (`ab` results bảng)
  - 4.4. Lighthouse PWA score
  - 4.5. Screenshots các chức năng (10-15 hình)
  - 4.6. Demo scenario (link tới demo URL)
  - 5.1. Kết luận
  - 5.2. Hướng phát triển (ML segmentation, mobile native, public API)
  - **Tài liệu tham khảo** (FastAPI docs, Next.js docs, SQLAlchemy docs, OWASP, ...)

- [ ] **Task 15.b:** Convert Markdown → PDF với Pandoc

```bash
cd D:/DoAn/docs/bao-cao
pandoc bao-cao.md -o bao-cao.pdf \
  --toc --toc-depth=3 \
  --pdf-engine=xelatex \
  -V geometry:margin=2cm \
  -V mainfont="Times New Roman" \
  -V fontsize=13pt
```

> Nếu Pandoc/LaTeX phức tạp, dùng VS Code extension "Markdown PDF" hoặc Typora export PDF.

```bash
git add docs/bao-cao/
git commit -m "docs: hoàn thiện báo cáo 5 chương ~50 trang"
```

---

## PHASE 5 — Slide Demo

### Tasks 16-19: Tạo slide presentation

> **Tool khuyến nghị:** Marp (Markdown → slides) hoặc Slidev (Vue), hoặc PowerPoint truyền thống.

- [ ] **Task 16:** Tạo `docs/slide-demo/slide-demo.md` với Marp syntax

```markdown
---
marp: true
theme: default
paginate: true
---

# Loyalty Platform
## Xây dựng Website tích điểm thành viên và quản lý khuyến mãi cho SME

Sinh viên: ...
GVHD: ...

---

# Tổng quan

- Nền tảng đa người thuê (multi-tenant)
- 4 vai trò: Super Admin, Owner, Staff, Customer
- Stack: FastAPI + Next.js + PostgreSQL + PWA
- 180+ tests pass · CI/CD

---

# Vấn đề

- SME muốn loyalty program nhưng tự xây tốn $$$
- Giải pháp hiện tại: cứng nhắc, đắt đỏ, khó tích hợp
- Cần: nền tảng SaaS multi-tenant đơn giản

---

# Giải pháp

[Architecture diagram]

- Backend FastAPI async
- Frontend Next.js + PWA cho khách
- Multi-tenant qua X-Tenant-Id header
- Point ledger append-only (DB trigger)

---

# DEMO

(Switch sang demo scenario)

---

# Kiến trúc

[Architecture diagram]

---

# Bảo mật

- JWT + refresh token rotation
- bcrypt cost ≥ 12
- HMAC verification code
- Cross-tenant isolation tests
- DB trigger append-only ledger

---

# Kết quả

- 180+ tests pass
- p95 < 500ms
- Lighthouse PWA ≥ 85
- Multi-tenant verified

---

# Hướng phát triển (Luận văn)

- ML phân khúc khách (RFM + K-means)
- Dự báo churn
- Mobile app React Native
- Public API + webhook

---

# Q&A

Demo URL: https://...
GitHub: https://...
Báo cáo: bao-cao.pdf
```

- [ ] **Task 17:** Generate PDF từ Marp

```bash
cd D:/DoAn/docs/slide-demo
npx @marp-team/marp-cli slide-demo.md -o slide-demo.pdf
```

- [ ] **Task 18:** Cũng export `.pptx` nếu trường yêu cầu

```bash
npx @marp-team/marp-cli slide-demo.md -o slide-demo.pptx
```

- [ ] **Task 19:** Commit

```bash
git add docs/slide-demo/
git commit -m "docs: thêm slide demo (Marp + PDF + pptx)"
```

---

## PHASE 6 — Diagrams cho Báo Cáo

### Tasks 20-22: Vẽ diagrams + chèn vào báo cáo

- [ ] **Task 20:** Vẽ Use Case Diagram
  - Tool: draw.io (https://app.diagrams.net) — UML Use Case template
  - 4 actors + 38 use cases (xem `docs/mo-ta-so-do.md`)
  - Export PNG → save `docs/bao-cao/images/usecase.png`

- [ ] **Task 21:** Vẽ ERD
  - Tool: draw.io ERD template hoặc dbdiagram.io
  - 14 entities với relationships (xem `docs/mo-ta-so-do.md` Section 2)
  - Export PNG → `docs/bao-cao/images/erd.png`

- [ ] **Task 22:** Vẽ 5 Sequence Diagrams
  - Mỗi luồng (B, C, D, E, F) — paste Mermaid code từ `docs/mo-ta-so-do.md` Section 3 vào https://mermaid.live → export PNG
  - Save `docs/bao-cao/images/sequence-luong-{b,c,d,e,f}.png`
  - Vẽ thêm Architecture Diagram cho Section 3.2 spec

```bash
git add docs/bao-cao/images/
git commit -m "docs: thêm diagrams use case + ERD + sequence cho báo cáo"
```

---

## PHASE 7 — Milestone Review #4 với Giảng Viên

### Tasks 23-25: Bảo vệ nháp + ghi nhận feedback

- [ ] **Task 23:** Hẹn lịch milestone #4 với giảng viên (đầu hoặc giữa tuần 8)
  - Email/Zalo
  - Đem demo: laptop + điện thoại + báo cáo PDF + slide

- [ ] **Task 24:** Demo bảo vệ nháp ~30 phút
  - Slide tổng quan (10 phút)
  - Live demo (15 phút) theo `demo-scenario.md`
  - Q&A (5 phút)

- [ ] **Task 25:** Ghi nhận feedback giảng viên vào `docs/milestone-4-feedback.md`
  - Câu hỏi đã trả lời được
  - Câu hỏi chưa trả lời được → research thêm
  - Feedback về báo cáo (cần sửa gì)
  - Feedback về slide
  - Feedback về demo

```bash
git add docs/milestone-4-feedback.md
git commit -m "docs: ghi nhận feedback milestone #4 với giảng viên"
```

---

## PHASE 8 — Final Cleanup + Tag

### Tasks 26-28: Final commits + tag

- [ ] **Task 26:** Cập nhật README.md với:
  - Demo URL
  - Default credentials
  - Link báo cáo PDF
  - Link slide demo
  - Status: "Tuần 8 hoàn thành — sẵn sàng bảo vệ"

- [ ] **Task 27:** Apply final fixes từ feedback giảng viên (nếu có)
  - **CHỈ apply nếu là Critical** (vd: typo trong báo cáo, broken URL)
  - **KHÔNG code feature mới**

- [ ] **Task 28:** Push CI + tag final

```bash
cd D:/DoAn
git add README.md
git commit -m "docs: cập nhật README cho final submission"
git push origin main
git tag tuan-8-final
git push origin tuan-8-final
```

Verify CI xanh trên GitHub.

---

## Tổng kết Tuần 8

### Đã hoàn thành (28 tasks)

- ✅ Seed v3 với data realistic (200 transactions, names Việt Nam)
- ✅ Demo URL public chạy được (Docker + ngrok HOẶC VPS)
- ✅ Smoke test deploy URL pass
- ✅ Báo cáo PDF ~30-50 trang với 5 chương
- ✅ Slide demo ~15 slides (Marp PDF + pptx)
- ✅ Diagrams: use case + ERD + 5 sequence + architecture
- ✅ Demo scenario script 15-20 phút
- ✅ Milestone Review #4 với giảng viên xong + feedback ghi nhận
- ✅ README final
- ✅ Tag `tuan-8-final` push GitHub
- ✅ CI xanh

### Acceptance criteria

- [x] Demo URL accessible từ Internet
- [x] Báo cáo PDF in được, đầy đủ 5 chương
- [x] Slide demo dùng được khi bảo vệ
- [x] Demo scenario chạy trơn tru
- [x] Giảng viên feedback positive (hoặc note items rõ ràng)
- [x] Tất cả deliverables push GitHub

---

## Sau tuần 8 — Bảo vệ chính thức

Sau khi hoàn thành 8 tuần:

1. **Bảo vệ chính thức** trước Hội đồng (trường tổ chức)
2. **Nộp báo cáo** bản in (theo format trường)
3. **Lưu trữ source code** + tất cả docs lên GitHub public hoặc private (cho portfolio)
4. **Cân nhắc** chuyển hướng sang luận văn:
   - ML segmentation (RFM + K-means)
   - Dự báo churn
   - Mobile native React Native
   - Public API + webhook
5. **Reflection:** ghi nhận bài học (tự đánh giá process, what worked/what didn't)

---

## Kết luận 8 tuần

| Tuần | Focus | Tasks | Tests |
|---|---|---|---|
| 1 | Foundation + Auth + Frontend setup | 40 | 25 |
| 2 | Multi-tenant + Tenants/Staff/Tiers | 58 | +35 |
| 3 | Members + Transactions + Ledger | 44 | +30 |
| 4 | QR + Rewards + Redemption | 50 | +30 |
| 5 | Campaigns + Vouchers + Birthday | 42 | +30 |
| 6 | Analytics + Dashboard + Polish | 34 | +20 |
| 7 | QA + Performance + Bug fix | 33 | +10 |
| 8 | Deploy + Báo cáo + Demo | 28 | — |
| **Total** | **8 tuần** | **329 tasks** | **~180 tests** |

**Giả định:** ~25 giờ/tuần × 8 tuần ≈ 200 giờ. Sản phẩm đầu ra: full multi-tenant loyalty platform với ~12,000 LOC backend + ~12,000 LOC frontend, 180+ tests, CI/CD, deploy URL, báo cáo + slide.

**Sẵn sàng cho:**
- Bảo vệ thực tập tốt nghiệp
- Portfolio
- Chuyển hướng sang luận văn (ML / mobile / public API)
