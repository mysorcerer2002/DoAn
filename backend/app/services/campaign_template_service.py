"""Admin CRUD service cho `campaign_templates`.

Phase 2 của plan voucher rebuild v2.2. Template là khung khuyến mãi do admin
định nghĩa; shop chọn template khi enroll campaign và fill instance-level.

Version bump rule (section 4.1 plan): khi update đổi rule nghiệp vụ
(program_form, discount_type, caps, min_order_floor, ttl) → `version += 1`.
Campaign đã enroll giữ `template_version_snapshot` cũ → rule cũ, không bị
ảnh hưởng.

Soft delete: set `deleted_at = NOW()`. Template đã deleted không cho enroll
mới nhưng campaign cũ vẫn đọc được (FK RESTRICT).
"""

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.campaign_template import CampaignTemplate, ProgramForm
from app.schemas.campaign_template import (
    CampaignTemplateCreateRequest,
    CampaignTemplateUpdateRequest,
)


class TemplateNotFoundError(Exception):
    pass


class TemplateCodeConflictError(Exception):
    pass


# Các field mà đổi giá trị → bump version.
_RULE_FIELDS = {
    "program_form",
    "discount_type",
    "max_discount_percent_cap",
    "max_discount_value_cap",
    "max_discount_fixed_cap",
    "min_order_floor",
    "max_issuances_cap",
    "max_duration_days",
    "min_voucher_ttl_days",
    "max_voucher_ttl_days",
}


class CampaignTemplateService:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def compute_tier_hint(program_form: ProgramForm | str, estimated_cost: int) -> str:
        """Tính `approval_tier` từ program_form + estimated_cost (NĐ 81 Điều 17/19).

        Implement theo code block plan section 6.1 (`determine_tier`):
        - `may_rui_*` → luôn `dang_ky_so_ct` (Điều 19, bất kể cost).
        - Khác: cost <= auto threshold → `none` (auto_approved);
          cost <= notify threshold → `notify_so_ct` (Điều 17);
          cost > notify → `full_dossier` (hồ sơ đầy đủ).

        Plan có mâu thuẫn cục bộ line 137 vs 498 ở nhánh may_rui — pick theo
        code block line 498 (`dang_ky_so_ct`) khớp với CHECK enum trong
        `campaigns.approval_tier`.
        """
        form = program_form.value if isinstance(program_form, ProgramForm) else program_form
        if form in {"may_rui_quay_so", "may_rui_truc_tiep"}:
            return "dang_ky_so_ct"
        s = get_settings()
        if estimated_cost <= s.campaign_auto_threshold:
            return "none"
        if estimated_cost <= s.campaign_notify_threshold:
            return "notify_so_ct"
        return "full_dossier"

    async def list_templates(
        self,
        *,
        source: str | None = None,
        is_active: bool | None = None,
        include_deleted: bool = False,
    ) -> list[CampaignTemplate]:
        stmt = select(CampaignTemplate)
        if not include_deleted:
            stmt = stmt.where(CampaignTemplate.deleted_at.is_(None))
        if source is not None:
            stmt = stmt.where(CampaignTemplate.source == source)
        if is_active is not None:
            stmt = stmt.where(CampaignTemplate.is_active.is_(is_active))
        stmt = stmt.order_by(CampaignTemplate.created_at.desc())
        rows = await self.db.scalars(stmt)
        return list(rows.all())

    async def get_template(self, template_id: int) -> CampaignTemplate:
        obj = await self.db.get(CampaignTemplate, template_id)
        if obj is None:
            raise TemplateNotFoundError(f"Template {template_id} không tồn tại")
        return obj

    async def _ensure_code_unique(self, code: str, exclude_id: int | None = None) -> None:
        stmt = select(func.count()).select_from(CampaignTemplate).where(
            CampaignTemplate.code == code
        )
        if exclude_id is not None:
            stmt = stmt.where(CampaignTemplate.id != exclude_id)
        count = int(await self.db.scalar(stmt) or 0)
        if count > 0:
            raise TemplateCodeConflictError(f"Template code '{code}' đã tồn tại")

    async def create_template(
        self, request: CampaignTemplateCreateRequest
    ) -> CampaignTemplate:
        await self._ensure_code_unique(request.code)
        template = CampaignTemplate(
            code=request.code,
            name=request.name,
            description=request.description,
            source=request.source.value,
            program_form=request.program_form.value,
            discount_type=request.discount_type.value,
            default_usage_guide=request.default_usage_guide,
            default_support_contact=request.default_support_contact,
            default_terms=request.default_terms,
            max_discount_percent_cap=request.max_discount_percent_cap,
            max_discount_value_cap=request.max_discount_value_cap,
            max_discount_fixed_cap=request.max_discount_fixed_cap,
            min_order_floor=request.min_order_floor,
            max_issuances_cap=request.max_issuances_cap,
            max_duration_days=request.max_duration_days,
            min_voucher_ttl_days=request.min_voucher_ttl_days,
            max_voucher_ttl_days=request.max_voucher_ttl_days,
            version=1,
            is_active=request.is_active,
        )
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def update_template(
        self, template_id: int, request: CampaignTemplateUpdateRequest
    ) -> CampaignTemplate:
        """Patch template. Chỉ fields trong `_RULE_FIELDS` bump version —
        nghĩa là caps + program_form + discount_type + ttl + min_order_floor +
        max_issuances_cap + max_duration_days. Đổi text mô tả
        (`default_terms`, `default_usage_guide`, `default_support_contact`,
        `description`, `name`) hoặc `is_active` KHÔNG bump version vì text đã
        snapshot tại enroll (campaign giữ bản text cũ qua trường riêng).
        """
        template = await self.get_template(template_id)
        data = request.model_dump(exclude_unset=True)
        if not data:
            return template

        rule_changed = False
        for key, value in data.items():
            current = getattr(template, key)
            # Enum field: request gửi Enum, DB lưu str — so giá trị string.
            new_value = value.value if hasattr(value, "value") else value
            current_value = current.value if hasattr(current, "value") else current
            if new_value != current_value:
                setattr(template, key, new_value)
                if key in _RULE_FIELDS:
                    rule_changed = True

        # Validate cross-field sau khi patch — tương tự CHECK DB.
        if (
            template.max_voucher_ttl_days is not None
            and template.min_voucher_ttl_days is not None
            and template.max_voucher_ttl_days < template.min_voucher_ttl_days
        ):
            raise ValueError(
                "max_voucher_ttl_days phải >= min_voucher_ttl_days"
            )
        if template.discount_type == "percent":
            if (
                template.max_discount_percent_cap is None
                or template.max_discount_value_cap is None
            ):
                raise ValueError(
                    "discount_type=percent cần đủ cả max_discount_percent_cap "
                    "và max_discount_value_cap"
                )
        elif template.discount_type == "fixed":
            if template.max_discount_fixed_cap is None:
                raise ValueError(
                    "discount_type=fixed cần max_discount_fixed_cap"
                )

        if rule_changed:
            template.version += 1

        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def soft_delete_template(self, template_id: int) -> CampaignTemplate:
        template = await self.get_template(template_id)
        if template.deleted_at is None:
            template.deleted_at = datetime.now(UTC)
            template.is_active = False
            await self.db.commit()
            await self.db.refresh(template)
        return template
