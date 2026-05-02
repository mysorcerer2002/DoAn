#!/usr/bin/env bash
# Nhóm B — Vòng đời đối tác (TC-B01..B10)
source "$(dirname "$0")/../setup.sh"

log ""
log "${COLOR_BOLD}>>> Nhóm B — Vòng đời đối tác${COLOR_RESET}"

# ---------- Setup: tạo customer + login để sau đó đăng ký partner ----------
NEW_OWNER_EMAIL="newowner+$(date +%s)@e2e.vn"
NEW_OWNER_PHONE="09$(printf '%08d' $((RANDOM*RANDOM % 100000000)))"
RESP=$(http POST /auth/register "{\"email\":\"$NEW_OWNER_EMAIL\",\"phone\":\"$NEW_OWNER_PHONE\",\"password\":\"e2etest1234\",\"full_name\":\"E2E Owner\"}")
NEW_OWNER_TOKEN=$(echo "$RESP" | tail -n +2 | jq -r '.access_token // empty')

# ---------- TC-B01: Đăng ký đối tác hợp lệ ----------
SHOP_NAME="E2E Shop $(date +%s)"
PARTNER_BODY=$(cat <<EOF
{
  "name": "$SHOP_NAME",
  "category": "cafe",
  "description": "E2E test shop",
  "contact_phone": "0900000001",
  "contact_email": "shop@e2e.vn",
  "address": "1 Street, HCM",
  "tax_code": "0123456789",
  "business_license_url": "/api/uploads/licenses/0/dummy.png",
  "accept_terms": true,
  "terms_version": "v1.0"
}
EOF
)
RESP=$(http POST /partner/register "$PARTNER_BODY" "$NEW_OWNER_TOKEN")
STATUS=$(echo "$RESP" | head -1); BODY=$(echo "$RESP" | tail -n +2)
assert_status "TC-B01" "Đăng ký đối tác hợp lệ → 201" "201" "$STATUS" "$BODY"
NEW_PARTNER_ID=$(echo "$BODY" | jq -r '.id // empty')

# ---------- TC-B02: Đăng ký đối tác thiếu giấy phép ----------
PARTNER_BODY_NO_LICENSE=$(cat <<EOF
{"name":"Bad Shop","category":"cafe","accept_terms":true,"terms_version":"v1.0"}
EOF
)
RESP=$(http POST /partner/register "$PARTNER_BODY_NO_LICENSE" "$NEW_OWNER_TOKEN")
STATUS=$(echo "$RESP" | head -1)
assert_status "TC-B02" "Thiếu business_license_url → 422" "422" "$STATUS"

# ---------- TC-B03: Quản trị viên phê duyệt ----------
ADMIN_TOKEN=$(login "$ADMIN_EMAIL" "$ADMIN_PWD")
if [ -n "$NEW_PARTNER_ID" ] && [ -n "$ADMIN_TOKEN" ]; then
    RESP=$(http POST "/admin/partners/$NEW_PARTNER_ID/approve" '{"approve":true,"reason":"Hồ sơ đầy đủ, duyệt"}' "$ADMIN_TOKEN")
    STATUS=$(echo "$RESP" | head -1); BODY=$(echo "$RESP" | tail -n +2)
    assert_status "TC-B03" "Phê duyệt → 200, status=active" "200" "$STATUS" "$BODY"
    assert_contains "TC-B03b" "Status thành active" "$BODY" "active"
fi

