# Loyalty Platform — Đồ án thực tập

Multi-tenant loyalty platform cho SME (cà phê, nhà hàng, shop bán lẻ).

## Stack
- Backend: FastAPI + PostgreSQL + SQLAlchemy 2.0 async + Alembic
- Frontend: Next.js 14 App Router + Tailwind CSS v4 + shadcn/ui + PWA
- Infra: Docker Compose

## Setup nhanh

```bash
# 1. Copy env files
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local

# 2. Start all services
docker compose up -d --build

# 3. Verify
curl http://localhost:8000/health
# Frontend: http://localhost:3000
```

## Run tests

```bash
cd backend
pytest -v
```

## Tài liệu
- Spec: `docs/superpowers/specs/2026-04-12-loyalty-platform-design.md`
- Danh sách tính năng: `docs/danh-sach-tinh-nang.md`
- Plans: `docs/superpowers/plans/`
