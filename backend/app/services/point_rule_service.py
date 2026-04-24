from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.point_rule import PointRule
from app.schemas.point_rule import PointRuleCreateRequest


class PointRuleService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_active_rule(self, *, partner_id: int) -> PointRule | None:
        return await self.db.scalar(
            select(PointRule).where(
                PointRule.partner_id == partner_id, PointRule.is_active.is_(True)
            )
        )

    async def list_rules(self, *, partner_id: int) -> list[PointRule]:
        rows = await self.db.scalars(
            select(PointRule)
            .where(PointRule.partner_id == partner_id)
            .order_by(PointRule.created_at.desc())
        )
        return list(rows.all())

    async def create_rule(
        self, *, partner_id: int, request: PointRuleCreateRequest
    ) -> PointRule:
        # Deactivate active rules cũ
        await self.db.execute(
            update(PointRule)
            .where(
                PointRule.partner_id == partner_id, PointRule.is_active.is_(True)
            )
            .values(is_active=False)
        )
        await self.db.flush()

        rule = PointRule(
            partner_id=partner_id,
            points_per_unit=request.points_per_unit,
            unit_amount=request.unit_amount,
            min_amount=request.min_amount,
            is_active=True,
        )
        self.db.add(rule)
        await self.db.flush()
        await self.db.refresh(rule)
        return rule
