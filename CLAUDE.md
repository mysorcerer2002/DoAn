# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**Loyalty Platform** — Multi-tenant loyalty/rewards system for Vietnamese SMEs (cafés, restaurants, retail, beauty). Customers earn points at member shops, redeem rewards, and claim campaign vouchers. This is an internship thesis project ("Đồ án thực tập").

**Domain vocabulary:** tenant = shop, member/membership = customer-at-a-shop, tier = hạng thành viên, campaign = chiến dịch khuyến mãi, voucher = phiếu giảm giá, redemption = đổi quà, transaction = giao dịch POS.

Commit messages and UI copy are in **Vietnamese**.

## Stack

- **Backend**: FastAPI + SQLAlchemy 2.0 async + asyncpg + Alembic + Pydantic v2 + slowapi + APScheduler + python-jose (JWT) + bcrypt
- **Frontend**: Next.js 14 App Router + TypeScript + Tailwind v4 + shadcn/ui + TanStack Query + Zustand + react-hook-form + zod + Serwist (PWA) + qrcode.react
- **DB**: PostgreSQL 15
- **Infra**: Docker Compose (dev + prod), Cloudflare Tunnel in prod to `loyalty.ecom-bill.com`

## Commands

### Dev environment (local)
```bash
docker compose up -d --build            # start postgres + backend + frontend
curl http://localhost:8000/health       # verify backend
# Frontend: http://localhost:3000, Backend: http://localhost:8000
```

