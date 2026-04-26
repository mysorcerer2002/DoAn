from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.slug import generate_slug, generate_unique_slug
from app.models.partner import Partner, PartnerStatus
from app.models.user import User
from app.schemas.partner import PartnerCreateRequest, PartnerUpdateRequest


class PartnerNotFoundError(Exception):
    pass


class SlugConflictError(Exception):
    pass


class InvalidStatusTransitionError(Exception):
    """Raised khi cố thay đổi trạng thái đối tác theo hướng không hợp lệ."""

    pass


class PartnerService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_partner(self, *, owner: User, request: PartnerCreateRequest) -> Partner:
        """Tạo đối tác mới (status=pending). MVP final: 1 owner / shop, không có staff."""
        base = generate_slug(request.name) or "shop"
        existing_slugs = set(
            (
                await self.db.scalars(
                    select(Partner.slug).where(Partner.slug.like(f"{base}%"))
                )
            ).all()
        )
        slug = generate_unique_slug(request.name, existing_slugs)

        partner = Partner(
            name=request.name,
            slug=slug,
            owner_user_id=owner.id,
            status=PartnerStatus.PENDING,
            category=request.category,
            description=request.description,
            logo_url=request.logo_url,
            contact_phone=request.contact_phone,
            contact_email=request.contact_email,
            address=request.address,
            tax_code=request.tax_code,
            website=request.website,
            business_hours=request.business_hours,
            settings={},
        )
        self.db.add(partner)
        try:
            await self.db.flush()
        except IntegrityError as e:
            raise SlugConflictError(
                f"Slug '{slug}' already exists, please retry"
            ) from e
        await self.db.refresh(partner)
        return partner

    async def get_partner_by_id(self, partner_id: int) -> Partner:
        partner = await self.db.get(Partner, partner_id)
        if partner is None:
            raise PartnerNotFoundError(f"Partner {partner_id} not found")
        return partner

    async def get_partner_by_slug(self, slug: str) -> Partner | None:
        return await self.db.scalar(select(Partner).where(Partner.slug == slug))

    async def list_partners(self, *, status: PartnerStatus | None = None) -> list[Partner]:
        stmt = select(Partner).order_by(Partner.created_at.desc())
        if status is not None:
            stmt = stmt.where(Partner.status == status)
        return list((await self.db.scalars(stmt)).all())

    async def approve_partner(self, *, partner_id: int) -> Partner:
        """Approve đối tác: chỉ chấp nhận chuyển PENDING/SUSPENDED → ACTIVE."""
        partner = await self.get_partner_by_id(partner_id)
        if partner.status not in (PartnerStatus.PENDING, PartnerStatus.SUSPENDED):
            raise InvalidStatusTransitionError(
                f"Cannot approve partner in status {partner.status.value}"
            )
        partner.status = PartnerStatus.ACTIVE
        if partner.activated_at is None:
            partner.activated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return partner

    async def suspend_partner(self, *, partner_id: int) -> Partner:
        """Suspend đối tác: chỉ chấp nhận chuyển PENDING/ACTIVE → SUSPENDED."""
        partner = await self.get_partner_by_id(partner_id)
        if partner.status not in (PartnerStatus.PENDING, PartnerStatus.ACTIVE):
            raise InvalidStatusTransitionError(
                f"Cannot suspend partner in status {partner.status.value}"
            )
        partner.status = PartnerStatus.SUSPENDED
        await self.db.flush()
        return partner

    async def update_partner(
        self, *, partner_id: int, request: PartnerUpdateRequest
    ) -> Partner:
        partner = await self.get_partner_by_id(partner_id)
        for field, value in request.model_dump(exclude_unset=True).items():
            setattr(partner, field, value)
        await self.db.flush()
        return partner

    async def list_partners_for_user(self, *, user_id: int) -> list[dict]:
        """List đối tác mà user là owner hoặc active staff. Output match PartnerStaffSummary."""
        from app.models.partner_staff import PartnerStaff

        owner_partners = (
            await self.db.scalars(
                select(Partner)
                .where(Partner.owner_user_id == user_id)
                .order_by(Partner.created_at)
            )
        ).all()

        staff_partners = (
            await self.db.scalars(
                select(Partner)
                .join(PartnerStaff, PartnerStaff.partner_id == Partner.id)
                .where(
                    PartnerStaff.user_id == user_id,
                    PartnerStaff.is_active.is_(True),
                )
                .order_by(Partner.created_at)
            )
        ).all()

        result: list[dict] = []
        seen: set[int] = set()
        for p in owner_partners:
            if p.id in seen:
                continue
            seen.add(p.id)
            result.append(
                {
                    "id": p.id,
                    "name": p.name,
                    "slug": p.slug,
                    "logo_url": p.logo_url,
                    "status": p.status,
                    "role": "owner",
                }
            )
        for p in staff_partners:
            if p.id in seen:
                continue
            seen.add(p.id)
            result.append(
                {
                    "id": p.id,
                    "name": p.name,
                    "slug": p.slug,
                    "logo_url": p.logo_url,
                    "status": p.status,
                    "role": "staff",
                }
            )
        return result
