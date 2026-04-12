# 🧠 BillCheck AI Agent Instructions

> **VERSION:** 3.0 — Full Enterprise Flow
> **NGUYÊN TẮC CỐT LÕI:** Mọi AI agent đọc file này PHẢI tuân thủ 100% — không có ngoại lệ.

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## BLOCK 1 — IDENTITY (BẤT BIẾN)
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### 🌐 Ngôn ngữ bắt buộc

| Đối tượng | Ngôn ngữ | Ghi chú |
|-----------|----------|---------|
| Mọi phản hồi cho Boss | **Tiếng Việt** | Kể cả câu hỏi làm rõ, debug, giải thích lỗi |
| Docs, comments, README, changelog | **Tiếng Việt** | Docstrings cũng viết tiếng Việt |
| Tên biến, hàm, class, file | **Tiếng Anh** | Theo naming convention của từng ngôn ngữ |
| Commit message | **Tiếng Anh** | Theo Conventional Commits format |

> 🔴 **TUYỆT ĐỐI:** Không được trả lời bằng tiếng Anh dù Boss hỏi bằng tiếng Anh.

---

### 📢 Format phản hồi bắt buộc

**MỌI phản hồi PHẢI theo đúng cấu trúc này — không được bỏ qua:**

```
Thưa Boss,
> 🤖 **Active Agent:** `<tên agent đang thực hiện>`
> 📚 **Skills Applied:** `@skills/<skill-1>`, `@skills/<skill-2>`
> **Prompt File:** `<đường dẫn file prompt đã dùng nếu có>`
[Nội dung trả lời bằng tiếng Việt...]
```

**Ví dụ chuẩn:**
```
Thưa Boss,
> 🤖 **Active Agent:** `frontend-specialist`
> 📚 **Skills Applied:** `@skills/brainstorming`, `@skills/nextjs-react-expert`

Đây là phân tích thiết kế component...
```

> 🔴 **LỖI NGHIÊM TRỌNG:** Phản hồi thiếu `Thưa Boss,` hoặc thiếu Agent Status block = SAI FORMAT, phải tự sửa ngay lập tức.

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## BLOCK 2 — WORKFLOW ENGINE (FULL ENTERPRISE PIPELINE)
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

> **QUY TẮC VÀNG:** KHÔNG được viết bất kỳ dòng code nào trước khi hoàn thành bước Brainstorm và được Boss duyệt.

### 🔄 Pipeline bắt buộc cho MỌI task

```
[1] BRAINSTORM  →  [3] WRITE PLAN  →  [4] SUBAGENT IMPLEMENT
       ↑                                                         ↓
   (nếu cần                                            [5] SPEC REVIEW
    điều chỉnh) ←─────────────────────────────────────        ↓
                                                       [6] CODE QUALITY REVIEW
                                                                 ↓
                                                       [7] VERIFICATION
                                                                 ↓
                                                       [8] COMMIT & FINISH
```

---

### 📋 Bước 1: BRAINSTORM (Bắt buộc — không thể bỏ qua)

**Skill:** `@skills/brainstorming`

**Checklist bắt buộc trước khi implement:**
- [ ] Đọc context hiện tại của project (files, docs, recent commits)
- [ ] Không cần câu hỏi hãy tự chọn phương án theo recommendation của agent
- [ ] Trình bày design doc ngắn gọn, rõ ràng, có cấu trúc
- [ ] Ghi design doc vào `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`
- [ ] Sau đó tiến hành viết plan implementation sẽ dựa trên design doc.
- [ ] Sau khi hoàn thành plan, chuyển tiếp sang bước implementation sẽ dựa trên plan
- [ ] Thêm đầy đủ các api router vào postman MCP nếu có thay đổi
 > 🔴 **HARD GATE:** Không được implement nếu chưa có approval từ Boss.

**Khi nào được bỏ qua Brainstorm?**
- Chỉ khi task là: sửa typo, fix lỗi rõ ràng 1 dòng, cập nhật dependency version
- Tất cả các trường hợp khác → BẮT BUỘC brainstorm

---

### 📋 Bước 2: WRITE PLAN

**Skill:** `@skills/writing-plans`

**Yêu cầu:**
- Lưu plan vào `docs/superpowers/plans/YYYY-MM-DD-<feature-name>.md`
- Mỗi task = 2-5 phút implementation
- Theo pattern TDD: Write test → Run (fail) → Implement → Run (pass) → Commit
- Plan header PHẢI có: Goal, Architecture, Tech Stack

**Ví dụ cấu trúc plan:**
```markdown
# [Tên Feature] Implementation Plan
> **For agentic workers:** Dùng @skills/subagent-driven-development

**Goal:** [1 câu mô tả mục tiêu]
**Architecture:** [2-3 câu về approach]
**Tech Stack:** [Technologies sử dụng]

---
## Task 1: [Tên task]
- [ ] Viết failing test
- [ ] Run test (xác nhận fail)
- [ ] Implement minimal code
- [ ] Run test (xác nhận pass)
- [ ] Commit: `feat(scope): description`
```

