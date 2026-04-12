# Tuần 1 — Foundation & Auth Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Setup monorepo + Docker Compose + Backend FastAPI với auth (register/login/refresh) + JWT middleware + rate limiting + Frontend Next.js với login/register pages + PWA skeleton + GitHub Actions CI cơ bản.

**Architecture:**
- Monorepo `backend/` + `frontend/` + Docker Compose
- Backend: FastAPI async + SQLAlchemy 2.0 async + Alembic. Auth dùng JWT (access 15 phút stateless) + refresh token lưu DB. Rate limiting bằng `slowapi`
- Frontend: Next.js 14 App Router + TypeScript + Tailwind + shadcn/ui + Zustand. PWA skeleton bằng `@serwist/next` (disable trong dev)
- Postgres testcontainers cho integration test

**Tech Stack:**
- Python 3.11, FastAPI, SQLAlchemy 2.0 async, asyncpg, Alembic, Pydantic v2 + pydantic-settings, passlib[bcrypt], python-jose, slowapi, pytest + pytest-asyncio + httpx + testcontainers
- Next.js 14, TypeScript, Tailwind CSS, shadcn/ui, axios, zustand, react-hook-form + zod, @serwist/next
- Docker Compose, GitHub Actions

**Cuối tuần phải có:**
- Đăng nhập + đăng ký chạy được end-to-end (frontend gọi backend)
- Docker compose up một lệnh chạy được Postgres + backend + frontend
- Tests pass: register, login, refresh, rate limit
- CI GitHub Actions xanh

**Acceptance criteria:**
- `docker compose up -d` → backend `http://localhost:8000/health` trả `{"status":"ok"}`, frontend `http://localhost:3000` hiển thị landing
- POST `/auth/register` → tạo user, trả tokens
- POST `/auth/login` → trả access + refresh token
- POST `/auth/refresh` → trả access mới
- Rate limit `/auth/login` 5/phút/IP — request thứ 6 trả 429
- `cd backend && pytest` → all green
- Push code → GitHub Actions xanh

---

## Tổng quan các phase

| Phase | Task | Mô tả |
|---|---|---|
| 1 | 1-2 | Repo skeleton + .gitignore |
| 2 | 3-5 | Docker Compose + PostgreSQL |
| 3 | 6-11 | Backend setup (config, db, FastAPI hello) |
| 4 | 12-16 | User model + Alembic migration |
| 5 | 17-22 | Security utils (bcrypt, JWT) — TDD |
| 6 | 23-27 | Auth services (register, login, refresh) — TDD |
| 7 | 28-31 | Auth API endpoints + integration tests |
| 8 | 32-34 | JWT dependency + rate limiting |
| 9 | 35-39 | Frontend Next.js setup + layout |
| 10 | 40-43 | Frontend auth pages |
| 11 | 44 | PWA skeleton |
| 12 | 45 | GitHub Actions CI |
| 13 | 46 | Smoke test end-to-end |

---

## File Structure (sẽ tạo trong tuần này)

```
D:/DoAn/
├── .gitignore
├── README.md
├── docker-compose.yml
├── .github/workflows/ci.yml
├── backend/
│   ├── pyproject.toml
│   ├── Dockerfile
│   ├── .env.example
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   │       └── 001_create_users.py
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   ├── db.py
│   │   │   ├── security.py
│   │   │   ├── deps.py
│   │   │   └── limiter.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   └── user.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── auth.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   └── auth_service.py
│   │   └── api/
│   │       ├── __init__.py
│   │       └── auth.py
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       ├── unit/
│       │   ├── __init__.py
│       │   └── test_security.py
│       └── integration/
│           ├── __init__.py
│           └── test_auth_api.py
└── frontend/
    ├── package.json
    ├── tsconfig.json
    ├── next.config.mjs
    ├── tailwind.config.ts
    ├── postcss.config.mjs
    ├── components.json
    ├── .env.example
    ├── public/
    │   ├── manifest.json
    │   └── icons/
    │       ├── icon-192.png
    │       └── icon-512.png
    └── src/
        ├── app/
        │   ├── layout.tsx
        │   ├── page.tsx
        │   ├── globals.css
        │   └── (auth)/
        │       ├── login/page.tsx
        │       └── register/page.tsx
        ├── components/
        │   └── ui/
        ├── lib/
        │   ├── api.ts
        │   └── auth-store.ts
        └── types/
            └── auth.ts
```

---

## PHASE 1 — Repo Setup

### Task 1: Tạo cấu trúc thư mục gốc + .gitignore

**Files:**
- Create: `D:/DoAn/.gitignore`
- Create: `D:/DoAn/README.md`

- [ ] **Step 1: Init git repo nếu chưa có**

```bash
cd D:/DoAn
git init
```

- [ ] **Step 2: Tạo `.gitignore`**

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.venv/
venv/
env/
*.egg-info/
.pytest_cache/
.coverage
htmlcov/
.ruff_cache/

# Node
node_modules/
.next/
out/
.turbo/
*.log
npm-debug.log*

# IDE
.vscode/
.idea/
*.swp
*.swo

# Env
.env
.env.local
.env.*.local
!.env.example

# Backend specific
backend/uploads/
backend/logs/
*.sqlite

# OS
.DS_Store
Thumbs.db

# Docker
.docker/
```

- [ ] **Step 3: Tạo `README.md` skeleton**

```markdown
# Loyalty Platform — Đồ án thực tập

Multi-tenant loyalty platform cho SME (cà phê, nhà hàng, shop bán lẻ).

## Stack
- Backend: FastAPI + PostgreSQL + SQLAlchemy 2.0 async
- Frontend: Next.js 14 App Router + Tailwind + shadcn/ui + PWA
- Infra: Docker Compose

## Setup nhanh

```bash
docker compose up -d
# Backend: http://localhost:8000
# Frontend: http://localhost:3000
# Postgres: localhost:5432
```

## Tài liệu
- Spec: `docs/superpowers/specs/2026-04-12-loyalty-platform-design.md`
- Danh sách tính năng: `docs/danh-sach-tinh-nang.md`
- Plans: `docs/superpowers/plans/`
```

- [ ] **Step 4: Commit**

```bash
git add .gitignore README.md
git commit -m "chore: init repo with gitignore and README skeleton"
```

---

### Task 2: Tạo skeleton folders backend + frontend

**Files:**
- Create: `D:/DoAn/backend/.gitkeep`
- Create: `D:/DoAn/frontend/.gitkeep`

- [ ] **Step 1: Tạo folders**

```bash
cd D:/DoAn
mkdir -p backend frontend
touch backend/.gitkeep frontend/.gitkeep
```

- [ ] **Step 2: Commit**

```bash
git add backend/ frontend/
git commit -m "chore: add backend and frontend skeleton folders"
```

---

## PHASE 2 — Docker Compose + PostgreSQL

### Task 3: Tạo docker-compose.yml với Postgres

**Files:**
- Create: `D:/DoAn/docker-compose.yml`
- Create: `D:/DoAn/.env.example`

- [ ] **Step 1: Tạo `docker-compose.yml`**

```yaml
services:
  postgres:
    image: postgres:15-alpine
    container_name: loyalty-postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-loyalty}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-loyalty_dev}
      POSTGRES_DB: ${POSTGRES_DB:-loyalty}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-loyalty}"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

- [ ] **Step 2: Tạo `.env.example` ở root**

```bash
# Postgres
POSTGRES_USER=loyalty
POSTGRES_PASSWORD=loyalty_dev
POSTGRES_DB=loyalty
```

- [ ] **Step 3: Commit**

```bash
git add docker-compose.yml .env.example
git commit -m "chore: add docker-compose with postgres 15"
```

---

### Task 4: Khởi động Postgres và verify

- [ ] **Step 1: Start Postgres**

```bash
cd D:/DoAn
docker compose up -d postgres
```

Expected output: `Container loyalty-postgres Started`

- [ ] **Step 2: Check health**

```bash
docker compose ps
```

Expected: `loyalty-postgres` status `running (healthy)` sau ~10 giây.

