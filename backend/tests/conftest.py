from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer

from app.core.db import get_db
from app.main import app
from app.models.base import Base


@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:15-alpine") as container:
        yield container


@pytest.fixture(scope="session")
def database_url(postgres_container):
    sync_url = postgres_container.get_connection_url()
    return sync_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://").replace(
        "postgresql://", "postgresql+asyncpg://"
    )


@pytest_asyncio.fixture
async def db_session(database_url) -> AsyncGenerator[AsyncSession, None]:
    """Mỗi test có 1 engine + session riêng, drop/create tables để isolate hoàn toàn."""
    engine = create_async_engine(database_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

        # Apply append-only trigger cho point_ledger (Base.metadata.create_all không biết DDL trigger)
        await conn.execute(text("""
            CREATE OR REPLACE FUNCTION prevent_point_ledger_mutation()
            RETURNS TRIGGER AS $$
            BEGIN
                RAISE EXCEPTION 'point_ledger is append-only — UPDATE/DELETE not allowed';
            END;
            $$ LANGUAGE plpgsql;
        """))
        await conn.execute(text(
            "DROP TRIGGER IF EXISTS no_update_or_delete_point_ledger ON point_ledger;"
        ))
        await conn.execute(text("""
            CREATE TRIGGER no_update_or_delete_point_ledger
            BEFORE UPDATE OR DELETE ON point_ledger
            FOR EACH ROW EXECUTE FUNCTION prevent_point_ledger_mutation();
        """))

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()

    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """HTTP test client sử dụng db_session fixture để override get_db."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(autouse=True)
async def clear_tenant_cache():
    from app.core.tenant_cache import tenant_role_cache

    tenant_role_cache.clear()
    yield
    tenant_role_cache.clear()


@pytest_asyncio.fixture(autouse=True)
async def reset_rate_limiter():
    """Reset rate limiter giữa các test để tránh 429 từ test khác."""
    from app.core.limiter import limiter

    limiter.reset()
    yield
    limiter.reset()