# ---------- TC-B04: Quản trị viên từ chối ----------
# Tạo partner mới khác để từ chối
PARTNER_BODY_REJECT=$(cat <<EOF
{
  "name": "Reject Shop $(date +%s)",
  "category": "food",
  "business_license_url": "/api/uploads/licenses/0/dummy.png",
  "accept_terms": true,
  "terms_version": "v1.0"
}
EOF
)
RESP=$(http POST /partner/register "$PARTNER_BODY_REJECT" "$NEW_OWNER_TOKEN")
REJECT_PARTNER_ID=$(echo "$RESP" | tail -n +2 | jq -r '.id // empty')
if [ -n "$REJECT_PARTNER_ID" ]; then
    RESP=$(http POST "/admin/partners/$REJECT_PARTNER_ID/approve" '{"approve":false,"reason":"Giấy phép giả"}' "$ADMIN_TOKEN")
    STATUS=$(echo "$RESP" | head -1); BODY=$(echo "$RESP" | tail -n +2)
    assert_status "TC-B04" "Từ chối → 200" "200" "$STATUS" "$BODY"
    assert_contains "TC-B04b" "Trạng thái suspended/rejected" "$BODY" "suspended\|rejected"
fi

# ---------- TC-B05: Đối tác chưa duyệt cố thao tác endpoint cần partner active ----------
# Tạo partner pending mới (không approve) → owner gọi GET /partners/me → 403
NEW_PENDING_OWNER="b05+$(date +%s)@e2e.vn"
NEW_PENDING_PHONE="09$(printf '%08d' $((RANDOM*RANDOM % 100000000)))"
RESP=$(http POST /auth/register "{\"email\":\"$NEW_PENDING_OWNER\",\"phone\":\"$NEW_PENDING_PHONE\",\"password\":\"e2etest1234\",\"full_name\":\"Pending Owner\"}")
PENDING_OWNER_TOKEN=$(echo "$RESP" | tail -n +2 | jq -r '.access_token')
PENDING_BODY=$(cat <<EOF
{"name":"Pending Shop $(date +%s)","category":"cafe","business_license_url":"/api/uploads/licenses/0/d.png","accept_terms":true,"terms_version":"v1.0"}
EOF
)
RESP=$(http POST /partner/register "$PENDING_BODY" "$PENDING_OWNER_TOKEN")
PENDING_PARTNER_ID=$(echo "$RESP" | tail -n +2 | jq -r '.id')
if [ -n "$PENDING_PARTNER_ID" ]; then
    RESP=$(http GET /partners/me "" "$PENDING_OWNER_TOKEN" "$PENDING_PARTNER_ID")
    STATUS=$(echo "$RESP" | head -1)
    assert_status "TC-B05" "Pending partner gọi /partners/me → 403" "403" "$STATUS"
fi

# ---------- TC-B06: Tạm dừng đối tác đang hoạt động ----------
if [ -n "$NEW_PARTNER_ID" ]; then
    RESP=$(http POST "/admin/partners/$NEW_PARTNER_ID/suspend" '{"reason":"Vi phạm điều khoản dịch vụ"}' "$ADMIN_TOKEN")
    STATUS=$(echo "$RESP" | head -1); BODY=$(echo "$RESP" | tail -n +2)
    assert_status "TC-B06" "Suspend → 200" "200" "$STATUS" "$BODY"
    # Verify audit log
    RESP=$(http GET "/admin/audit-logs?action=partner_suspend&target_id=$NEW_PARTNER_ID" "" "$ADMIN_TOKEN")
    BODY=$(echo "$RESP" | tail -n +2)
    REASON=$(echo "$BODY" | jq -r '.items[0].reason // empty')
    if [ "$REASON" = "Vi phạm điều khoản dịch vụ" ]; then
        log "${COLOR_GREEN}✅ TC-B06b${COLOR_RESET}  Audit log có lý do '$REASON'"
        PASS=$((PASS+1))
    else
        log "${COLOR_RED}❌ TC-B06b${COLOR_RESET}  Audit log thiếu lý do, got: '$REASON'"
        FAIL=$((FAIL+1))
    fi
fi