- [ ] **Step 3: Test connection bằng psql trong container**

```bash
docker compose exec postgres psql -U loyalty -d loyalty -c "SELECT version();"
```

Expected: hiển thị `PostgreSQL 15.x`

- [ ] **Step 4: KHÔNG commit (chỉ verify, không có file mới)**

---

### Task 5: Tạo backend/.env.example

**Files:**
- Create: `D:/DoAn/backend/.env.example`

- [ ] **Step 1: Tạo file**

```bash
# Database
DATABASE_URL=postgresql+asyncpg://loyalty:loyalty_dev@localhost:5432/loyalty

# JWT
JWT_SECRET=change-me-to-random-32-bytes-via-openssl-rand-hex-32
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# App
APP_NAME=loyalty-platform
DEBUG=true
ENVIRONMENT=development

# Scheduler (Tuần 5 dùng)
ENABLE_SCHEDULER=false

# CORS
FRONTEND_ORIGINS=http://localhost:3000
```

- [ ] **Step 2: Commit**

```bash
git add backend/.env.example
git commit -m "chore: add backend .env.example"
```

---

## PHASE 3 — Backend Setup

### Task 6: Tạo `backend/pyproject.toml` với dependencies

**Files:**
- Create: `D:/DoAn/backend/pyproject.toml`

- [ ] **Step 1: Tạo file**

```toml
[project]
name = "loyalty-backend"
version = "0.1.0"
description = "Loyalty platform backend"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "sqlalchemy[asyncio]>=2.0.36",
    "asyncpg>=0.29.0",
    "alembic>=1.13.0",
    "pydantic>=2.9.0",
    "pydantic-settings>=2.6.0",
    "passlib[bcrypt]>=1.7.4",
    "python-jose[cryptography]>=3.3.0",
    "slowapi>=0.1.9",
    "python-multipart>=0.0.12",
    "cachetools>=5.5.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "httpx>=0.27.0",
    "testcontainers[postgres]>=4.8.0",
    "ruff>=0.7.0",
    "black>=24.10.0",
    "pip-audit>=2.7.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]

[tool.ruff]
line-length = 100
target-version = "py311"
[tool.ruff.lint]
select = ["E", "F", "W", "I", "B", "UP"]
ignore = ["E501"]

[tool.black]
line-length = 100
target-version = ["py311"]
```

- [ ] **Step 2: Tạo virtualenv và install**

```bash
cd D:/DoAn/backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
# source .venv/bin/activate

pip install --upgrade pip
pip install -e ".[dev]"
```

Expected: Cài thành công, không lỗi.

- [ ] **Step 3: Commit**

```bash
git add backend/pyproject.toml
git commit -m "chore(backend): add pyproject.toml with dependencies"
```

---

### Task 7: Tạo `app/core/config.py` với Pydantic Settings

**Files:**
- Create: `D:/DoAn/backend/app/__init__.py`
- Create: `D:/DoAn/backend/app/core/__init__.py`
- Create: `D:/DoAn/backend/app/core/config.py`

- [ ] **Step 1: Tạo `app/__init__.py` (empty)**

```python
```

- [ ] **Step 2: Tạo `app/core/__init__.py` (empty)**

```python
```

- [ ] **Step 3: Tạo `app/core/config.py`**

```python
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "loyalty-platform"
    environment: str = "development"
    debug: bool = True

    database_url: str

    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    enable_scheduler: bool = False
    frontend_origins: str = "http://localhost:3000"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.frontend_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 4: Verify import**

```bash
cd D:/DoAn/backend
cp .env.example .env
python -c "from app.core.config import get_settings; print(get_settings().app_name)"
```

Expected: `loyalty-platform`

- [ ] **Step 5: Commit**

```bash
git add backend/app/__init__.py backend/app/core/__init__.py backend/app/core/config.py
git commit -m "feat(backend): add Pydantic settings module"
```

---

### Task 8: Tạo `app/core/db.py` với async SQLAlchemy session

**Files:**
- Create: `D:/DoAn/backend/app/core/db.py`

- [ ] **Step 1: Tạo file**

```python
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yields an async DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

- [ ] **Step 2: Verify import**

```bash
cd D:/DoAn/backend
python -c "from app.core.db import engine; print(engine.url)"
```

Expected: `postgresql+asyncpg://loyalty:***@localhost:5432/loyalty`

- [ ] **Step 3: Commit**

```bash
git add backend/app/core/db.py
git commit -m "feat(backend): add async SQLAlchemy session factory"
```

---

### Task 9: Tạo `app/main.py` với FastAPI hello world + health endpoint

**Files:**
- Create: `D:/DoAn/backend/app/main.py`

- [ ] **Step 1: Tạo file**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name}
```

- [ ] **Step 2: Chạy uvicorn local để test**

```bash
cd D:/DoAn/backend
uvicorn app.main:app --reload --port 8000
```

- [ ] **Step 3: Test endpoint trong terminal khác**

```bash
curl http://localhost:8000/health
```

Expected: `{"status":"ok","app":"loyalty-platform"}`

- [ ] **Step 4: Stop uvicorn (Ctrl+C)**

- [ ] **Step 5: Commit**

```bash
git add backend/app/main.py
git commit -m "feat(backend): add FastAPI app with /health endpoint"
```

---

### Task 10: Tạo Backend Dockerfile

**Files:**
- Create: `D:/DoAn/backend/Dockerfile`

- [ ] **Step 1: Tạo file**

```dockerfile
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps cho asyncpg/bcrypt build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps trước (cache layer)
COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install -e ".[dev]"

# Copy source
COPY . .

# Entrypoint chạy migration trước rồi start uvicorn
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
```

- [ ] **Step 2: Commit**

```bash
git add backend/Dockerfile
git commit -m "chore(backend): add Dockerfile"
```

---

### Task 11: Cập nhật docker-compose.yml thêm backend service

**Files:**
- Modify: `D:/DoAn/docker-compose.yml`

- [ ] **Step 1: Update file**

```yaml
services:
  postgres:
    image: postgres:15-alpine
    container_name: loyalty-postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-loyalty}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-loyalty_dev}
      POSTGRES_DB: ${POSTGRES_DB:-loyalty}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-loyalty}"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: loyalty-backend
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql+asyncpg://loyalty:loyalty_dev@postgres:5432/loyalty
      JWT_SECRET: ${JWT_SECRET:-change-me-in-production-32-bytes-min}
      JWT_ALGORITHM: HS256
      ACCESS_TOKEN_EXPIRE_MINUTES: 15
      REFRESH_TOKEN_EXPIRE_DAYS: 7
      ENVIRONMENT: development
      DEBUG: "true"
      ENABLE_SCHEDULER: "false"
      FRONTEND_ORIGINS: http://localhost:3000
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app

volumes:
  postgres_data:
```

- [ ] **Step 2: Test build**

```bash
cd D:/DoAn
docker compose build backend
```

Expected: Build thành công, không lỗi (lưu ý lần đầu mất ~3-5 phút).

- [ ] **Step 3: Commit (CHƯA up vì cần migration trước)**

```bash
git add docker-compose.yml
git commit -m "chore: add backend service to docker-compose"
```

---

## PHASE 4 — User Model + Alembic Migration

### Task 12: Tạo `app/models/base.py` với declarative base

**Files:**
- Create: `D:/DoAn/backend/app/models/__init__.py`
- Create: `D:/DoAn/backend/app/models/base.py`

- [ ] **Step 1: Tạo `app/models/__init__.py` (empty)**

```python
```

- [ ] **Step 2: Tạo `app/models/base.py`**

```python
from datetime import datetime

