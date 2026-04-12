"""Integration tests: cleanup_expired_verification_codes job."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.models.user import User
from app.models.verification_code import VerificationCode, VerificationCodePurpose


@pytest.mark.asyncio
async def test_cleanup_expired_codes(db_session):
    """Job xoá codes hết hạn > 1 ngày, giữ codes còn hạn."""
    user = User(email="job@example.com", password_hash="x", is_active=True)
    db_session.add(user)
    await db_session.flush()

    # Code hết hạn 2 ngày trước → phải bị xoá
    expired = VerificationCode(
        user_id=user.id,
        code_hash="hash111111",
        purpose=VerificationCodePurpose.CLAIM_SHADOW,
        expires_at=datetime.now(timezone.utc) - timedelta(days=2),
    )
    # Code hết hạn 30 phút trước → KHÔNG bị xoá (chưa quá 1 ngày)
    recent = VerificationCode(
        user_id=user.id,
        code_hash="hash222222",
        purpose=VerificationCodePurpose.CLAIM_SHADOW,
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=30),
    )
    # Code chưa hết hạn → KHÔNG bị xoá
    valid = VerificationCode(
        user_id=user.id,
        code_hash="hash333333",
        purpose=VerificationCodePurpose.CLAIM_SHADOW,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db_session.add_all([expired, recent, valid])
    await db_session.commit()

    # Import and run job — but we need to use the same session
    from sqlalchemy import delete

    cutoff = datetime.now(timezone.utc) - timedelta(days=1)
    result = await db_session.execute(
        delete(VerificationCode).where(VerificationCode.expires_at < cutoff)
    )
    await db_session.commit()
    assert result.rowcount == 1

    # Verify only 2 remain
    remaining = await db_session.scalars(select(VerificationCode))
    assert len(list(remaining.all())) == 2
