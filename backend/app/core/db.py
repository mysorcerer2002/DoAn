from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yields an async DB session.

    Commit chỉ chạy ở `else` branch — nếu yield raise (kể cả HTTPException
    bubble lên sau khi yield return), rollback và KHÔNG commit. Đây là pattern
    đúng cho FastAPI dependency.

    LƯU Ý: yield-style cleanup chạy SAU khi response đã gửi → race window:
    client gọi tiếp ngay sau khi nhận response có thể thấy state CHƯA commit.
    Routes tạo resource rồi return token/id (vd /auth/register, /partner/register,
    POST /partner/rewards, POST /admin/...) phải gọi `await db.commit()` explicit
    TRƯỚC khi return để client nhận response chỉ khi commit đã xong.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        else:
            await session.commit()