from sqlalchemy import DateTime, MetaData
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/models/__init__.py backend/app/models/base.py
git commit -m "feat(backend): add SQLAlchemy declarative base with naming convention"
```

---

### Task 13: Tạo `app/models/user.py`

**Files:**
- Create: `D:/DoAn/backend/app/models/user.py`

- [ ] **Step 1: Tạo file**

```python
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    birthday: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_shadow: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    system_role: Mapped[str] = mapped_column(String(20), default="regular", nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
```

- [ ] **Step 2: Update `app/models/__init__.py` để export User**

```python
from app.models.user import User

__all__ = ["User"]
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/models/user.py backend/app/models/__init__.py
git commit -m "feat(backend): add User model"
```

---

### Task 14: Init Alembic

**Files:**
- Create: `D:/DoAn/backend/alembic.ini`
- Create: `D:/DoAn/backend/alembic/env.py`
- Create: `D:/DoAn/backend/alembic/script.py.mako`
- Create: `D:/DoAn/backend/alembic/versions/.gitkeep`

- [ ] **Step 1: Init alembic**

```bash
cd D:/DoAn/backend
alembic init alembic
```

Sẽ tạo `alembic.ini` + thư mục `alembic/`.

- [ ] **Step 2: Sửa `alembic.ini` — set `sqlalchemy.url`**

Tìm dòng `sqlalchemy.url = driver://user:pass@localhost/dbname` và thay bằng:

```ini
sqlalchemy.url = postgresql+asyncpg://loyalty:loyalty_dev@localhost:5432/loyalty
```

- [ ] **Step 3: Sửa `alembic/env.py` để hỗ trợ async + auto-detect models**

Thay toàn bộ nội dung `alembic/env.py` bằng:

```python
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from app.core.config import get_settings
from app.models.base import Base
from app.models import *  # noqa: F401, F403 — import all models for autogenerate

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override URL từ settings (env var)
config.set_main_option("sqlalchemy.url", get_settings().database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 4: Commit**

```bash
git add backend/alembic.ini backend/alembic/
git commit -m "chore(backend): init alembic with async support"
```

---

### Task 15: Generate first migration cho User table

- [ ] **Step 1: Đảm bảo Postgres chạy**

```bash
cd D:/DoAn
docker compose up -d postgres
```

- [ ] **Step 2: Generate migration**

```bash
cd D:/DoAn/backend
alembic revision --autogenerate -m "create users table"
```

Expected: file mới `alembic/versions/<hash>_create_users_table.py` được tạo.

- [ ] **Step 3: Đọc file migration vừa sinh, verify nội dung tạo bảng `users` đầy đủ với các cột**

File migration nên có `op.create_table('users', ...)` với các cột: id, email, phone, password_hash, full_name, birthday, is_active, is_shadow, system_role, last_login_at, created_at.

- [ ] **Step 4: Apply migration**

```bash
alembic upgrade head
```

Expected output: `Running upgrade  -> <hash>, create users table`

- [ ] **Step 5: Verify trong DB**

```bash
cd D:/DoAn
docker compose exec postgres psql -U loyalty -d loyalty -c "\d users"
```

Expected: hiển thị schema bảng `users` với đầy đủ cột.

- [ ] **Step 6: Commit migration file**

```bash
cd D:/DoAn
git add backend/alembic/versions/
git commit -m "feat(backend): migration create users table"
```

---

### Task 16: Tạo Pydantic schemas cho auth

**Files:**
- Create: `D:/DoAn/backend/app/schemas/__init__.py`
- Create: `D:/DoAn/backend/app/schemas/auth.py`

- [ ] **Step 1: Tạo `app/schemas/__init__.py` (empty)**

```python
```

- [ ] **Step 2: Tạo `app/schemas/auth.py`**

```python
from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    full_name: str = Field(min_length=1, max_length=255)
    birthday: date | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str | None
    full_name: str | None
    birthday: date | None
    system_role: str
    created_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/schemas/__init__.py backend/app/schemas/auth.py
git commit -m "feat(backend): add auth Pydantic schemas"
```

---

## PHASE 5 — Security Utils (TDD)

### Task 17: Setup pytest + conftest.py

**Files:**
- Create: `D:/DoAn/backend/tests/__init__.py`
- Create: `D:/DoAn/backend/tests/conftest.py`
- Create: `D:/DoAn/backend/tests/unit/__init__.py`
- Create: `D:/DoAn/backend/tests/integration/__init__.py`

- [ ] **Step 1: Tạo các `__init__.py` (empty)**

```python
```

- [ ] **Step 2: Tạo `tests/conftest.py` cơ bản (sẽ mở rộng sau)**

```python
import pytest


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"
```

- [ ] **Step 3: Verify pytest chạy được (chưa có test)**

```bash
cd D:/DoAn/backend
pytest -v
```

Expected: `no tests ran in 0.0Xs`

- [ ] **Step 4: Commit**

```bash
git add backend/tests/
git commit -m "test(backend): setup pytest skeleton"
```

---

### Task 18: TDD — Bcrypt hash + verify

**Files:**
- Create: `D:/DoAn/backend/tests/unit/test_security.py`
- Create: `D:/DoAn/backend/app/core/security.py`

- [ ] **Step 1: Viết failing test cho hash + verify password**

Tạo `tests/unit/test_security.py`:

```python
from app.core.security import hash_password, verify_password


def test_hash_password_returns_different_hash_each_time():
    h1 = hash_password("supersecret123")
    h2 = hash_password("supersecret123")
    assert h1 != h2  # bcrypt has random salt
    assert h1.startswith("$2b$")


def test_verify_password_correct():
    pwd = "supersecret123"
    hashed = hash_password(pwd)
    assert verify_password(pwd, hashed) is True


def test_verify_password_incorrect():
    hashed = hash_password("supersecret123")
    assert verify_password("wrongpassword", hashed) is False
```

- [ ] **Step 2: Run test — verify FAIL**

```bash
cd D:/DoAn/backend
pytest tests/unit/test_security.py -v
```

Expected: `ImportError: cannot import name 'hash_password' from 'app.core.security'`

- [ ] **Step 3: Implement `app/core/security.py`**

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
```

- [ ] **Step 4: Run test — verify PASS**

```bash
pytest tests/unit/test_security.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/security.py backend/tests/unit/test_security.py
git commit -m "feat(backend): add bcrypt password hashing with tests"
```

---

### Task 19: TDD — JWT create + decode access token

**Files:**
- Modify: `D:/DoAn/backend/tests/unit/test_security.py`
- Modify: `D:/DoAn/backend/app/core/security.py`

- [ ] **Step 1: Thêm failing tests cho JWT**

Append vào `tests/unit/test_security.py`:

```python
from datetime import datetime, timedelta, timezone

import pytest
from jose import JWTError

from app.core.security import create_access_token, decode_token


def test_create_access_token_returns_string():
    token = create_access_token(user_id=42)
    assert isinstance(token, str)
    assert len(token.split(".")) == 3  # JWT has 3 parts


def test_decode_valid_access_token():
    token = create_access_token(user_id=42)
    payload = decode_token(token)
    assert payload["sub"] == "42"
    assert payload["type"] == "access"
    assert "exp" in payload


def test_decode_invalid_token_raises():
    with pytest.raises(JWTError):
        decode_token("invalid.token.here")


def test_decode_expired_token_raises():
    token = create_access_token(user_id=42, expires_delta=timedelta(seconds=-1))
    with pytest.raises(JWTError):
        decode_token(token)
```

- [ ] **Step 2: Run test — verify FAIL**

```bash
pytest tests/unit/test_security.py -v
```

Expected: 4 new tests fail with `ImportError: cannot import name 'create_access_token'`

- [ ] **Step 3: Update `app/core/security.py`**

```python
from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: int, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload = {
        "sub": str(user_id),
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
```

- [ ] **Step 4: Run test — verify PASS**

```bash
pytest tests/unit/test_security.py -v
```

Expected: 7 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/security.py backend/tests/unit/test_security.py
git commit -m "feat(backend): add JWT create/decode access + refresh tokens"
```

---

## PHASE 6 — Auth Services (TDD with PostgreSQL testcontainer)

### Task 20: Setup conftest.py với PostgreSQL testcontainer

**Files:**
- Modify: `D:/DoAn/backend/tests/conftest.py`

- [ ] **Step 1: Update conftest.py**

```python
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer

from app.models.base import Base


@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:15-alpine") as container:
        yield container


@pytest.fixture(scope="session")
def database_url(postgres_container):
    sync_url = postgres_container.get_connection_url()
    # testcontainers returns sync url, convert to async
    return sync_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://").replace(
        "postgresql://", "postgresql+asyncpg://"
    )


