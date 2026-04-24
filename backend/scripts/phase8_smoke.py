"""Smoke test Phase 8 — admin approval queue."""

import asyncio
import json
import urllib.request
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import AsyncSessionLocal
from app.core.security import create_access_token
from app.models.campaign import Campaign
from app.models.campaign_approval_event import CampaignApprovalEvent
from app.models.campaign_regulatory_submission import CampaignRegulatorySubmission
from app.models.tenant import Tenant
from app.models.membership import Membership
from app.models.tenant_authorization import TenantAuthorization
from app.models.user import User
from app.models.voucher import Voucher, VoucherStatus


BASE = "http://localhost:8000"


def _req(method: str, path: str, *, token: str, body: dict | None = None) -> tuple[int, dict]:
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, headers=headers, method=method, data=data)
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"null")


async def _get_admin(db: AsyncSession) -> User:
    u = await db.scalar(select(User).where(User.system_role == "super_admin"))
    if u is None:
        raise RuntimeError("Cần super_admin user trong DB")
    return u


async def _create_pending_campaign(
    db: AsyncSession, *, tenant_id: int, owner_id: int, with_auth: bool = True
) -> tuple[Campaign, int | None]:
    now = datetime.now(timezone.utc)
    c = Campaign(
        tenant_id=tenant_id,
        name="Phase8 smoke " + str(int(now.timestamp() * 1000) % 10_000_000),
        description="Smoke campaign",
        discount_type="percent",
        discount_value=20,
        min_order=0,
        starts_at=now + timedelta(days=1),
        ends_at=now + timedelta(days=8),
        program_form="giam_gia",
        approval_status="pending_approval",
        approval_tier="notify_so_ct",
        estimated_cost=1_000_000,
        realized_cost=0,
        authorization_id=None,
        created_by_user_id=owner_id,
    )
    db.add(c)
    await db.flush()

    auth_id: int | None = None
    if with_auth:
        auth = TenantAuthorization(
            tenant_id=tenant_id,
            scope="per_campaign",
            campaign_id=c.id,
            document_content_hash="hash_smoke_" + str(int(now.timestamp() * 1000)),
            signed_by_user_id=owner_id,
            signed_at=now,
            signature_method="otp_email",
            signature_payload={"ip": "127.0.0.1", "otp_purpose": "sign_authorization"},
            valid_from=now,
            valid_until=now + timedelta(days=365),
            retention_until=now + timedelta(days=365 * 10 + 5),
        )
        db.add(auth)
        await db.flush()
        auth_id = auth.id
        c.authorization_id = auth_id
        await db.flush()
    return c, auth_id


async def _create_voucher(
    db: AsyncSession, *, campaign: Campaign, tenant_id: int, status: str, membership_id: int
) -> int:
    ts = int(datetime.now(timezone.utc).timestamp() * 1000) % 100_000_000
    # code 8 ký tự alphanumeric uppercase
    code = f"SM{campaign.id:03d}{ts % 1000:03d}"[:8].upper()
    now = datetime.now(timezone.utc)
    v = Voucher(
        tenant_id=tenant_id,
        campaign_id=campaign.id,
        membership_id=membership_id,
        code=code,
        status=status,
        issue_source="manual",
        discount_snapshot={"discount_type": "percent", "discount_value": 20, "min_order": 0},
        issued_at=now,
        expires_at=now + timedelta(days=30),
    )
    db.add(v)
    await db.flush()
    return v.id