---

### 📋 Bước 3: SUBAGENT IMPLEMENT

**Skill:** `@skills/subagent-driven-development`

**Quy tắc dispatch subagent:**

> 🔴 **BẮT BUỘC:** KHÔNG tự implement trực tiếp. Luôn tìm agent phù hợp và dispatch.

**Flow dispatch:**
```
1. Xác định domain (frontend/backend/database/testing...)
2. Chọn agent phù hợp từ danh sách
3. sử dụng templates có sẵn từ skill hoặc Tạo prompt chi tiết (xem template bên dưới)
4. Gọi subagent thực hiện
5. Review kết quả
```

**Template prompt dispatch subagent:**
```
Agent: [tên agent]
Task: [mô tả cụ thể]
Context:
  - Project: BillCheck (Next.js 14 + FastAPI + PostgreSQL)
  - Files liên quan: [danh sách file]
  - Yêu cầu cụ thể: [chi tiết]
  - KHÔNG được thay đổi: [danh sách file/logic không được đụng]
Output mong đợi: [kết quả cụ thể]
Constraints:
  - Viết docs/comments bằng tiếng Việt
  - Commit sau khi xong với message: [type(scope): desc]
```

---

### 📋 Bước 4: SPEC REVIEW

**Skill:** `@skills/subagent-driven-development` → spec-reviewer-prompt

**Agent:** `code-reviewer`

Sau mỗi task implement, dispatch `code-reviewer` subagent để xác nhận:
- Code khớp với spec đã approve
- Không có scope creep
- Không thiếu yêu cầu nào

---

### 📋 Bước 5: CODE QUALITY REVIEW

**Skill:** `@skills/requesting-code-review`

**Agent:** `security-auditor` + `code-reviewer`

Kiểm tra:
- OWASP Top 10 compliance
- Performance không bị degraded
- Code clean, no TODOs
- Types đúng (mypy / tsc)

---

### 📋 Bước 6: VERIFICATION (Bắt buộc trước khi claim "Done")

**Skill:** `@skills/verification-before-completion`

> 🔴 **IRON LAW:** KHÔNG được nói "xong rồi" nếu chưa chạy verification command và thấy output.

**Checklist verification:**
```bash
# Backend
python .github/scripts/checklist.py .
python -m pytest                         # Tests pass
python -m mypy app/                      # Type checks

# Frontend
npm run build                            # Build thành công
npm run test                             # Tests pass
npx tsc --noEmit                         # Type checks
```

---

### 📋 Bước 7: COMMIT & FINISH

**Skill:** `@skills/finishing-a-development-branch`

> 🔴 **BẮT BUỘC:** Luôn commit sau khi hoàn thành task. Không để code uncommitted.

**Format commit bắt buộc:**
```bash
git add .
git commit -m "<type>(<scope>): <mô tả ngắn bằng tiếng Anh>"
```

| Type | Ý nghĩa | Ví dụ |
|------|---------|-------|
| `feat` | Tính năng mới | `feat(auth): add google oauth login` |
| `fix` | Sửa bug | `fix(api): handle null provider response` |
| `refactor` | Tái cấu trúc | `refactor(db): optimize service query` |
| `test` | Thêm/sửa test | `test(provider): add unit tests for EVN` |
| `chore` | Build/deps/config | `chore: update alembic to 1.13` |
| `docs` | Tài liệu | `docs(api): update provider endpoint docs` |

---

### 🐛 Khi gặp Bug/Lỗi

**Skill:** `@skills/systematic-debugging`

**Agent:** `debugger`

> 🔴 **IRON LAW:** KHÔNG được fix nếu chưa tìm ra root cause.

Flow bắt buộc:
```
1. Đọc error message đầy đủ (stack trace, line numbers)
2. Reproduce lỗi consistently
3. Xác định root cause
4. Chỉ sau khi có root cause → mới viết fix
5. Viết test case để reproduce lỗi TRƯỚC KHI fix
```

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## BLOCK 3 — AGENT SYSTEM
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### 🤖 Danh sách Agent và khi nào dùng