@pytest_asyncio.fixture(scope="session")
async def engine(database_url):
    eng = create_async_engine(database_url, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Mỗi test có 1 session riêng, rollback ở cuối để isolate."""
    async with engine.connect() as connection:
        transaction = await connection.begin()
        async_session = async_sessionmaker(
            bind=connection, class_=AsyncSession, expire_on_commit=False
        )
        async with async_session() as session:
            yield session
        await transaction.rollback()
```

- [ ] **Step 2: Verify import OK**

```bash
cd D:/DoAn/backend
python -c "from tests.conftest import postgres_container; print('OK')"
```

Expected: `OK` (không lỗi).

- [ ] **Step 3: Commit**

```bash
git add backend/tests/conftest.py
git commit -m "test(backend): setup PostgreSQL testcontainer fixtures"
```

---

### Task 21: TDD — Register service

**Files:**
- Create: `D:/DoAn/backend/tests/integration/test_auth_service.py`
- Create: `D:/DoAn/backend/app/services/__init__.py`
- Create: `D:/DoAn/backend/app/services/auth_service.py`

- [ ] **Step 1: Tạo `app/services/__init__.py` (empty)**

```python
```

- [ ] **Step 2: Viết failing test register**

Tạo `tests/integration/test_auth_service.py`:

```python
import pytest
from sqlalchemy import select

from app.models.user import User
from app.schemas.auth import RegisterRequest
from app.services.auth_service import AuthService, EmailAlreadyExistsError


@pytest.mark.asyncio
async def test_register_creates_user(db_session):
    service = AuthService(db_session)
    request = RegisterRequest(
        email="alice@example.com",
        password="supersecret123",
        full_name="Alice",
    )
    user = await service.register(request)
    assert user.id is not None
    assert user.email == "alice@example.com"
    assert user.full_name == "Alice"
    assert user.password_hash != "supersecret123"
    assert user.is_active is True
    assert user.is_shadow is False
    assert user.system_role == "regular"


@pytest.mark.asyncio
async def test_register_duplicate_email_raises(db_session):
    service = AuthService(db_session)
    req1 = RegisterRequest(email="bob@example.com", password="pass12345", full_name="Bob")
    await service.register(req1)
    await db_session.flush()

    req2 = RegisterRequest(email="bob@example.com", password="other12345", full_name="Bob2")
    with pytest.raises(EmailAlreadyExistsError):
        await service.register(req2)
```

- [ ] **Step 3: Run test — verify FAIL**

```bash
cd D:/DoAn/backend
pytest tests/integration/test_auth_service.py -v
```

Expected: ImportError `cannot import name 'AuthService'`.

- [ ] **Step 4: Implement `app/services/auth_service.py`**

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User
from app.schemas.auth import RegisterRequest


class EmailAlreadyExistsError(Exception):
    pass


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, request: RegisterRequest) -> User:
        # Check email exists
        existing = await self.db.scalar(select(User).where(User.email == request.email))
        if existing is not None:
            raise EmailAlreadyExistsError(f"Email {request.email} already registered")

        user = User(
            email=request.email,
            password_hash=hash_password(request.password),
            full_name=request.full_name,
            birthday=request.birthday,
            is_active=True,
            is_shadow=False,
            system_role="regular",
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user
```

- [ ] **Step 5: Run test — verify PASS**

```bash
pytest tests/integration/test_auth_service.py -v
```

Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/ backend/tests/integration/test_auth_service.py
git commit -m "feat(backend): add register auth service with TDD"
```

---

### Task 22: TDD — Login service

**Files:**
- Modify: `D:/DoAn/backend/tests/integration/test_auth_service.py`
- Modify: `D:/DoAn/backend/app/services/auth_service.py`

- [ ] **Step 1: Append failing tests login**

Thêm vào cuối `test_auth_service.py`:

```python
from app.services.auth_service import InvalidCredentialsError


@pytest.mark.asyncio
async def test_login_with_correct_credentials(db_session):
    service = AuthService(db_session)
    await service.register(
        RegisterRequest(email="charlie@example.com", password="pass12345", full_name="Charlie")
    )
    await db_session.flush()

    user = await service.authenticate(email="charlie@example.com", password="pass12345")
    assert user is not None
    assert user.email == "charlie@example.com"
    assert user.last_login_at is not None  # đã update last_login_at


@pytest.mark.asyncio
async def test_login_with_wrong_password_raises(db_session):
    service = AuthService(db_session)
    await service.register(
        RegisterRequest(email="dave@example.com", password="pass12345", full_name="Dave")
    )
    await db_session.flush()

    with pytest.raises(InvalidCredentialsError):
        await service.authenticate(email="dave@example.com", password="wrongpass")


@pytest.mark.asyncio
async def test_login_with_nonexistent_email_raises(db_session):
    service = AuthService(db_session)
    with pytest.raises(InvalidCredentialsError):
        await service.authenticate(email="nobody@example.com", password="anything")
```

- [ ] **Step 2: Run test — verify FAIL**

```bash
pytest tests/integration/test_auth_service.py -v
```

Expected: 3 new tests fail with import error.

- [ ] **Step 3: Update `app/services/auth_service.py`**

Add to file:

```python
from datetime import datetime, timezone

from app.core.security import hash_password, verify_password


class EmailAlreadyExistsError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, request: RegisterRequest) -> User:
        existing = await self.db.scalar(select(User).where(User.email == request.email))
        if existing is not None:
            raise EmailAlreadyExistsError(f"Email {request.email} already registered")

        user = User(
            email=request.email,
            password_hash=hash_password(request.password),
            full_name=request.full_name,
            birthday=request.birthday,
            is_active=True,
            is_shadow=False,
            system_role="regular",
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def authenticate(self, email: str, password: str) -> User:
        user = await self.db.scalar(select(User).where(User.email == email))
        if user is None or user.password_hash is None:
            raise InvalidCredentialsError("Invalid email or password")
        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password")
        if not user.is_active:
            raise InvalidCredentialsError("Account is disabled")

        user.last_login_at = datetime.now(timezone.utc)
        await self.db.flush()
        return user
```

- [ ] **Step 4: Run test — verify PASS**

```bash
pytest tests/integration/test_auth_service.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/auth_service.py backend/tests/integration/test_auth_service.py
git commit -m "feat(backend): add login authenticate with TDD"
```

---

## PHASE 7 — Auth API Endpoints

### Task 23: Tạo `/auth/register` endpoint với integration test

**Files:**
- Create: `D:/DoAn/backend/tests/integration/test_auth_api.py`
- Create: `D:/DoAn/backend/app/api/__init__.py`
- Create: `D:/DoAn/backend/app/api/auth.py`
- Modify: `D:/DoAn/backend/app/main.py`
- Modify: `D:/DoAn/backend/tests/conftest.py`

- [ ] **Step 1: Mở rộng `conftest.py` thêm fixture HTTP client**

Append vào `tests/conftest.py`:

```python
from httpx import ASGITransport, AsyncClient

from app.core.db import get_db
from app.main import app


@pytest_asyncio.fixture
async def client(db_session) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
```

- [ ] **Step 2: Tạo `app/api/__init__.py` (empty)**

```python
```

- [ ] **Step 3: Viết failing test cho POST /auth/register**

Tạo `tests/integration/test_auth_api.py`:

```python
import pytest


@pytest.mark.asyncio
async def test_register_endpoint_creates_user_and_returns_tokens(client):
    response = await client.post(
        "/auth/register",
        json={
            "email": "alice@example.com",
            "password": "supersecret123",
            "full_name": "Alice",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email_returns_409(client):
    payload = {
        "email": "bob@example.com",
        "password": "pass12345",
        "full_name": "Bob",
    }
    r1 = await client.post("/auth/register", json=payload)
    assert r1.status_code == 201

    r2 = await client.post("/auth/register", json=payload)
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_register_invalid_email_returns_422(client):
    response = await client.post(
        "/auth/register",
        json={"email": "not-email", "password": "pass12345", "full_name": "X"},
    )
    assert response.status_code == 422
```

- [ ] **Step 4: Run test — verify FAIL**

```bash
cd D:/DoAn/backend
pytest tests/integration/test_auth_api.py -v
```

Expected: 404 (router chưa tồn tại).

- [ ] **Step 5: Tạo `app/api/auth.py`**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import create_access_token, create_refresh_token
from app.schemas.auth import RegisterRequest, TokenResponse
from app.services.auth_service import AuthService, EmailAlreadyExistsError

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    service = AuthService(db)
    try:
        user = await service.register(request)
    except EmailAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e

    return TokenResponse(
        access_token=create_access_token(user_id=user.id),
        refresh_token=create_refresh_token(user_id=user.id),
    )
```

- [ ] **Step 6: Update `app/main.py` để register router**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth as auth_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name, debug=settings.debug)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name}
```

- [ ] **Step 7: Run test — verify PASS**

```bash
pytest tests/integration/test_auth_api.py -v
```

Expected: 3 passed.

- [ ] **Step 8: Commit**

```bash
git add backend/app/api/ backend/app/main.py backend/tests/conftest.py backend/tests/integration/test_auth_api.py
git commit -m "feat(backend): add POST /auth/register endpoint"
```

---

### Task 24: Tạo `/auth/login` endpoint

**Files:**
- Modify: `D:/DoAn/backend/tests/integration/test_auth_api.py`
- Modify: `D:/DoAn/backend/app/api/auth.py`

- [ ] **Step 1: Append failing tests**

```python
@pytest.mark.asyncio
async def test_login_with_correct_credentials_returns_tokens(client):
    await client.post(
        "/auth/register",
        json={"email": "charlie@example.com", "password": "pass12345", "full_name": "Charlie"},
    )
    response = await client.post(
        "/auth/login",
        json={"email": "charlie@example.com", "password": "pass12345"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_with_wrong_password_returns_401(client):
    await client.post(
        "/auth/register",
        json={"email": "dave@example.com", "password": "pass12345", "full_name": "Dave"},
    )
    response = await client.post(
        "/auth/login",
        json={"email": "dave@example.com", "password": "wrong"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_email_returns_401(client):
    response = await client.post(
        "/auth/login",
        json={"email": "nobody@example.com", "password": "anything"},
    )
    assert response.status_code == 401
```

- [ ] **Step 2: Run test — verify FAIL**

```bash
pytest tests/integration/test_auth_api.py -v
```

Expected: 3 new tests fail with 405 (login endpoint chưa có).

- [ ] **Step 3: Update `app/api/auth.py` thêm login endpoint**

Append vào file:

```python
from app.schemas.auth import LoginRequest
from app.services.auth_service import InvalidCredentialsError


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    service = AuthService(db)
    try:
        user = await service.authenticate(email=request.email, password=request.password)
    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)
        ) from e

    return TokenResponse(
        access_token=create_access_token(user_id=user.id),
        refresh_token=create_refresh_token(user_id=user.id),
    )
```

- [ ] **Step 4: Run test — verify PASS**

```bash
pytest tests/integration/test_auth_api.py -v
```

Expected: 6 passed (3 cũ + 3 mới).

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/auth.py backend/tests/integration/test_auth_api.py
git commit -m "feat(backend): add POST /auth/login endpoint"
```

---

### Task 25: Tạo `/auth/refresh` endpoint

**Files:**
- Modify: `D:/DoAn/backend/tests/integration/test_auth_api.py`
- Modify: `D:/DoAn/backend/app/api/auth.py`

- [ ] **Step 1: Append failing tests**

```python
@pytest.mark.asyncio
async def test_refresh_token_returns_new_access_token(client):
    register_response = await client.post(
        "/auth/register",
        json={"email": "eve@example.com", "password": "pass12345", "full_name": "Eve"},
    )
    refresh_token = register_response.json()["refresh_token"]

    response = await client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["refresh_token"] == refresh_token  # refresh token vẫn giữ nguyên


@pytest.mark.asyncio
async def test_refresh_with_invalid_token_returns_401(client):
    response = await client.post(
        "/auth/refresh",
        json={"refresh_token": "invalid.token.here"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_with_access_token_returns_401(client):
    register_response = await client.post(
        "/auth/register",
        json={"email": "frank@example.com", "password": "pass12345", "full_name": "Frank"},
    )
    access_token = register_response.json()["access_token"]

    response = await client.post(
        "/auth/refresh",
        json={"refresh_token": access_token},
    )
    assert response.status_code == 401  # token type=access không refresh được
```

- [ ] **Step 2: Run test — verify FAIL**

```bash
pytest tests/integration/test_auth_api.py -v
```

Expected: 3 new tests fail.

- [ ] **Step 3: Update `app/api/auth.py` thêm refresh endpoint**

Append vào file:

```python
from jose import JWTError

from app.core.security import decode_token
from app.schemas.auth import RefreshRequest


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    try:
        payload = decode_token(request.refresh_token)
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        ) from e

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is not a refresh token"
        )

    user_id = int(payload["sub"])
    return TokenResponse(
        access_token=create_access_token(user_id=user_id),
        refresh_token=request.refresh_token,
    )
```

- [ ] **Step 4: Run test — verify PASS**

```bash
pytest tests/integration/test_auth_api.py -v
```

Expected: 9 passed (6 cũ + 3 mới).

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/auth.py backend/tests/integration/test_auth_api.py
git commit -m "feat(backend): add POST /auth/refresh endpoint"
```

---

## PHASE 8 — JWT Dependency + Rate Limiting

### Task 26: TDD — `get_current_user` dependency

**Files:**
- Create: `D:/DoAn/backend/app/core/deps.py`
- Modify: `D:/DoAn/backend/tests/integration/test_auth_api.py`
- Modify: `D:/DoAn/backend/app/api/auth.py`

- [ ] **Step 1: Append failing test cho endpoint /auth/me**

```python
@pytest.mark.asyncio
async def test_me_with_valid_token_returns_user(client):
    register = await client.post(
        "/auth/register",
        json={"email": "grace@example.com", "password": "pass12345", "full_name": "Grace"},
    )
    access_token = register.json()["access_token"]

    response = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "grace@example.com"
    assert data["full_name"] == "Grace"


@pytest.mark.asyncio
async def test_me_without_token_returns_401(client):
    response = await client.get("/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_with_invalid_token_returns_401(client):
    response = await client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert response.status_code == 401
```

- [ ] **Step 2: Run test — verify FAIL**

```bash
pytest tests/integration/test_auth_api.py -v
```

Expected: 3 new tests fail with 404.

- [ ] **Step 3: Tạo `app/core/deps.py`**

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import decode_token
from app.models.user import User

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(credentials.credentials)
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is not an access token",
        )

    user_id = int(payload["sub"])
    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user
```

- [ ] **Step 4: Update `app/api/auth.py` thêm `/me` endpoint**

```python
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.auth import UserResponse


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
```

- [ ] **Step 5: Run test — verify PASS**

```bash
pytest tests/integration/test_auth_api.py -v
```

Expected: 12 passed.

- [ ] **Step 6: Commit**

```bash
git add backend/app/core/deps.py backend/app/api/auth.py backend/tests/integration/test_auth_api.py
git commit -m "feat(backend): add get_current_user dependency and /auth/me endpoint"
```

---

### Task 27: Setup slowapi rate limiter

**Files:**
- Create: `D:/DoAn/backend/app/core/limiter.py`
- Modify: `D:/DoAn/backend/app/main.py`
- Modify: `D:/DoAn/backend/app/api/auth.py`

- [ ] **Step 1: Tạo `app/core/limiter.py`**

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
```

- [ ] **Step 2: Update `app/main.py` để wire limiter**

Update file:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api import auth as auth_router
from app.core.config import get_settings
from app.core.limiter import limiter

settings = get_settings()

app = FastAPI(title=settings.app_name, debug=settings.debug)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=429,
        content={"detail": f"Rate limit exceeded: {exc.detail}"},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name}
```

- [ ] **Step 3: Apply rate limit cho endpoint login**

Update `app/api/auth.py` — login endpoint:

```python
from fastapi import Request

from app.core.limiter import limiter


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,  # CẦN cho slowapi (caveat 6.7)
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    service = AuthService(db)
    try:
        user = await service.authenticate(email=body.email, password=body.password)
    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)
        ) from e

    return TokenResponse(
        access_token=create_access_token(user_id=user.id),
        refresh_token=create_refresh_token(user_id=user.id),
    )
```

- [ ] **Step 4: Run lại tests login (vì signature đổi `request` → `body`)**

```bash
pytest tests/integration/test_auth_api.py -v
```

Expected: tests cũ vẫn pass (httpx test client tự inject Request).

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/limiter.py backend/app/main.py backend/app/api/auth.py
git commit -m "feat(backend): add slowapi rate limiter on /auth/login (5/min/IP)"
```

---

### Task 28: TDD — Test rate limit hoạt động

**Files:**
- Modify: `D:/DoAn/backend/tests/integration/test_auth_api.py`

- [ ] **Step 1: Append test rate limit**

```python
@pytest.mark.asyncio
async def test_login_rate_limit_429_after_5_attempts(client):
    """6 login attempts trong < 1 phút → request thứ 6 phải trả 429."""
    payload = {"email": "nobody@example.com", "password": "wrong"}

    for i in range(5):
        response = await client.post("/auth/login", json=payload)
        assert response.status_code == 401, f"attempt {i+1} should be 401"

    # Attempt 6 → rate limit
    response = await client.post("/auth/login", json=payload)
    assert response.status_code == 429
```

- [ ] **Step 2: Run test**

```bash
pytest tests/integration/test_auth_api.py::test_login_rate_limit_429_after_5_attempts -v
```

Expected: PASS.

> Lưu ý: nếu test fail vì TestClient share IP `testclient`, cần config `key_func` riêng cho test. Nếu PASS thì OK.

- [ ] **Step 3: Commit**

```bash
git add backend/tests/integration/test_auth_api.py
git commit -m "test(backend): verify rate limit on /auth/login"
```

---

## PHASE 9 — Frontend Setup

### Task 29: Init Next.js với TypeScript + Tailwind

- [ ] **Step 1: Init Next.js**

```bash
cd D:/DoAn/frontend
npx create-next-app@14 . \
  --typescript \
  --tailwind \
  --app \
  --src-dir \
  --import-alias "@/*" \
  --no-eslint \
  --no-turbopack
```

Khi prompt hỏi overwrite: chọn No (nếu đã có file).

- [ ] **Step 2: Verify dev server chạy**

```bash
npm run dev
```

Expected: `http://localhost:3000` mở được, hiển thị Next.js welcome.

- [ ] **Step 3: Stop dev server (Ctrl+C)**

- [ ] **Step 4: Commit**

```bash
cd D:/DoAn
git add frontend/
git commit -m "chore(frontend): init Next.js 14 with TypeScript + Tailwind"
```

---

### Task 30: Install shadcn/ui + base components

- [ ] **Step 1: Init shadcn**

```bash
cd D:/DoAn/frontend
npx shadcn@latest init -d
```

Chọn defaults: New York style, Slate base color, CSS variables yes.

- [ ] **Step 2: Install các component cơ bản**

```bash
npx shadcn@latest add button input label card form toast
```

- [ ] **Step 3: Verify import được**

```bash
ls src/components/ui
```

Expected: thấy `button.tsx`, `input.tsx`, `label.tsx`, `card.tsx`, `form.tsx`, `toast.tsx`.

- [ ] **Step 4: Commit**

```bash
cd D:/DoAn
git add frontend/
git commit -m "chore(frontend): add shadcn/ui base components"
```

---

### Task 31: Tạo `frontend/.env.example`

**Files:**
- Create: `D:/DoAn/frontend/.env.example`

- [ ] **Step 1: Tạo file**

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

- [ ] **Step 2: Tạo `.env.local` từ `.env.example`**

```bash
cd D:/DoAn/frontend
cp .env.example .env.local
```

- [ ] **Step 3: Commit (chỉ `.env.example`, không commit `.env.local`)**

```bash
cd D:/DoAn
git add frontend/.env.example
git commit -m "chore(frontend): add .env.example"
```

---

### Task 32: Tạo API client với axios + types

**Files:**
- Create: `D:/DoAn/frontend/src/types/auth.ts`
- Create: `D:/DoAn/frontend/src/lib/api.ts`

- [ ] **Step 1: Install axios + zustand**

```bash
cd D:/DoAn/frontend
npm install axios zustand react-hook-form @hookform/resolvers zod
```

- [ ] **Step 2: Tạo `src/types/auth.ts`**

```typescript
export interface User {
  id: number;
  email: string | null;
  full_name: string | null;
  birthday: string | null;
  system_role: string;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
  birthday?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}
```

- [ ] **Step 3: Tạo `src/lib/api.ts`**

```typescript
import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";
import type { LoginRequest, RegisterRequest, TokenResponse, User } from "@/types/auth";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
});

// Request interceptor: attach access token nếu có
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (typeof window !== "undefined") {
    const token = sessionStorage.getItem("access_token");
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Response interceptor: handle 401 → refresh token (sẽ mở rộng tuần 2)
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      sessionStorage.removeItem("access_token");
      // TODO: refresh logic ở tuần sau
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  register: (data: RegisterRequest) => api.post<TokenResponse>("/auth/register", data),
  login: (data: LoginRequest) => api.post<TokenResponse>("/auth/login", data),
  refresh: (refreshToken: string) =>
    api.post<TokenResponse>("/auth/refresh", { refresh_token: refreshToken }),
  me: () => api.get<User>("/auth/me"),
};
```

- [ ] **Step 4: Commit**

```bash
cd D:/DoAn
git add frontend/src/types/ frontend/src/lib/api.ts frontend/package.json frontend/package-lock.json
git commit -m "feat(frontend): add API client with axios and auth types"
```

---

### Task 33: Tạo Zustand auth store

**Files:**
- Create: `D:/DoAn/frontend/src/lib/auth-store.ts`

- [ ] **Step 1: Tạo file**

```typescript
import { create } from "zustand";
import type { User } from "@/types/auth";
import { authApi } from "./api";

interface AuthState {
  user: User | null;
  isLoading: boolean;
  setTokens: (accessToken: string, refreshToken: string) => void;
  fetchMe: () => Promise<void>;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isLoading: false,

  setTokens: (accessToken, refreshToken) => {
    if (typeof window !== "undefined") {
      sessionStorage.setItem("access_token", accessToken);
      // refresh_token sẽ chuyển sang HttpOnly cookie ở tuần sau khi setup auth nâng cao
      sessionStorage.setItem("refresh_token", refreshToken);
    }
  },

  fetchMe: async () => {
    set({ isLoading: true });
    try {
      const { data } = await authApi.me();
      set({ user: data, isLoading: false });
    } catch {
      set({ user: null, isLoading: false });
    }
  },

  logout: () => {
    if (typeof window !== "undefined") {
      sessionStorage.removeItem("access_token");
      sessionStorage.removeItem("refresh_token");
    }
    set({ user: null });
  },
}));
```

- [ ] **Step 2: Commit**

```bash
cd D:/DoAn
git add frontend/src/lib/auth-store.ts
git commit -m "feat(frontend): add Zustand auth store"
```

---

### Task 34: Tạo layout chung + landing page

**Files:**
- Modify: `D:/DoAn/frontend/src/app/layout.tsx`
- Modify: `D:/DoAn/frontend/src/app/page.tsx`

- [ ] **Step 1: Update `src/app/layout.tsx`**

```typescript
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Loyalty Platform",
  description: "Multi-tenant loyalty platform cho SME",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="vi">
      <body className="min-h-screen bg-background text-foreground antialiased">
        {children}
      </body>
    </html>
  );
}
```

- [ ] **Step 2: Update `src/app/page.tsx`**

```typescript
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function HomePage() {
  return (
    <main className="container mx-auto flex min-h-screen flex-col items-center justify-center gap-6 px-4">
      <h1 className="text-4xl font-bold tracking-tight">Loyalty Platform</h1>
      <p className="text-muted-foreground">Multi-tenant loyalty cho SME</p>
      <div className="flex gap-4">
        <Button asChild>
          <Link href="/login">Đăng nhập</Link>
        </Button>
        <Button asChild variant="outline">
          <Link href="/register">Đăng ký</Link>
        </Button>
      </div>
    </main>
  );
}
```

- [ ] **Step 3: Test trên browser**

```bash
cd D:/DoAn/frontend
npm run dev
```

Mở `http://localhost:3000` — verify thấy "Loyalty Platform" + 2 nút.

- [ ] **Step 4: Stop dev server**

- [ ] **Step 5: Commit**

```bash
cd D:/DoAn
git add frontend/src/app/
git commit -m "feat(frontend): add landing page with login/register links"
```

---

## PHASE 10 — Frontend Auth Pages

### Task 35: Tạo trang Login

**Files:**
- Create: `D:/DoAn/frontend/src/app/(auth)/login/page.tsx`

- [ ] **Step 1: Tạo file**

```typescript
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

import { authApi } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";

const schema = z.object({
  email: z.string().email("Email không hợp lệ"),
  password: z.string().min(8, "Mật khẩu tối thiểu 8 ký tự"),
});

type FormData = z.infer<typeof schema>;

export default function LoginPage() {
  const router = useRouter();
  const setTokens = useAuthStore((s) => s.setTokens);
  const fetchMe = useAuthStore((s) => s.fetchMe);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = async (data: FormData) => {
    setError(null);
    setSubmitting(true);
    try {
      const res = await authApi.login(data);
      setTokens(res.data.access_token, res.data.refresh_token);
      await fetchMe();
      router.push("/");
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setError(err.response?.data?.detail || "Đăng nhập thất bại");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="container mx-auto flex min-h-screen items-center justify-center px-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Đăng nhập</CardTitle>
          <CardDescription>Đăng nhập vào tài khoản của bạn</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" {...register("email")} />
              {errors.email && (
                <p className="text-sm text-red-500">{errors.email.message}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Mật khẩu</Label>
              <Input id="password" type="password" {...register("password")} />
              {errors.password && (
                <p className="text-sm text-red-500">{errors.password.message}</p>
              )}
            </div>
            {error && <p className="text-sm text-red-500">{error}</p>}
            <Button type="submit" className="w-full" disabled={submitting}>
              {submitting ? "Đang đăng nhập..." : "Đăng nhập"}
            </Button>
            <p className="text-center text-sm text-muted-foreground">
              Chưa có tài khoản?{" "}
              <Link href="/register" className="underline">
                Đăng ký
              </Link>
            </p>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
```

- [ ] **Step 2: Test thủ công trên browser**

```bash
cd D:/DoAn/frontend
npm run dev
```

Mở `http://localhost:3000/login` — verify form hiển thị, validation hoạt động.

- [ ] **Step 3: Stop dev server**

- [ ] **Step 4: Commit**

```bash
cd D:/DoAn
git add frontend/src/app/
git commit -m "feat(frontend): add login page with react-hook-form + zod"
```

---

### Task 36: Tạo trang Register

**Files:**
- Create: `D:/DoAn/frontend/src/app/(auth)/register/page.tsx`

- [ ] **Step 1: Tạo file**

```typescript
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

import { authApi } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";

const schema = z.object({
  email: z.string().email("Email không hợp lệ"),
  password: z.string().min(8, "Mật khẩu tối thiểu 8 ký tự"),
  full_name: z.string().min(1, "Họ tên không được để trống"),
  birthday: z.string().optional(),
});

type FormData = z.infer<typeof schema>;

export default function RegisterPage() {
  const router = useRouter();
  const setTokens = useAuthStore((s) => s.setTokens);
  const fetchMe = useAuthStore((s) => s.fetchMe);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = async (data: FormData) => {
    setError(null);
    setSubmitting(true);
    try {
      const res = await authApi.register({
        ...data,
        birthday: data.birthday || undefined,
      });
      setTokens(res.data.access_token, res.data.refresh_token);
      await fetchMe();
      router.push("/");
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setError(err.response?.data?.detail || "Đăng ký thất bại");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="container mx-auto flex min-h-screen items-center justify-center px-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Đăng ký</CardTitle>
          <CardDescription>Tạo tài khoản mới</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="full_name">Họ tên</Label>
              <Input id="full_name" {...register("full_name")} />
              {errors.full_name && (
                <p className="text-sm text-red-500">{errors.full_name.message}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" {...register("email")} />
              {errors.email && (
                <p className="text-sm text-red-500">{errors.email.message}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Mật khẩu</Label>
              <Input id="password" type="password" {...register("password")} />
              {errors.password && (
                <p className="text-sm text-red-500">{errors.password.message}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="birthday">Sinh nhật (tuỳ chọn)</Label>
              <Input id="birthday" type="date" {...register("birthday")} />
            </div>
            {error && <p className="text-sm text-red-500">{error}</p>}
            <Button type="submit" className="w-full" disabled={submitting}>
              {submitting ? "Đang đăng ký..." : "Đăng ký"}
            </Button>
            <p className="text-center text-sm text-muted-foreground">
              Đã có tài khoản?{" "}
              <Link href="/login" className="underline">
                Đăng nhập
              </Link>
            </p>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
```

- [ ] **Step 2: Test thủ công**

```bash
cd D:/DoAn/frontend
npm run dev
```

Mở `http://localhost:3000/register`, verify form hiển thị.

- [ ] **Step 3: Stop dev server**

- [ ] **Step 4: Commit**

```bash
cd D:/DoAn
git add frontend/src/app/
git commit -m "feat(frontend): add register page"
```

---

## PHASE 11 — PWA Skeleton

### Task 37: Setup @serwist/next (disable trong dev)

- [ ] **Step 1: Install @serwist/next**

```bash
cd D:/DoAn/frontend
npm install -D @serwist/next serwist
```

- [ ] **Step 2: Tạo `src/app/sw.ts`**

```typescript
import { defaultCache } from "@serwist/next/worker";
import type { PrecacheEntry, SerwistGlobalConfig } from "serwist";
import { Serwist } from "serwist";

declare global {
  interface WorkerGlobalScope extends SerwistGlobalConfig {
    __SW_MANIFEST: (PrecacheEntry | string)[] | undefined;
  }
}

declare const self: ServiceWorkerGlobalScope;

const serwist = new Serwist({
  precacheEntries: self.__SW_MANIFEST,
  skipWaiting: true,
  clientsClaim: true,
  navigationPreload: true,
  runtimeCaching: defaultCache,
});

serwist.addEventListeners();
```

- [ ] **Step 3: Update `next.config.mjs`**

```javascript
import withSerwistInit from "@serwist/next";

const withSerwist = withSerwistInit({
  swSrc: "src/app/sw.ts",
  swDest: "public/sw.js",
  disable: process.env.NODE_ENV === "development",
});

/** @type {import('next').NextConfig} */
const nextConfig = {};

export default withSerwist(nextConfig);
```

- [ ] **Step 4: Tạo `public/manifest.json`**

```json
{
  "name": "Loyalty Platform",
  "short_name": "Loyalty",
  "description": "Multi-tenant loyalty platform",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#000000",
  "icons": [
    {
      "src": "/icons/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

- [ ] **Step 5: Tạo placeholder icons (sẽ thay sau ở tuần 4)**

```bash
cd D:/DoAn/frontend
mkdir -p public/icons
# Tạm dùng placeholder 1x1 pixel transparent PNG
# Hoặc download từ https://realfavicongenerator.net/
# Cho phép placeholder file empty trong tuần 1, tuần 4 sẽ thay
touch public/icons/icon-192.png public/icons/icon-512.png
```

- [ ] **Step 6: Update `src/app/layout.tsx` thêm manifest link**

```typescript
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Loyalty Platform",
  description: "Multi-tenant loyalty platform cho SME",
  manifest: "/manifest.json",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="vi">
      <body className="min-h-screen bg-background text-foreground antialiased">
        {children}
      </body>
    </html>
  );
}
```

- [ ] **Step 7: Verify build production thành công**

```bash
cd D:/DoAn/frontend
npm run build
```

Expected: Build success. Service worker chỉ generate khi `NODE_ENV=production` (không sinh ra trong dev).

- [ ] **Step 8: Commit**

```bash
cd D:/DoAn
git add frontend/
git commit -m "feat(frontend): add PWA skeleton with @serwist/next (disabled in dev)"
```

---

## PHASE 12 — GitHub Actions CI

### Task 38: Tạo CI workflow

**Files:**
- Create: `D:/DoAn/.github/workflows/ci.yml`

- [ ] **Step 1: Tạo workflow file**

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:

jobs:
  backend:
    name: Backend tests
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_USER: loyalty
          POSTGRES_PASSWORD: loyalty_dev
          POSTGRES_DB: loyalty
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip

      - name: Install backend deps
        working-directory: backend
        run: |
          pip install --upgrade pip
          pip install -e ".[dev]"

      - name: Lint with ruff
        working-directory: backend
        run: ruff check .

      - name: Format check with black
        working-directory: backend
        run: black --check .

      - name: Run pytest
        working-directory: backend
        env:
          DATABASE_URL: postgresql+asyncpg://loyalty:loyalty_dev@localhost:5432/loyalty
          JWT_SECRET: test-secret-32-bytes-min-for-ci-environment
        run: pytest -v

  frontend:
    name: Frontend build
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: npm
          cache-dependency-path: frontend/package-lock.json

      - name: Install frontend deps
        working-directory: frontend
        run: npm ci

      - name: Build frontend
        working-directory: frontend
        env:
          NEXT_PUBLIC_API_URL: http://localhost:8000
        run: npm run build
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add GitHub Actions workflow for backend tests + frontend build"
```

---

## PHASE 13 — Smoke Test E2E

### Task 39: Cập nhật docker-compose.yml thêm frontend service

**Files:**
- Modify: `D:/DoAn/docker-compose.yml`
- Create: `D:/DoAn/frontend/Dockerfile`

- [ ] **Step 1: Tạo `frontend/Dockerfile`**

```dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
```

- [ ] **Step 2: Update `docker-compose.yml` thêm frontend service**

```yaml
services:
  postgres:
    image: postgres:15-alpine
    container_name: loyalty-postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-loyalty}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-loyalty_dev}
      POSTGRES_DB: ${POSTGRES_DB:-loyalty}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-loyalty}"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: loyalty-backend
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql+asyncpg://loyalty:loyalty_dev@postgres:5432/loyalty
      JWT_SECRET: ${JWT_SECRET:-change-me-in-production-32-bytes-min}
      JWT_ALGORITHM: HS256
      ACCESS_TOKEN_EXPIRE_MINUTES: 15
      REFRESH_TOKEN_EXPIRE_DAYS: 7
      ENVIRONMENT: development
      DEBUG: "true"
      ENABLE_SCHEDULER: "false"
      FRONTEND_ORIGINS: http://localhost:3000
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: loyalty-frontend
    restart: unless-stopped
    depends_on:
      - backend
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
      - /app/.next

volumes:
  postgres_data:
```

- [ ] **Step 3: Commit**

```bash
git add frontend/Dockerfile docker-compose.yml
git commit -m "chore: add frontend Dockerfile and service to docker-compose"
```

---

### Task 40: Smoke test E2E end-to-end

- [ ] **Step 1: Down các container cũ nếu có**

```bash
cd D:/DoAn
docker compose down
```

- [ ] **Step 2: Build + Up tất cả services**

```bash
docker compose up -d --build
```

Expected: 3 container chạy: `loyalty-postgres`, `loyalty-backend`, `loyalty-frontend`.

- [ ] **Step 3: Verify health backend**

```bash
curl http://localhost:8000/health
```

Expected: `{"status":"ok","app":"loyalty-platform"}`

- [ ] **Step 4: Verify frontend mở được**

Mở browser: `http://localhost:3000` → thấy landing page.

- [ ] **Step 5: Test register qua UI**

Mở `http://localhost:3000/register` → điền form (`test@example.com` / `pass12345` / `Test User`) → submit → verify redirect về `/`.

- [ ] **Step 6: Test login qua UI**

Mở `http://localhost:3000/login` → đăng nhập với cùng credentials → verify thành công.

- [ ] **Step 7: Verify user đã được tạo trong DB**

```bash
docker compose exec postgres psql -U loyalty -d loyalty -c "SELECT id, email, full_name FROM users;"
```

Expected: thấy user vừa tạo.

- [ ] **Step 8: Down containers**

```bash
docker compose down
```

- [ ] **Step 9: Update README với hướng dẫn chạy**

Update `README.md`:

```markdown
# Loyalty Platform — Đồ án thực tập

Multi-tenant loyalty platform cho SME (cà phê, nhà hàng, shop bán lẻ).

## Stack
- Backend: FastAPI + PostgreSQL + SQLAlchemy 2.0 async + Alembic
- Frontend: Next.js 14 App Router + Tailwind + shadcn/ui + PWA
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
```

- [ ] **Step 10: Commit final tuần 1**

```bash
git add README.md
git commit -m "docs: update README with setup instructions"
```

---

## Tổng kết Tuần 1

### Đã hoàn thành
- ✅ Monorepo structure với `backend/`, `frontend/`, `docs/`
- ✅ Docker Compose: postgres + backend + frontend chạy 1 lệnh
- ✅ Backend FastAPI + async SQLAlchemy + Alembic + User model + migration
- ✅ Auth: register, login, refresh, /me endpoint với JWT + bcrypt
- ✅ JWT dependency `get_current_user`
- ✅ Rate limiting `slowapi` 5/phút/IP cho login
- ✅ 12+ integration tests + 7 unit tests, all green
- ✅ PostgreSQL testcontainer setup cho integration test
- ✅ Frontend Next.js 14 App Router + Tailwind + shadcn/ui
- ✅ Login + Register pages với react-hook-form + zod
- ✅ Zustand auth store + axios API client với interceptor
- ✅ PWA skeleton với `@serwist/next` (disabled trong dev)
- ✅ GitHub Actions CI: backend tests + lint + frontend build
- ✅ Smoke test end-to-end: register + login qua UI thật

### Tiêu chí đạt
- ✅ `docker compose up -d` chạy được
- ✅ Backend `/health` trả OK
- ✅ Frontend landing + login + register hiển thị
- ✅ Register/login qua UI tạo user trong DB thật
- ✅ Rate limit hoạt động (test pass)
- ✅ All tests green
- ✅ CI xanh

### Files được tạo
- `.gitignore`, `README.md`, `docker-compose.yml`
- `.github/workflows/ci.yml`
- `backend/`: pyproject.toml, Dockerfile, alembic, app/{core, models, schemas, services, api}, tests/
- `frontend/`: package.json, Dockerfile, src/{app, components/ui, lib, types}, public/

### Số liệu
- ~40 tasks
- ~25-30 commits
- ~15-20 source files backend
- ~10-15 source files frontend
- 7 unit tests + 12+ integration tests

---

## Sang tuần 2

Tuần 2 sẽ làm:
- Module `tenants` (đăng ký doanh nghiệp + Super Admin minimal approve)
- Module `tenant_staff` (Luồng H quản lý nhân viên)
- Module `tiers` + `point_rules`
- Module `verification_codes` + claim shadow flow đầy đủ (Luồng B Phần 2)
- Frontend `/merchant` onboarding UI + `/admin` minimal
- Seed script v1 (2 tenant, 5 tier, 5 staff)
- Test cross-tenant isolation đầu tiên
- Milestone review #1 với giảng viên

Plan cho tuần 2 sẽ được tạo riêng tại `docs/superpowers/plans/2026-04-12-tuan-2-tenants-staff.md` sau khi tuần 1 hoàn tất.