async def main():
    async with AsyncSessionLocal() as db:
        admin = await _get_admin(db)
        token = create_access_token(admin.id)

        # Pick any tenant + owner
        tenant = await db.scalar(select(Tenant).where(Tenant.id > 0))
        owner = await db.scalar(select(User).where(User.system_role == "regular"))
        print(f"admin={admin.id} tenant={tenant.id} owner={owner.id}")

        # ── Scenario A: approve flow ───────────────────────────────────
        c, auth_id = await _create_pending_campaign(db, tenant_id=tenant.id, owner_id=owner.id)
        await db.commit()
        print(f"\n[A] pending campaign #{c.id} auth #{auth_id}")

        code, rows = _req("GET", "/admin/campaigns/pending", token=token)
        assert code == 200 and any(r["id"] == c.id for r in rows), f"list_pending fail {code} {rows}"
        print(f"  list_pending OK — có {len(rows)} row")

        # Approve khi chưa có xac_nhan_so_ct → 400
        code, body = _req("POST", f"/admin/campaigns/{c.id}/approve", token=token)
        assert code == 400 and "xác nhận" in body["detail"].lower(), f"guard c fail {code} {body}"
        print(f"  approve thiếu xác nhận → 400 OK ({body['detail']})")

        # Mark ops started
        code, body = _req("POST", f"/admin/campaigns/{c.id}/mark-ops-started", token=token)
        assert code == 200 and body["ops_filing_started_at"] is not None, f"mark ops fail {code} {body}"
        print(f"  mark_ops_started OK — ops_filing_started_at={body['ops_filing_started_at']}")

        # Upload xac_nhan_so_ct
        code, body = _req(
            "POST",
            f"/admin/campaigns/{c.id}/regulatory-submissions",
            token=token,
            body={"doc_type": "xac_nhan_so_ct", "reference_no": "SCT-2026-001"},
        )
        assert code == 201, f"regulatory fail {code} {body}"
        print(f"  regulatory-submission xac_nhan OK #{body['id']}")

        # Approve
        code, body = _req("POST", f"/admin/campaigns/{c.id}/approve", token=token)
        assert code == 200 and body["approval_status"] == "approved", f"approve fail {code} {body}"
        assert body["post_report_due_at"] is not None
        print(f"  approve OK — post_report_due_at={body['post_report_due_at']}")

        # Events log
        code, ev = _req("GET", f"/admin/campaigns/{c.id}/events", token=token)
        types = [e["event_type"] for e in ev]
        assert "ops_started" in types and "approved" in types, f"events miss {types}"
        print(f"  events={types}")

        # ── Scenario B: reject + cascade cancel issued-only ────────────
        c2, _ = await _create_pending_campaign(db, tenant_id=tenant.id, owner_id=owner.id)
        membership = await db.scalar(
            select(Membership).where(Membership.tenant_id == tenant.id)
        )
        assert membership is not None, "Cần membership sẵn có trong tenant để tạo voucher"
        v_issued = await _create_voucher(
            db, campaign=c2, tenant_id=tenant.id, status=VoucherStatus.ISSUED.value, membership_id=membership.id,
        )
        v_used = await _create_voucher(
            db, campaign=c2, tenant_id=tenant.id, status=VoucherStatus.USED.value, membership_id=membership.id,
        )
        await db.commit()
        print(f"\n[B] campaign #{c2.id} + voucher issued #{v_issued} + used #{v_used}")

        # Reject không ack → 409 USED_VOUCHERS_REQUIRE_ACK
        code, body = _req(
            "POST",
            f"/admin/campaigns/{c2.id}/reject",
            token=token,
            body={"reason": "Scope đi lệch NĐ 81", "acknowledge_used_vouchers": False},
        )
        assert code == 409 and body["detail"]["code"] == "USED_VOUCHERS_REQUIRE_ACK", (
            f"reject no-ack fail {code} {body}"
        )
        assert body["detail"]["used_count"] == 1
        print(f"  reject no-ack → 409 USED_VOUCHERS_REQUIRE_ACK (used_count=1) OK")

        # Reject có ack → 200
        code, body = _req(
            "POST",
            f"/admin/campaigns/{c2.id}/reject",
            token=token,
            body={"reason": "Scope đi lệch NĐ 81", "acknowledge_used_vouchers": True},
        )
        assert code == 200 and body["approval_status"] == "rejected", f"reject fail {code} {body}"
        print(f"  reject with-ack → rejected OK")

        # Verify cascade: issued → cancelled, used vẫn used
        v1 = await db.scalar(select(Voucher).where(Voucher.id == v_issued))
        v2 = await db.scalar(select(Voucher).where(Voucher.id == v_used))
        await db.refresh(v1)
        await db.refresh(v2)
        assert v1.status == VoucherStatus.CANCELLED.value, f"issued voucher không cancel: {v1.status}"
        assert v2.status == VoucherStatus.USED.value, f"used voucher bị đụng: {v2.status}"
        print(f"  cascade OK — issued→cancelled ({v1.status}), used giữ nguyên ({v2.status})")

        # ── Scenario C: campaign not found → 404 ───────────────────────
        code, body = _req("POST", "/admin/campaigns/999999/approve", token=token)
        assert code == 404, f"not found fail {code} {body}"
        print(f"\n[C] approve #999999 → 404 OK")

        # ── Scenario D: doc_type invalid → 400 ─────────────────────────
        code, body = _req(
            "POST",
            f"/admin/campaigns/{c.id}/regulatory-submissions",
            token=token,
            body={"doc_type": "bogus_type", "reference_no": "x"},
        )
        assert code == 400, f"invalid doc fail {code} {body}"
        print(f"[D] doc_type=bogus → 400 OK")

        # ── Scenario E: overdue-reports ─────────────────────────────────
        # Force c approved + post_report_due_at past
        await db.execute(
            text(
                "UPDATE campaigns SET post_report_due_at = :d, post_report_submitted_at = NULL WHERE id = :i"
            ),
            {"d": datetime.now(timezone.utc) - timedelta(days=3), "i": c.id},
        )
        await db.commit()
        code, rows = _req("GET", "/admin/campaigns/overdue-reports", token=token)
        assert code == 200 and any(r["id"] == c.id for r in rows), f"overdue fail {code} {rows}"
        print(f"[E] overdue-reports — campaign #{c.id} days_overdue=3 OK")

        print("\n✅ Phase 8 smoke PASS")


if __name__ == "__main__":
    asyncio.run(main())
