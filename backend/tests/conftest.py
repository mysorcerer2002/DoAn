import secrets
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer

from app.core.db import get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.base import Base
from app.models.partner import Partner, PartnerCategory, PartnerStatus
from app.models.partner_staff import PartnerStaff
from app.models.point_rule import PointRule
from app.models.reward import Reward, RewardOfferType
from app.models.user import User


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
    engine = create_async_engine(database_url, echo=False, pool_size=2, max_overflow=0)
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
async def clear_partner_cache():
    yield


@pytest_asyncio.fixture(autouse=True)
async def reset_rate_limiter():
    """Reset rate limiter giữa các test để tránh 429 từ test khác."""
    from app.core.limiter import limiter

    limiter.reset()
    yield
    limiter.reset()


# ---------------------------------------------------------------------------
# Factory + token fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def user_factory():
    """Tạo user với phone unique tự sinh.

    LƯU Ý: Phase 0 KHÔNG có `must_change_password` kwarg vì cột này chưa tồn tại
    trong DB ở thời điểm Phase 0 commit (Phase 3 mới thêm). Phase 3 sẽ extend
    factory thêm `must_change_password=False` kwarg.
    """
    async def _factory(db, *, email=None, phone=None, password_hash=None,
                       is_active=True, system_role="regular", points_balance=0):
        if email is None:
            email = f"u{secrets.token_hex(4)}@test.vn"
        if phone is None:
            phone = f"09{secrets.randbelow(10**8):08d}"
        if password_hash is None:
            password_hash = hash_password("testpass1")
        user = User(
            email=email, phone=phone, password_hash=password_hash,
            full_name=f"User {email}", is_active=is_active,
            system_role=system_role, points_balance=points_balance,
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user
    return _factory


@pytest_asyncio.fixture
async def partner_factory():
    """Tạo Partner; auto-create owner User nếu owner_user=None.

    Khi test cần đăng nhập dưới quyền chủ shop, pass `owner_user=user` rõ ràng
    để giữ tham chiếu đến User object. Nhánh auto-create chỉ dùng cho test
    không quan tâm danh tính owner (chỉ cần partner tồn tại).
    """
    async def _factory(db, *, name=None, status=PartnerStatus.ACTIVE,
                       category=PartnerCategory.CAFE, owner_user=None):
        if name is None:
            name = f"Shop {secrets.token_hex(3)}"
        if owner_user is None:
            owner = User(
                email=f"owner-{secrets.token_hex(3)}@test.vn",
                phone=f"09{secrets.randbelow(10**8):08d}",
                password_hash=hash_password("ownerpass1"),
                full_name="Owner", is_active=True, system_role="regular",
            )
            db.add(owner)
            await db.flush()
        else:
            owner = owner_user
        slug = name.lower().replace(" ", "-") + secrets.token_hex(2)
        partner = Partner(
            name=name, slug=slug, owner_user_id=owner.id,
            status=status, category=category, settings={},
        )
        db.add(partner)
        await db.flush()
        await db.refresh(partner)
        return partner
    return _factory


@pytest_asyncio.fixture
async def reward_factory():
    async def _factory(db, *, partner_id, name=None, points_cost=100,
                       stock=None, offer_type=RewardOfferType.ITEM_GIFT,
                       offer_value=None, offer_label=None,
                       valid_until=None, is_active=True):
        if name is None:
            name = f"Reward {secrets.token_hex(3)}"
        if offer_label is None:
            offer_label = name
        reward = Reward(
            partner_id=partner_id, name=name, points_cost=points_cost,
            stock=stock, offer_type=offer_type, offer_value=offer_value,
            offer_label=offer_label, valid_until=valid_until, is_active=is_active,
        )
        db.add(reward)
        await db.flush()
        await db.refresh(reward)
        return reward
    return _factory


@pytest_asyncio.fixture
async def point_rule_factory():
    """Factory dùng schema MỚI sau Phase 1A (earn_percent thay points_per_unit/unit_amount/min_amount).

    Tests Phase 0 KHÔNG gọi factory này → ổn dù migration QT3 chưa apply.
    Tests Phase 2 trở đi (QT4 dùng đầu tiên) chạy SAU migration QT3 → fixture work.
    """
    from decimal import Decimal

    async def _factory(db, *, partner_id, earn_percent=Decimal("1.00"),
                       use_tiers=False, is_active=True):
        rule = PointRule(
            partner_id=partner_id, earn_percent=earn_percent,
            use_tiers=use_tiers, is_active=is_active,
        )
        db.add(rule)
        await db.flush()
        return rule
    return _factory


@pytest_asyncio.fixture
async def staff_user_factory(user_factory):
    """User là staff của 1 partner."""
    async def _factory(db, *, partner_id, **kwargs):
        user = await user_factory(db, **kwargs)
        staff = PartnerStaff(partner_id=partner_id, user_id=user.id, is_active=True)
        db.add(staff)
        await db.flush()
        return user
    return _factory


def _mint_token(user_id: int) -> str:
    return create_access_token(user_id=user_id)


@pytest_asyncio.fixture
async def admin_token(db_session, user_factory):
    """JWT cho 1 super_admin user mới được tạo riêng cho fixture này.

    Token KHÔNG tương ứng với bất kỳ User object nào trả về từ `user_factory`
    trong cùng test. Nếu test cần truy cập User object đứng sau token, hãy
    `await user_factory(db_session, system_role='super_admin')` rồi gọi
    `create_access_token(user_id=user.id)` thay vì dùng fixture này.
    """
    admin = await user_factory(db_session, system_role="super_admin")
    return _mint_token(admin.id)


@pytest_asyncio.fixture
async def user_token(db_session, user_factory):
    """JWT cho 1 regular user mới. Xem note ở `admin_token` về cách lấy User object."""
    user = await user_factory(db_session)
    return _mint_token(user.id)


@pytest_asyncio.fixture
async def customer_token(db_session, user_factory):
    """Alias customer_token = user_token (regular role). Xem note ở `admin_token`."""
    user = await user_factory(db_session)
    return _mint_token(user.id)
