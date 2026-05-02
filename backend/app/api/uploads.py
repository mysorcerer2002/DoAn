"""Partner uploads API — image upload cho logo / banner."""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

from app.core.deps import get_current_user, get_partner_id, require_owner_in_partner
from app.models.user import User

router = APIRouter(prefix="/partner/uploads", tags=["partner-uploads"])

UPLOAD_ROOT = Path("uploads")
ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp"}
MAX_BYTES = {
    "logo": 2 * 1024 * 1024,    # 2MB
    "banner": 5 * 1024 * 1024,  # 5MB
}


@router.post("/image")
async def upload_image(
    kind: str = Query(..., pattern="^(logo|banner)$"),
    file: UploadFile = File(...),
    partner_id: int = Depends(get_partner_id),
    _=Depends(require_owner_in_partner),
) -> dict[str, str]:
    """Upload logo/banner image cho partner. Trả về URL public.

    Lưu tại uploads/<partner_id>/<uuid>.<ext>. Whitelist .jpg/.jpeg/.png/.webp.
    Logo ≤2MB, banner ≤5MB. Không resize, không xoá file cũ (MVP).
    """
    filename = (file.filename or "").strip()
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(
            status_code=400,
            detail="Định dạng không hỗ trợ. Chỉ chấp nhận .jpg, .jpeg, .png, .webp",
        )

    contents = await file.read()
    max_size = MAX_BYTES[kind]
    if len(contents) > max_size:
        mb = max_size // (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=f"Ảnh vượt quá {mb}MB. Vui lòng nén hoặc chọn ảnh khác.",
        )
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="File rỗng")

    partner_dir = UPLOAD_ROOT / str(partner_id)
    partner_dir.mkdir(parents=True, exist_ok=True)
    new_name = f"{uuid.uuid4().hex}{ext}"
    target = partner_dir / new_name
    target.write_bytes(contents)

    # URL trả về dùng prefix /api/uploads/ để đi qua Next.js rewrite (/api/:path*)
    # → đồng nhất origin với FE; backend StaticFiles serve tại /uploads/.
    return {"url": f"/api/uploads/{partner_id}/{new_name}"}


@router.post("/license")
async def upload_license(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    """Upload ảnh giấy phép kinh doanh — dùng trước khi đăng ký partner.

    Khác /partner/uploads/image (cần owner role): endpoint này chỉ cần
    authenticated user — user chưa có partner khi đăng ký lần đầu.
    Whitelist .jpg/.jpeg/.png/.webp, max 5MB.
    Path: uploads/licenses/<user_id>/<uuid>.<ext>.
    """
    filename = (file.filename or "").strip()
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(
            status_code=400,
            detail="Định dạng không hỗ trợ. Chỉ chấp nhận .jpg, .jpeg, .png, .webp",
        )

    contents = await file.read()
    MAX_LICENSE = 5 * 1024 * 1024
    if len(contents) > MAX_LICENSE:
        raise HTTPException(status_code=413, detail="Ảnh vượt quá 5MB")
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="File rỗng")

    license_dir = UPLOAD_ROOT / "licenses" / str(current_user.id)
    license_dir.mkdir(parents=True, exist_ok=True)
    new_name = f"{uuid.uuid4().hex}{ext}"
    target = license_dir / new_name
    target.write_bytes(contents)

    return {"url": f"/api/uploads/licenses/{current_user.id}/{new_name}"}
