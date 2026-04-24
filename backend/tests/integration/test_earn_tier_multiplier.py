"""Tests cho earn_multiplier logic (B7).

Kiểm tra 2 case:
1. Multiplier áp dụng khi rule.use_tiers=True và member có tier.
2. Multiplier bị ignore khi rule.use_tiers=False.
"""

from decimal import Decimal
from types import SimpleNamespace

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.membership import Membership
from app.models.partner import Partner, PartnerCategory, PartnerStatus
from app.models.point_rule import PointRule
from app.models.tier import Tier
from app.services.transaction_service import TransactionService
from app.services.tier_service import TierService


# ---------------------------------------------------------------------------
# Unit tests trên _calculate_points (staticmethod, không cần DB)
# Dùng SimpleNamespace để tránh SQLAlchemy ORM instrumentation state issues
# khi tạo object ngoài session context.
# ---------------------------------------------------------------------------


def _make_rule(*, use_tiers: bool, unit_amount: int = 10_000, points_per_unit: Decimal = Decimal("1")) -> SimpleNamespace:
    """Tạo PointRule stub (SimpleNamespace) — đủ interface cho _calculate_points."""
    return SimpleNamespace(
        unit_amount=unit_amount,
        points_per_unit=points_per_unit,
        min_amount=0,
        use_tiers=use_tiers,
    )


def _make_membership_with_tier(*, earn_multiplier: Decimal) -> SimpleNamespace:
    """Tạo Membership stub với current_tier được set trực tiếp."""
    tier = SimpleNamespace(earn_multiplier=earn_multiplier)
    return SimpleNamespace(current_tier=tier)


class TestCalculatePointsUnit:
    """Unit tests cho TransactionService._calculate_points (không cần DB).

    Rule chuẩn: unit_amount=10_000, points_per_unit=1
    → 10.000₫ = 1 point (base), 100.000₫ = 10 points (base).
    """

    def test_earn_with_tier_multiplier(self):
        """rule.use_tiers=True + tier Gold(×1.50) + 100.000₫ → 15 points."""
        rule = _make_rule(use_tiers=True)
        membership = _make_membership_with_tier(earn_multiplier=Decimal("1.50"))
        # 100000/10000 = 10 base → int(10 * 1.50) = 15
        points = TransactionService._calculate_points(rule, 100_000, membership=membership)
        assert points == 15

    def test_earn_use_tiers_false_ignores_multiplier(self):
        """rule.use_tiers=False + tier Gold(×1.50) + 100.000₫ → 10 points (ignore multiplier)."""
        rule = _make_rule(use_tiers=False)
        membership = _make_membership_with_tier(earn_multiplier=Decimal("1.50"))
        # use_tiers=False → multiplier=1.00 → int(10 * 1.00) = 10
        points = TransactionService._calculate_points(rule, 100_000, membership=membership)
        assert points == 10

    def test_earn_bronze_tier_multiplier_1x(self):
        """rule.use_tiers=True + tier Bronze(×1.00) + 1.000₫ → 0 points (< unit_amount)."""
        rule = _make_rule(use_tiers=True)
        membership = _make_membership_with_tier(earn_multiplier=Decimal("1.00"))
        # 1000 < unit_amount=10000 → 0.1 unit → int(0.1 * 1 * 1.00) = 0
        points = TransactionService._calculate_points(rule, 1_000, membership=membership)
        assert points == 0

    def test_earn_no_membership_no_multiplier(self):
        """Không có membership → base points (không crash)."""
        rule = _make_rule(use_tiers=True)
        # 100000/10000 = 10 base → int(10 * 1.00) = 10
        points = TransactionService._calculate_points(rule, 100_000, membership=None)
        assert points == 10

    def test_earn_membership_no_tier(self):
        """Membership có current_tier=None → base points."""
        rule = _make_rule(use_tiers=True)
        membership = SimpleNamespace(current_tier=None)
        # 100000/10000 = 10 base → int(10 * 1.00) = 10
        points = TransactionService._calculate_points(rule, 100_000, membership=membership)
        assert points == 10


# ---------------------------------------------------------------------------
# Integration tests với DB (dùng db_session fixture từ conftest)
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def partner_with_tiers(db_session):
    """Tạo partner + tiers Bronze/Gold + point rule use_tiers=True."""
    from datetime import UTC, datetime
    from app.models.user import User
    from app.core.security import hash_password  # noqa: PLC0415

    # Tạo user owner
    owner = User(
        email="owner_b7@test.vn",
        password_hash=hash_password("test1234"),
        full_name="Owner B7",
        is_active=True,
        system_role="regular",
        password_changed_at=datetime.now(UTC),
    )
    db_session.add(owner)
    await db_session.flush()

    partner = Partner(
        name="Test Partner B7",
        slug="test-b7",
        owner_user_id=owner.id,
        status=PartnerStatus.ACTIVE,
        category=PartnerCategory.CAFE,
        activated_at=datetime.now(UTC),
    )
    db_session.add(partner)
    await db_session.flush()

    bronze = Tier(
        partner_id=partner.id,
        name="Bronze",
        min_points=0,
        earn_multiplier=Decimal("1.00"),
        is_active=True,
    )
    gold = Tier(
        partner_id=partner.id,
        name="Gold",
        min_points=1_000,
        earn_multiplier=Decimal("1.50"),
        is_active=True,
    )
    db_session.add_all([bronze, gold])
    await db_session.flush()

    rule = PointRule(
        partner_id=partner.id,
        unit_amount=10_000,
        points_per_unit=Decimal("1"),
        min_amount=0,
        use_tiers=True,
        is_active=True,
    )
    db_session.add(rule)
    await db_session.flush()

    return {"partner": partner, "bronze": bronze, "gold": gold, "rule": rule, "owner": owner}