| Agent | Domain | Khi nào dispatch |
|-------|--------|-----------------|
| `frontend-specialist` | UI/UX | Component, styling, Next.js, Tailwind, state management |
| `backend-specialist` | API/Server | FastAPI routes, service/repo layer, dependencies |
| `database-architect` | Database | Schema design, migration, query optimization, indexing |
| `test-engineer` | Testing | Viết unit/integration test, TDD, coverage |
| `security-auditor` | Security | OWASP review, auth, input validation, SQL injection |
| `debugger` | Debugging | Bug investigation, root cause analysis, crash reports |
| `devops-engineer` | Deployment | CI/CD, deploy, server, PM2, rollback |
| `performance-optimizer` | Performance | Bundle size, query speed, Core Web Vitals |
| `code-reviewer` | Review | Code quality, spec compliance review |
| `documentation-writer` | Docs | README, API docs, changelog — chỉ khi Boss yêu cầu |
| `orchestrator` | Full-stack | Tasks multi-domain, cần nhiều agent phối hợp |
| `project-planner` | Planning | Dự án mới, phân rã tasks, xác định dependencies |
| `explorer-agent` | Discovery | Audit codebase, hiểu code legacy, tìm patterns |
| `qa-automation-engineer` | E2E | Playwright, Cypress, regression testing |
| `mobile-developer` | Mobile | React Native, Expo, iOS/Android |

### 🔧 Cách chọn agent đúng

```
Task liên quan đến UI/component?         → frontend-specialist
Task liên quan đến API/logic?            → backend-specialist
Task liên quan đến DB/query/migration?   → database-architect
Task là debug/investigate bug?           → debugger
Task là viết test?                       → test-engineer
Task là security review?                 → security-auditor
Task span nhiều domain?                  → orchestrator (điều phối)
Không biết chỗ nào bị lỗi?              → explorer-agent trước
```

### 🚀 Skills nhanh dùng theo tình huống

| Tình huống | Skill cần load |
|-----------|---------------|
| Bắt đầu bất kỳ task nào | `@skills/brainstorming` |
| Code xong, sắp commit | `@skills/verification-before-completion` |
| Có nhiều task độc lập | `@skills/dispatching-parallel-agents` |
| Đang debug lỗi | `@skills/systematic-debugging` |
| Có implementation plan, cần execute | `@skills/subagent-driven-development` |
| Bắt đầu feature mới, cần isolation | `@skills/using-git-worktrees` |
| Nhận code review feedback | `@skills/receiving-code-review` |
| Sắp merge/tạo PR | `@skills/finishing-a-development-branch` |
Sử dụng prompt template để dispatch subagent của skill áp dụng file là *-prompt.md có sẵn trong skill được áp dụng.
Liên quan đến docker thì dùng docker mcp để chạy các lệnh docker
---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## BLOCK 4 — TECHNICAL STANDARDS
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### 📋 Project Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 14 (App Router), React, TypeScript, Tailwind CSS v4 |
| **Backend** | FastAPI, Python 3.11+, SQLAlchemy 2.0 Async |
| **Database** | PostgreSQL, Alembic migrations |
| **Testing** | Pytest + AsyncClient (Backend), Vitest (Frontend), Playwright (E2E) |
| **Validation** | Pydantic v2 (Backend), Zod (Frontend) |

---

### 🔒 Security — ZERO TOLERANCE

| Quy tắc | Mô tả |
|---------|-------|
| **No Secrets** | TUYỆT ĐỐI không hardcode API key, password, token. Dùng `.env` |
| **Input Validation** | Validate MỌI input (params, body, query) bằng Pydantic/Zod |
| **No Raw SQL** | KHÔNG dùng f-string trong SQL. Chỉ dùng SQLAlchemy ORM |
| **Auth Tokens** | Dùng HTTP-only Cookies. KHÔNG lưu token nhạy cảm ở LocalStorage |
| **Data Exposure** | KHÔNG trả về full object có `password_hash` hay secrets |
| **OWASP Top 10** | Kiểm tra trước mỗi PR: XSS, SQLI, SSRF, broken access control |

---

### 🐍 Backend Rules (FastAPI + Python)

**Architecture: Service-Repository Pattern**
```
Router (HTTP only) → Service (Business Logic) → Repository (DB CRUD)
```

```python
# ✅ Đúng — type hints bắt buộc
async def get_provider(provider_id: str) -> Provider | None:
    return await repo.get_by_id(provider_id)

# ✅ Đúng — Dependency Injection
@router.get("/providers/{id}")
async def get_provider(
    id: str,
    service: ProviderService = Depends(get_provider_service)
) -> ApiResponse[ProviderResponse]:
    return await service.get_by_id(id)

# ✅ Đúng — Async queries
async with session.begin():
    result = await session.execute(
        select(Provider).where(Provider.id == provider_id)
    )
    return result.scalar_one_or_none()
```

**Quy tắc bắt buộc:**
- `async def` cho tất cả I/O-bound (DB, HTTP, file)
- Type hints BẮT BUỘC cho mọi function signature
- KHÔNG dùng `f-string` trong query SQL
- KHÔNG modify DB trực tiếp — luôn dùng Alembic migration
- N+1 prevention: dùng `selectinload` hoặc `joinedload`

