"""Unit tests — logic thuần của CampaignEnrollmentService (no DB).

Phase 16 plan voucher rebuild v2.2. Test compute_tier_hint + form_commitment.
Không cần db_session — import service + schema trực tiếp.
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.schemas.campaign_enrollment import EnrollFormInput
from app.services.campaign_enrollment_service import form_commitment
from app.services.campaign_template_service import CampaignTemplateService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_form(template_id: int = 1, discount_value: int = 10_000, name: str = "Test") -> EnrollFormInput:
    now = datetime.now(timezone.utc)
    return EnrollFormInput(
        template_id=template_id,
        name=name,
        discount_value=discount_value,
        starts_at=now,
        ends_at=now + timedelta(days=7),
    )


# ---------------------------------------------------------------------------
# compute_tier_hint — program_form overrides
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_tier_hint_program_form_may_rui_quay_so_always_dang_ky():
    """may_rui_quay_so luôn → dang_ky_so_ct bất kể cost=0."""
    tier = CampaignTemplateService.compute_tier_hint("may_rui_quay_so", 0)
    assert tier == "dang_ky_so_ct"


@pytest.mark.asyncio
async def test_tier_hint_program_form_may_rui_truc_tiep_always_dang_ky():
    """may_rui_truc_tiep luôn → dang_ky_so_ct dù cost rất lớn."""
    tier = CampaignTemplateService.compute_tier_hint("may_rui_truc_tiep", 100_000_000)
    assert tier == "dang_ky_so_ct"


# ---------------------------------------------------------------------------
# compute_tier_hint — cost-based (giam_gia)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_tier_hint_giam_gia_below_auto_threshold_none():
    """cost == 500_000 (inclusive boundary) → none."""
    tier = CampaignTemplateService.compute_tier_hint("giam_gia", 500_000)
    assert tier == "none"


@pytest.mark.asyncio
async def test_tier_hint_giam_gia_above_auto_below_notify_notify_so_ct():
    """cost == 500_001 và cost == 2_000_000 → notify_so_ct."""
    assert CampaignTemplateService.compute_tier_hint("giam_gia", 500_001) == "notify_so_ct"
    assert CampaignTemplateService.compute_tier_hint("giam_gia", 2_000_000) == "notify_so_ct"


@pytest.mark.asyncio
async def test_tier_hint_giam_gia_above_notify_threshold_full_dossier():
    """cost == 2_000_001 → full_dossier."""
    tier = CampaignTemplateService.compute_tier_hint("giam_gia", 2_000_001)
    assert tier == "full_dossier"


# ---------------------------------------------------------------------------
# form_commitment — hash stability
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_form_commitment_stable_across_key_order():
    """Hai EnrollFormInput cùng data cho cùng hash (sort_keys=True)."""
    now = datetime.now(timezone.utc)
    ends = now + timedelta(days=7)
    form_a = EnrollFormInput(
        template_id=1,
        name="Camp A",
        discount_value=10_000,
        starts_at=now,
        ends_at=ends,
    )
    form_b = EnrollFormInput(
        template_id=1,
        name="Camp A",
        discount_value=10_000,
        starts_at=now,
        ends_at=ends,
    )
    assert form_commitment(form_a) == form_commitment(form_b)


@pytest.mark.asyncio
async def test_form_commitment_changes_on_any_field_mutation():
    """Đổi discount_value hoặc name → hash khác."""
    now = datetime.now(timezone.utc)
    ends = now + timedelta(days=7)

    base = EnrollFormInput(
        template_id=1,
        name="Camp A",
        discount_value=10_000,
        starts_at=now,
        ends_at=ends,
    )
    diff_value = EnrollFormInput(
        template_id=1,
        name="Camp A",
        discount_value=20_000,  # khác
        starts_at=now,
        ends_at=ends,
    )
    diff_name = EnrollFormInput(
        template_id=1,
        name="Camp B",  # khác
        discount_value=10_000,
        starts_at=now,
        ends_at=ends,
    )

    base_hash = form_commitment(base)
    assert form_commitment(diff_value) != base_hash
    assert form_commitment(diff_name) != base_hash
