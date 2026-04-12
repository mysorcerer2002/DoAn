import pytest

from app.core.slug import generate_slug, generate_unique_slug


def test_generate_slug_basic():
    assert generate_slug("The Coffee House") == "the-coffee-house"


def test_generate_slug_vietnamese():
    assert generate_slug("Cà Phê Trung Nguyên") == "ca-phe-trung-nguyen"


def test_generate_slug_special_chars():
    assert generate_slug("Shop A&B! @123") == "shop-a-b-123"


def test_generate_unique_slug_no_conflict():
    existing = set()
    slug = generate_unique_slug("My Shop", existing)
    assert slug == "my-shop"


def test_generate_unique_slug_with_conflict():
    existing = {"my-shop"}
    slug = generate_unique_slug("My Shop", existing)
    assert slug.startswith("my-shop-")
    assert len(slug) == len("my-shop-") + 4
    assert slug not in existing


def test_generate_unique_slug_empty_name_raises():
    with pytest.raises(ValueError):
        generate_unique_slug("", set())