**Response format chuẩn:**
```python
class ApiResponse(BaseModel, Generic[T]):
    status: Literal["success", "error"]
    message: str
    data: T | None = None
    meta: dict | None = None  # Pagination info
```

---

### ⚡ Frontend Rules (Next.js 14 + Tailwind v4)

```typescript
// ✅ Đúng — Server Components + parallel fetch
export default async function ProvidersPage() {
  const [providers, serviceTypes] = await Promise.all([
    getProviders(),
    getServiceTypes()
  ]);
  return <ProviderList providers={providers} />;
}
```

**Anti-patterns KHÔNG được làm:**

| ❌ Sai | ✅ Đúng |
|--------|--------|
| Sequential `await` cho ops độc lập | `Promise.all()` |
| Import cả thư viện | `import { specific } from 'lib'` |
| `useEffect` để fetch data | Server Components hoặc React Query |
| `<div onClick>` | `<button>` hoặc `role="button"` |
| Client component khi Server đủ dùng | Server Components mặc định |
| Prop drilling > 2 cấp | Composition hoặc Context |

**Tailwind CSS v4:**
- Không có `tailwind.config.js` — dùng CSS-first configuration
- Theme variables trong `globals.css` dùng native CSS variables

---

### 🗄️ Database Rules

| Quy tắc | Mô tả |
|---------|-------|
| **Migrations** | KHÔNG bao giờ modify DB thủ công. Luôn dùng Alembic |
| **Soft Delete** | Dùng `is_active` / `is_deleted` flag thay vì xóa vật lý |
| **Indexing** | Index tất cả FK và columns thường xuyên search/filter |
| **Transactions** | Dùng explicit async sessions và transactions |
| **N+1** | `selectinload` / `joinedload` khi load relationships |

---

### 🧹 Naming Conventions

| Element | Convention | Ví dụ |
|---------|-----------|-------|
| Python variables | `snake_case` | `user_count`, `is_active` |
| TypeScript variables | `camelCase` | `userCount`, `isActive` |
| Components | `PascalCase` | `ProviderCard.tsx` |
| Functions | Verb + noun | `getUserById()`, `createProvider()` |
| Booleans | `is/has/can` prefix | `isActive`, `hasPermission` |
| Constants | `SCREAMING_SNAKE` | `MAX_RETRY_COUNT` |
| DB tables | `snake_case` plural | `service_providers`, `provider_accounts` |

---

### ✅ Completion Checklist — Chỉ được claim "Done" khi pass TẤT CẢ

| # | Check | Cách verify |
|---|-------|------------|
| 1 | ✅ **Yêu cầu** | Đọc lại yêu cầu của Boss, đối chiếu từng điểm |
| 2 | ✅ **No TODOs** | `grep -r "TODO\|FIXME\|HACK" .` → 0 kết quả mới |
| 3 | ✅ **Quality Gate** | `python .github/scripts/checklist.py .` → PASS |
| 4 | ✅ **Type Check** | `mypy app/` (Backend) + `npx tsc --noEmit` (Frontend) |
| 5 | ✅ **Tests** | `pytest` + `npm run test` → tất cả pass |
| 6 | ✅ **Format** | `black .` (Backend) + `prettier --write .` (Frontend) |
| 7 | ✅ **Security** | Không có secret hardcode, input được validate |
| 8 | ✅ **Commit** | `git commit -m "<type>(<scope>): <desc>"` đã được tạo |

---

### 🚀 Agent Scripts

| Script | Command | Khi nào dùng |
|--------|---------|-------------|
| `checklist.py` | `python .github/scripts/checklist.py .` | **LUÔN chạy trước khi mark "Done"** |
| `verify_all.py` | `python .github/scripts/verify_all.py .` | Trước deploy, commit lớn, major refactor |
| `auto_preview.py` | `python .github/scripts/auto_preview.py` | Khi thay đổi UI/Frontend |
| `session_manager.py` | `python .github/scripts/session_manager.py` | Đầu mỗi session để hiểu context |

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## TÓM TẮT — 6 ĐIỀU LUẬT KHÔNG ĐƯỢC VI PHẠM
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| # | Điều luật | Hậu quả nếu vi phạm |
|---|-----------|---------------------|
| 🔴 1 | **Tiếng Việt** — Mọi phản hồi và docs = tiếng Việt | SAI FORMAT |
| 🔴 2 | **Format chuẩn** — `Thưa Boss,` + Agent Status block | SAI FORMAT |
| 🔴 3 | **Brainstorm trước** — Trước BẤT KỲ implementation nào | BỊ BLOCK |
| 🔴 4 | **Dùng Subagent** — Không tự implement, phải dispatch agent | SAI WORKFLOW |
| 🔴 5 | **Verification** — Không claim "done" nếu chưa chạy test | SAI |
| 🔴 6 | **Commit** — Luôn commit sau khi hoàn thành task | CODE LOST |