@pytest.mark.asyncio
async def test_earn_with_bronze_then_promote_to_gold(db_session, partner_with_tiers):
    """
    Tạo member Bronze → earn 1000₫ → 0 points (< unit_amount).
    Nâng total_points_earned = 1000 → recompute_tier → Gold.
    Earn 10.000₫ với tier Gold(×1.50) → 15 points.
    """
    from datetime import UTC, datetime
    from app.models.user import User
    from app.core.security import hash_password  # noqa: PLC0415

    data = partner_with_tiers
    partner = data["partner"]
    bronze = data["bronze"]
    gold = data["gold"]
    rule = data["rule"]

    # Tạo user + membership với tier Bronze
    user = User(
        email="khach_b7@test.vn",
        password_hash=hash_password("khach1234"),
        full_name="Khách B7",
        is_active=True,
        system_role="regular",
        password_changed_at=datetime.now(UTC),
    )
    db_session.add(user)
    await db_session.flush()

    membership = Membership(
        partner_id=partner.id,
        user_id=user.id,
        current_tier_id=bronze.id,
        points_balance=0,
        total_points_earned=0,
    )
    db_session.add(membership)
    await db_session.flush()

    # Load membership với current_tier
    membership = await db_session.scalar(
        select(Membership)
        .options(selectinload(Membership.current_tier))
        .where(Membership.id == membership.id)
    )

    # Earn 1000₫ với Bronze(×1.00): 1000/10000 = 0.1 unit → int(0.1 * 1 * 1.00) = 0
    points_bronze = TransactionService._calculate_points(rule, 1_000, membership=membership)
    assert points_bronze == 0, f"Expected 0 points at Bronze for 1000 VND, got {points_bronze}"

    # Simulate: earn 100000₫ ở Bronze → 10 điểm (còn dưới Gold threshold)
    # 100000/10000 = 10 base → int(10 * 1.00) = 10
    points_at_bronze_100k = TransactionService._calculate_points(rule, 100_000, membership=membership)
    assert points_at_bronze_100k == 10, f"Expected 10 at Bronze for 100000 VND, got {points_at_bronze_100k}"

    # Promote: nâng total_points_earned lên 1000 (vừa đủ Gold threshold=1000)
    membership.total_points_earned = 1_000
    await db_session.flush()

    # recompute_tier → Gold
    tier_svc = TierService(db_session)
    new_tier = await tier_svc.recompute_tier(
        partner_id=partner.id, membership_id=membership.id
    )
    assert new_tier is not None, "recompute_tier trả về None, expected Gold tier"
    assert new_tier.id == gold.id, f"Expected Gold tier, got {new_tier.name}"
    assert new_tier.earn_multiplier == Decimal("1.50")

    # Reload membership sau recompute để current_tier được populate
    membership = await db_session.scalar(
        select(Membership)
        .options(selectinload(Membership.current_tier))
        .where(Membership.id == membership.id)
    )

    # Earn 100.000₫ với Gold(×1.50): 100000/10000 = 10 base → int(10 * 1.50) = 15
    points_gold = TransactionService._calculate_points(rule, 100_000, membership=membership)
    assert points_gold == 15, f"Expected 15 points at Gold for 100000 VND, got {points_gold}"


@pytest.mark.asyncio
async def test_earn_with_use_tiers_false_ignores_multiplier(db_session, partner_with_tiers):
    """
    rule.use_tiers=False + member có tier Gold(×1.50).
    Earn 10.000₫ → 10 points (multiplier bị ignore).
    """
    from datetime import UTC, datetime
    from app.models.user import User
    from app.core.security import hash_password  # noqa: PLC0415

    data = partner_with_tiers
    partner = data["partner"]
    gold = data["gold"]
    rule = data["rule"]

    # Tạm thời set use_tiers=False trên rule object (không persist, chỉ dùng trong test)
    rule.use_tiers = False

    user = User(
        email="khach_b7b@test.vn",
        password_hash=hash_password("khach1234"),
        full_name="Khách B7 B",
        is_active=True,
        system_role="regular",
        password_changed_at=datetime.now(UTC),
    )
    db_session.add(user)
    await db_session.flush()

    membership = Membership(
        partner_id=partner.id,
        user_id=user.id,
        current_tier_id=gold.id,
        points_balance=1_000,
        total_points_earned=1_000,
    )
    db_session.add(membership)
    await db_session.flush()

    membership = await db_session.scalar(
        select(Membership)
        .options(selectinload(Membership.current_tier))
        .where(Membership.id == membership.id)
    )
    assert membership.current_tier is not None
    assert membership.current_tier.earn_multiplier == Decimal("1.50")

    # Với use_tiers=False, multiplier bị ignore → 100000/10000 = 10 base → int(10 * 1.00) = 10
    points = TransactionService._calculate_points(rule, 100_000, membership=membership)
    assert points == 10, f"Expected 10 points with use_tiers=False, got {points}"