# ---------- TC-B07: Cấu hình tỷ lệ tích điểm ----------
OWNER_CAFE_TOKEN=$(login "$OWNER_CAFE_EMAIL" "$OWNER_CAFE_PWD")
PARTNER_CAFE_ID=$(resolve_partner_id "$OWNER_CAFE_TOKEN")
RESP=$(http GET /partner/point-rules/active "" "$OWNER_CAFE_TOKEN" "$PARTNER_CAFE_ID")
BODY=$(echo "$RESP" | tail -n +2)
EXISTING_RULE_ID=$(echo "$BODY" | jq -r '.id // empty')
if [ -n "$EXISTING_RULE_ID" ]; then
    RESP=$(http PATCH "/partner/point-rules/$EXISTING_RULE_ID" '{"earn_percent":1.0}' "$OWNER_CAFE_TOKEN" "$PARTNER_CAFE_ID")
    STATUS=$(echo "$RESP" | head -1); BODY=$(echo "$RESP" | tail -n +2)
    assert_status "TC-B07" "Cập nhật earn_percent=1% → 200" "200" "$STATUS" "$BODY"
    assert_contains "TC-B07b" "earn_percent = 1.00" "$BODY" "\"earn_percent\":\"1.00\"\|\"earn_percent\":1"
fi

# ---------- TC-B08: Cấu hình hạng thành viên ----------
log "${COLOR_YELLOW}TC-B08${COLOR_RESET} verify thủ công qua UI /partner/settings → tab Hạng thành viên hoặc API:"
log "    GET /partner/tiers → list 3 hạng (Bronze/Silver/Gold) đã seed"
RESP=$(http GET /partner/tiers "" "$OWNER_CAFE_TOKEN" "$PARTNER_CAFE_ID")
STATUS=$(echo "$RESP" | head -1); BODY=$(echo "$RESP" | tail -n +2)
TIER_COUNT=$(echo "$BODY" | jq 'length // 0')
if [ "$STATUS" = "200" ] && [ "${TIER_COUNT:-0}" -ge 3 ]; then
    log "${COLOR_GREEN}✅ TC-B08${COLOR_RESET}  3+ hạng tồn tại (count=$TIER_COUNT)"
    PASS=$((PASS+1))
else
    log "${COLOR_RED}❌ TC-B08${COLOR_RESET}  status=$STATUS count=$TIER_COUNT"
    FAIL=$((FAIL+1))
fi

# ---------- TC-B09 + TC-B10: Bật/tắt cờ use_tiers ----------
if [ -n "$EXISTING_RULE_ID" ]; then
    # Bật use_tiers
    RESP=$(http PATCH "/partner/point-rules/$EXISTING_RULE_ID" '{"use_tiers":true}' "$OWNER_CAFE_TOKEN" "$PARTNER_CAFE_ID")
    BODY=$(echo "$RESP" | tail -n +2)
    USE_TIERS=$(echo "$BODY" | jq -r '.use_tiers')
    if [ "$USE_TIERS" = "true" ]; then
        log "${COLOR_GREEN}✅ TC-B09${COLOR_RESET}  Bật use_tiers → true"
        PASS=$((PASS+1))
    else
        log "${COLOR_RED}❌ TC-B09${COLOR_RESET}  use_tiers không = true"
        FAIL=$((FAIL+1))
    fi

    # Tắt use_tiers
    RESP=$(http PATCH "/partner/point-rules/$EXISTING_RULE_ID" '{"use_tiers":false}' "$OWNER_CAFE_TOKEN" "$PARTNER_CAFE_ID")
    BODY=$(echo "$RESP" | tail -n +2)
    USE_TIERS=$(echo "$BODY" | jq -r '.use_tiers')
    if [ "$USE_TIERS" = "false" ]; then
        log "${COLOR_GREEN}✅ TC-B10${COLOR_RESET}  Tắt use_tiers → false"
        PASS=$((PASS+1))
    else
        log "${COLOR_RED}❌ TC-B10${COLOR_RESET}  use_tiers không = false"
        FAIL=$((FAIL+1))
    fi
fi

[ "${BASH_SOURCE[0]}" = "${0}" ] && summary
