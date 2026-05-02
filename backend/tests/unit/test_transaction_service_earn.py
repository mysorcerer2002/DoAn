"""Unit tests cho _calculate_points sau khi đổi sang earn_percent (Phase 1A)."""

from decimal import Decimal

from app.services.transaction_service import TransactionService


def _rule(earn_percent="1.00", use_tiers=False):
    return type("R", (), {
        "earn_percent": Decimal(earn_percent),
        "use_tiers": use_tiers,
    })()


def _membership(multiplier="1.00"):
    tier = type("T", (), {"earn_multiplier": Decimal(multiplier)})()
    return type("M", (), {"current_tier": tier})()


def test_calculate_points_1_percent():
    """100k @ 1% = 1000 điểm."""
    assert TransactionService._calculate_points(_rule("1.00"), 100_000) == 1000


def test_calculate_points_decimal_percent():
    """100k @ 0.5% = 500 điểm."""
    assert TransactionService._calculate_points(_rule("0.50"), 100_000) == 500


def test_calculate_points_2_5_percent():
    """200k @ 2.5% = 5000 điểm."""
    assert TransactionService._calculate_points(_rule("2.50"), 200_000) == 5000


def test_calculate_points_with_tier_multiplier():
    """100k @ 1% × tier 1.5x = 1500 điểm."""
    assert (
        TransactionService._calculate_points(
            _rule("1.00", use_tiers=True), 100_000, membership=_membership("1.50")
        ) == 1500
    )


def test_calculate_points_tier_disabled():
    """use_tiers=false → multiplier không áp dụng dù tier có hệ số."""
    assert (
        TransactionService._calculate_points(
            _rule("1.00", use_tiers=False), 100_000, membership=_membership("1.50")
        ) == 1000
    )


def test_calculate_points_truncation():
    """Bill 333 @ 1% = 3.33 → floor về 3."""
    assert TransactionService._calculate_points(_rule("1.00"), 333) == 3


def test_calculate_points_zero_amount():
    """Bill 0 @ bất kỳ % = 0 điểm."""
    assert TransactionService._calculate_points(_rule("1.00"), 0) == 0
