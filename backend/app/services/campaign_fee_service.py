"""CampaignFeeService — Phase 7 plan voucher rebuild v2.2.

Scope đồ án (SERVICE_FEE_ENABLED=False): data model vẫn đầy đủ, service
chỉ đọc (list/get) để FE render invoice view khi bật flag. Không tạo fee
mới ở phase này — đã xử lý ở CampaignEnrollmentService (skip khi flag OFF).

VAT helper `calc_vat(amount, vat_rate)` dùng chung cho preview + admin
panel. Quy tắc: cast BIGINT (floor) giống DB `Computed` cột.
"""

from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign_service_fee import CampaignServiceFee


class FeeNotFoundError(Exception):
    pass


def calc_vat(amount: int, vat_rate: Decimal | float) -> int:
    """Khớp công thức DB GENERATED: `(amount * vat_rate / 100)::BIGINT`.

    Postgres cast `numeric → bigint` dùng "round half away from zero"
    (= ROUND_HALF_UP cho số dương) — verify bằng query thực:
    `SELECT (12345 * 10 / 100)::BIGINT` → 1235 chứ không phải 1234.
    Python phải match để preview FE không lệch invoice DB ở case `.5`.
    """
    rate = Decimal(str(vat_rate))
    return int(
        (Decimal(amount) * rate / Decimal(100)).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
    )


def calc_total_with_vat(amount: int, vat_rate: Decimal | float) -> int:
    return amount + calc_vat(amount, vat_rate)


class CampaignFeeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_tenant(
        self, tenant_id: int
    ) -> list[CampaignServiceFee]:
        rows = await self.db.scalars(
            select(CampaignServiceFee)
            .where(CampaignServiceFee.tenant_id == tenant_id)
            .order_by(CampaignServiceFee.created_at.desc())
        )
        return list(rows)

    async def list_for_campaign(
        self, *, tenant_id: int, campaign_id: int
    ) -> list[CampaignServiceFee]:
        rows = await self.db.scalars(
            select(CampaignServiceFee)
            .where(
                CampaignServiceFee.tenant_id == tenant_id,
                CampaignServiceFee.campaign_id == campaign_id,
            )
            .order_by(CampaignServiceFee.created_at.asc())
        )
        return list(rows)

    async def get_for_tenant(
        self, *, tenant_id: int, fee_id: int
    ) -> CampaignServiceFee:
        record = await self.db.scalar(
            select(CampaignServiceFee).where(
                CampaignServiceFee.id == fee_id,
                CampaignServiceFee.tenant_id == tenant_id,
            )
        )
        if record is None:
            raise FeeNotFoundError(f"Không tìm thấy khoản phí #{fee_id}")
        return record
