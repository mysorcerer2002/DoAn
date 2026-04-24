import pytest
from fastapi import HTTPException

from app.core.deps import extract_partner_id_from_header


def test_extract_partner_id_valid():
    assert extract_partner_id_from_header("42") == 42


def test_extract_partner_id_missing_raises_400():
    with pytest.raises(HTTPException) as exc_info:
        extract_partner_id_from_header(None)
    assert exc_info.value.status_code == 400
    assert "X-Partner-Id" in exc_info.value.detail


def test_extract_partner_id_invalid_format_raises_400():
    with pytest.raises(HTTPException) as exc_info:
        extract_partner_id_from_header("not-a-number")
    assert exc_info.value.status_code == 400


def test_extract_partner_id_negative_raises_400():
    with pytest.raises(HTTPException) as exc_info:
        extract_partner_id_from_header("-5")
    assert exc_info.value.status_code == 400