### Prod environment (the actively running one in this repo)
```bash
cd D:/DoAn
# Rebuild + restart a single service
docker compose -p loyalty-prod -f docker-compose.prod.yml build backend
docker compose -p loyalty-prod -f docker-compose.prod.yml up -d backend
# Same for `frontend`. Migrations auto-run on backend startup.
docker logs loyalty-backend-prod --tail 30
docker exec loyalty-postgres-prod psql -U loyalty -d loyalty -c "SELECT ..."
```
Prod URL: `https://loyalty.ecom-bill.com`. Rate limit defaults: login 30/min, register 20/min (raised for dev-in-prod testing — see task #183).

### Backend tests
```bash
cd backend
pytest -v                               # all tests
pytest tests/unit -v                    # unit only
pytest tests/integration -v             # integration (uses testcontainers postgres)
pytest tests/integration/test_auth_api.py::test_login_success -v   # single test
```

### Frontend
```bash
cd frontend
npx tsc --noEmit                        # type-check (preferred quick sanity check)
npm run lint
npm run build                           # full prod build
```

### Alembic migrations
```bash
# Migrations auto-run on container startup. Manual:
docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend alembic upgrade head
docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend alembic revision -m "msg"
```
Revisions live in `backend/alembic/versions/`. Follow the existing hex-id pattern (`e6f7a8b9c0d1_<name>.py`) and set `down_revision` to the current head.

## Architecture — the parts that span files

### Multi-tenant scoping

Every non-public API route is scoped by **one tenant**, selected via the `X-Tenant-Id` request header. The backend never infers tenant from the user — the client must send it. Auth dependencies in `backend/app/core/deps.py` enforce membership:

- `get_current_user` → extracts user from JWT
- `get_tenant_id` → parses `X-Tenant-Id`
- `require_staff_in_tenant` → user must be staff OR owner of that tenant
- `require_owner_in_tenant` → user must be owner (stricter — most read-list endpoints use this, POS actions allow staff)
- `require_customer_in_tenant` → user must have a membership in that tenant
- `require_super_admin` → user.system_role == `super_admin` (admin panel only)

Changing which dep an endpoint uses directly shifts who can call it. When modifying, always check the caller role story (owner-only vs staff-allowed vs customer-facing).

### Backend layering (thin routes, fat services)

```
app/api/<resource>.py       — FastAPI routers. Parse request, call service, map errors → HTTPException, return schema.
app/services/<resource>_service.py — Business logic. Raise domain exceptions (e.g. VoucherNotFoundError).
app/models/<resource>.py    — SQLAlchemy 2.0 ORM. Mapped[] annotations. TimestampMixin from base.py.
app/schemas/<resource>.py   — Pydantic v2 request/response DTOs.
app/core/                   — config, db session, deps, security (JWT+bcrypt), limiter, qr.
app/jobs/                   — APScheduler jobs (birthday voucher, etc.). Disabled by default via ENABLE_SCHEDULER.
```

Services receive an `AsyncSession` in `__init__`. API routes catch service exceptions and map to HTTP status — look at any existing endpoint (e.g. `api/tenants.py` → `TenantService.get_tenant_by_id` + `TenantNotFoundError`) for the pattern.

### Global exception handler

`backend/app/main.py` has a global handler that converts `sqlalchemy.exc.IntegrityError` into 409 with a Vietnamese message based on which unique constraint was violated (phone/email/slug). Don't add 500-catching try/except at the route level just for uniqueness — let the handler do it. Do add **local** try/except if you want a specific Vietnamese error per field.

### Frontend route groups

```
src/app/(auth)      — /login, /register, /register/merchant            — public, no chrome
src/app/(member)    — /member/*                                        — customer app (mobile-first, BottomNavBar)
src/app/(merchant)  — /merchant/*                                      — shop owner dashboard (sidebar, desktop)
src/app/(staff)     — /staff/*                                         — staff POS (emerald theme, limited to POS actions)
src/app/(admin)     — /admin/*                                         — super admin portal
```

Each group has its own `layout.tsx`. The (member) layout wraps in `max-w-md` + `BottomNavBar`. The (merchant) / (admin) layouts render a desktop sidebar. The BottomNavBar hides itself on `/member/qr` and `/member/vouchers/[id]` via pathname regex — add similar guards when adding focused detail views.

### Frontend API + auth state

- `src/lib/api.ts` — axios instance with JWT interceptor; on 401 redirects to `/login`
- `src/lib/api-merchant.ts` — grouped API clients used by the merchant/staff dashboards
- `src/lib/auth-store.ts` (Zustand) — tokens, `fetchMe()`, current user
- `src/lib/tenant-store.ts` (Zustand) — currently selected tenant, injects `X-Tenant-Id` header
- `src/lib/hooks/` — TanStack Query hooks per resource, used by pages

Merchant/staff pages call `useTenantStore` to get the active tenant and include the header via axios interceptor. Customer ("/member/*") pages use a separate customer API path (`/users/me/*`) that doesn't need `X-Tenant-Id` — the backend resolves by membership list for the user.

### Key domain invariants

- **Voucher.code** uniqueness is enforced per-tenant; `VoucherService.claim` uses an atomic `UPDATE ... WHERE issued_count < max_issuances` pattern to prevent TOCTOU over-issuance, plus a partial unique index to prevent duplicate active-voucher-per-member-per-campaign.
- **Campaign.discount_type** and **Voucher.status** are currently declared `Mapped[Enum]` but stored as `String(20)` — callers must defensively handle either `str` or `Enum` when reading. Task #183 tracks the fix to use `SQLEnum(..., native_enum=False)` properly.
- **Tenant slug** is auto-generated in `TenantService.create_tenant` from the name with a LIKE-prefix uniqueness check.
- **Rate limiter** in `app/core/limiter.py` keys by `X-Forwarded-For` — trust boundary is the reverse proxy / Cloudflare Tunnel. Don't expose the backend directly.

## Workflow rules for this repo

- **Between tasks, run `superpowers:code-reviewer` and fix Critical/Important feedback before starting the next task.** Don't batch multiple features then review at the end. (Memory: `feedback_workflow_between_tasks.md`)
- **Do NOT run `gitnexus analyze` immediately after each commit.** A PostToolUse hook handles index refresh; running it inline wastes time. Only run manually at end of session or when a GitNexus tool reports stale.
- **All commit messages in Vietnamese.**
- **GitNexus tools are mandatory before edits** — see the GitNexus section below. Use `gitnexus_impact` before modifying any symbol, `gitnexus_detect_changes` before committing.

## Stitch (design tool)

When generating Stitch screens (e.g. for new frontend pages), always pass `modelId: "GEMINI_3_1_PRO"`. Stitch often times out — when it does, don't blindly retry; call `list_screens` first and verify whether the screen was actually created. If Stitch is unreliable for a given task, hand-code against the documented design system instead (see the Loyalty Platform design system stored under project `9962421755172378085`).

## Demo accounts (seeded via `backend/seed_demo.py`)

| Role | Email | Password |
|------|-------|----------|
| Super admin | `admin@loyalty.vn` | `admin1234` |
| Shop owner (Cafe Cộng) | `owner@cafe.vn` | `owner1234` |
| Shop owner (Lala Food) | `owner@lala.vn` | `owner1234` |
| Customer | `khach1@gmail.com` – `khach5@gmail.com` | `khach1234` |
| Customer (Lala) | `lala1@gmail.com` – `lala5@gmail.com` | `khach1234` |

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **DoAn** (2982 symbols, 7188 relationships, 163 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## When Debugging

1. `gitnexus_query({query: "<error or symptom>"})` — find execution flows related to the issue
2. `gitnexus_context({name: "<suspect function>"})` — see all callers, callees, and process participation
3. `READ gitnexus://repo/DoAn/process/{processName}` — trace the full execution flow step by step
4. For regressions: `gitnexus_detect_changes({scope: "compare", base_ref: "main"})` — see what your branch changed

## When Refactoring

- **Renaming**: MUST use `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` first. Review the preview — graph edits are safe, text_search edits need manual review. Then run with `dry_run: false`.
- **Extracting/Splitting**: MUST run `gitnexus_context({name: "target"})` to see all incoming/outgoing refs, then `gitnexus_impact({target: "target", direction: "upstream"})` to find all external callers before moving code.
- After any refactor: run `gitnexus_detect_changes({scope: "all"})` to verify only expected files changed.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Tools Quick Reference

| Tool | When to use | Command |
|------|-------------|---------|
| `query` | Find code by concept | `gitnexus_query({query: "auth validation"})` |
| `context` | 360-degree view of one symbol | `gitnexus_context({name: "validateUser"})` |
| `impact` | Blast radius before editing | `gitnexus_impact({target: "X", direction: "upstream"})` |
| `detect_changes` | Pre-commit scope check | `gitnexus_detect_changes({scope: "staged"})` |
| `rename` | Safe multi-file rename | `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` |
| `cypher` | Custom graph queries | `gitnexus_cypher({query: "MATCH ..."})` |

## Impact Risk Levels

| Depth | Meaning | Action |
|-------|---------|--------|
| d=1 | WILL BREAK — direct callers/importers | MUST update these |
| d=2 | LIKELY AFFECTED — indirect deps | Should test |
| d=3 | MAY NEED TESTING — transitive | Test if critical path |

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/DoAn/context` | Codebase overview, check index freshness |
| `gitnexus://repo/DoAn/clusters` | All functional areas |
| `gitnexus://repo/DoAn/processes` | All execution flows |
| `gitnexus://repo/DoAn/process/{name}` | Step-by-step execution trace |

## Self-Check Before Finishing

Before completing any code modification task, verify:
1. `gitnexus_impact` was run for all modified symbols
2. No HIGH/CRITICAL risk warnings were ignored
3. `gitnexus_detect_changes()` confirms changes match expected scope
4. All d=1 (WILL BREAK) dependents were updated

## Keeping the Index Fresh

After committing code changes, the GitNexus index becomes stale. Re-run analyze to update it:

```bash
gitnexus analyze
```

If the index previously included embeddings, preserve them by adding `--embeddings`:

```bash
gitnexus analyze --embeddings
```

To check whether embeddings exist, inspect `.gitnexus/meta.json` — the `stats.embeddings` field shows the count (0 means no embeddings). **Running analyze without `--embeddings` will delete any previously generated embeddings.**

> Claude Code users: A PostToolUse hook handles this automatically after `git commit` and `git merge`.

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
