from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.services.transaction_service import TransactionService


def _rule(points_per_unit=1, unit_amount=1000, min_amount=0, use_tiers=False):
    return SimpleNamespace(
        points_per_unit=Decimal(points_per_unit),
        unit_amount=unit_amount,
        min_amount=min_amount,
        use_tiers=use_tiers,
    )


def _membership_with_tier(multiplier):
    tier = SimpleNamespace(earn_multiplier=Decimal(str(multiplier)))
    return SimpleNamespace(current_tier=tier)


def test_calculate_points_below_min_amount_returns_zero():
    rule = _rule(min_amount=5000)
    assert TransactionService._calculate_points(rule, 1000) == 0


def test_calculate_points_base_no_membership():
    rule = _rule(points_per_unit=1, unit_amount=1000)
    assert TransactionService._calculate_points(rule, 10_000) == 10


def test_calculate_points_use_tiers_false_ignores_multiplier():
    rule = _rule(use_tiers=False)
    membership = _membership_with_tier(1.50)
    assert TransactionService._calculate_points(
        rule, 10_000, membership=membership
    ) == 10


def test_calculate_points_use_tiers_true_applies_gold_multiplier():
    rule = _rule(use_tiers=True)
    membership = _membership_with_tier(1.50)
    assert TransactionService._calculate_points(
        rule, 10_000, membership=membership
    ) == 15


def test_calculate_points_membership_null_tier_falls_back_to_1():
    rule = _rule(use_tiers=True)
    membership = SimpleNamespace(current_tier=None)
    assert TransactionService._calculate_points(
        rule, 10_000, membership=membership
    ) == 10


def test_calculate_points_truncation():
    rule = _rule(use_tiers=True)
    membership = _membership_with_tier(1.50)
    assert TransactionService._calculate_points(
        rule, 1_000, membership=membership
    ) == 1


def test_calculate_points_no_membership_kwarg_backcompat():
    rule = _rule(use_tiers=True)
    assert TransactionService._calculate_points(rule, 10_000) == 10
