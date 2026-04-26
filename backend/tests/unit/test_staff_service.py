"""Unit tests cho StaffService.

Các test này cần DB thật (integration-style) nên đánh dấu
pytest.mark.integration. Trên Windows không có docker.sock,
testcontainers sẽ fail — skip gracefully.
"""
import pytest

from app.core.security import gen_temp_password


# ─── gen_temp_password (pure function, không cần DB) ────────────────────────

def test_gen_temp_password_length():
    pwd = gen_temp_password()
    assert len(pwd) == 12


def test_gen_temp_password_custom_length():
    pwd = gen_temp_password(length=20)
    assert len(pwd) == 20


def test_gen_temp_password_alphanumeric_only():
    import string
    allowed = set(string.ascii_letters + string.digits)
    for _ in range(50):
        pwd = gen_temp_password()
        assert set(pwd) <= allowed, f"Non-alphanumeric char found in: {pwd}"


def test_gen_temp_password_randomness():
    """Hai lần gọi không được ra cùng kết quả (xác suất va chạm ~0)."""
    pwds = {gen_temp_password() for _ in range(20)}
    assert len(pwds) > 1


# ─── StaffService (integration — bỏ qua nếu DB không khả dụng) ─────────────

pytest.importorskip(
    "testcontainers",
    reason="testcontainers không cài — bỏ qua integration tests",
)


@pytest.mark.integration
def test_placeholder_staff_service_add():
    """Placeholder — staff service add_staff tạo user + staff row thành công.

    Thực thi đầy đủ cần async DB session từ testcontainers Postgres.
    Bỏ qua khi không có docker socket (Windows CI).
    """
    pytest.skip("Cần AsyncSession từ testcontainers — skip trên Windows")


@pytest.mark.integration
def test_placeholder_staff_service_toggle():
    """Placeholder — toggle_active đổi is_active trên staff row."""
    pytest.skip("Cần AsyncSession từ testcontainers — skip trên Windows")


@pytest.mark.integration
def test_placeholder_staff_service_reset_password():
    """Placeholder — reset_staff_password set password_hash mới + trả temp_password."""
    pytest.skip("Cần AsyncSession từ testcontainers — skip trên Windows")
