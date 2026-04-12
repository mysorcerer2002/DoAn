import secrets
import string

from slugify import slugify


def generate_slug(name: str) -> str:
    """Sinh slug từ tên (lowercase, dashes, ASCII)."""
    return slugify(name, lowercase=True, separator="-")


def generate_unique_slug(name: str, existing_slugs: set[str]) -> str:
    """Sinh slug duy nhất, thêm random suffix nếu trùng.

    Args:
        name: Tên gốc
        existing_slugs: Set các slug đã tồn tại trong DB

    Returns:
        Slug duy nhất, không trùng với existing_slugs

    Raises:
        ValueError: Nếu name rỗng
    """
    if not name or not name.strip():
        raise ValueError("Name cannot be empty")

    base = generate_slug(name)
    if not base:
        raise ValueError("Name produces empty slug")

    if base not in existing_slugs:
        return base

    alphabet = string.ascii_lowercase + string.digits
    while True:
        suffix = "".join(secrets.choice(alphabet) for _ in range(4))
        candidate = f"{base}-{suffix}"
        if candidate not in existing_slugs:
            return candidate
