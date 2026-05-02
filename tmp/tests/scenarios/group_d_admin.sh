#!/usr/bin/env bash
# Nhóm D — Quản trị và kiểm toán (TC-D01..D07)
source "$(dirname "$0")/../setup.sh"

log ""
log "${COLOR_BOLD}>>> Nhóm D — Quản trị và kiểm toán${COLOR_RESET}"

ADMIN_TOKEN=$(login "$ADMIN_EMAIL" "$ADMIN_PWD")
if [ -z "$ADMIN_TOKEN" ]; then
    log "${COLOR_RED}Setup fail: không login được admin${COLOR_RESET}"; summary; exit 1
fi

# Tạo customer mới làm victim test khoá
TARGET_EMAIL="target+$(date +%s)@e2e.vn"
TARGET_PHONE="09$(printf '%08d' $((RANDOM*RANDOM % 100000000)))"
RESP=$(http POST /auth/register "{\"email\":\"$TARGET_EMAIL\",\"phone\":\"$TARGET_PHONE\",\"password\":\"victim1234\",\"full_name\":\"Target\"}")
TARGET_BODY=$(echo "$RESP" | tail -n +2)
TARGET_TOKEN=$(echo "$TARGET_BODY" | jq -r '.access_token')
TARGET_ID=$(curl -s "$BASE_URL/auth/me" -H "Authorization: Bearer $TARGET_TOKEN" -H "X-Forwarded-For: $(random_ip)" | jq -r '.id')
log "    Target user: $TARGET_EMAIL (id=$TARGET_ID)"

# ---------- TC-D01: Khóa tài khoản khách hàng ----------
RESP=$(http PATCH "/admin/users/$TARGET_ID" \
    '{"is_active":false,"reason":"Khoá test E2E - vi phạm điều khoản"}' \
    "$ADMIN_TOKEN")
STATUS=$(echo "$RESP" | head -1); BODY=$(echo "$RESP" | tail -n +2)
assert_status "TC-D01" "Khoá user → 200" "200" "$STATUS" "$BODY"
IS_ACTIVE=$(echo "$BODY" | jq -r '.is_active')
[ "$IS_ACTIVE" = "false" ] && { log "${COLOR_GREEN}✅ TC-D01b${COLOR_RESET}  is_active=false"; PASS=$((PASS+1)); } \
    || { log "${COLOR_RED}❌ TC-D01b${COLOR_RESET}  is_active=$IS_ACTIVE"; FAIL=$((FAIL+1)); }

# Verify audit log
RESP=$(http GET "/admin/audit-logs?action=user_lock&target_id=$TARGET_ID" "" "$ADMIN_TOKEN")
BODY=$(echo "$RESP" | tail -n +2)
TOTAL=$(echo "$BODY" | jq -r '.total // 0')
REASON=$(echo "$BODY" | jq -r '.items[0].reason // empty')
# Lưu ý: jq `// empty` treat `false` as falsy → dùng tostring để giữ nguyên giá trị
BEFORE=$(echo "$BODY" | jq -r '.items[0].before_snapshot.is_active | tostring')
AFTER=$(echo "$BODY" | jq -r '.items[0].after_snapshot.is_active | tostring')
if [ "$TOTAL" -ge 1 ] && [ -n "$REASON" ] && [ "$BEFORE" = "true" ] && [ "$AFTER" = "false" ]; then
    log "${COLOR_GREEN}✅ TC-D01c${COLOR_RESET}  Audit log có reason='$REASON', before/after snapshot"
    PASS=$((PASS+1))
else
    log "${COLOR_RED}❌ TC-D01c${COLOR_RESET}  Audit log thiếu thông tin (total=$TOTAL reason='$REASON' before=$BEFORE after=$AFTER)"
    FAIL=$((FAIL+1))
fi

# ---------- TC-D02: Khách bị khóa cố đăng nhập ----------
RESP=$(http POST /auth/login "{\"identifier\":\"$TARGET_EMAIL\",\"password\":\"victim1234\"}")
STATUS=$(echo "$RESP" | head -1)
# Backend trả 401 với message "Account is disabled" cho user is_active=false
assert_status "TC-D02" "User khoá đăng nhập → 401" "401" "$STATUS"

# ---------- TC-D03: Mở khoá tài khoản ----------
RESP=$(http PATCH "/admin/users/$TARGET_ID" \
    '{"is_active":true,"reason":"Mở khoá sau khi xác minh"}' \
    "$ADMIN_TOKEN")
STATUS=$(echo "$RESP" | head -1); BODY=$(echo "$RESP" | tail -n +2)
assert_status "TC-D03" "Mở khoá → 200" "200" "$STATUS"
RESP=$(http GET "/admin/audit-logs?action=user_unlock&target_id=$TARGET_ID" "" "$ADMIN_TOKEN")
BODY=$(echo "$RESP" | tail -n +2)
TOTAL=$(echo "$BODY" | jq -r '.total // 0')
[ "$TOTAL" -ge 1 ] && { log "${COLOR_GREEN}✅ TC-D03b${COLOR_RESET}  Audit log user_unlock entry"; PASS=$((PASS+1)); } \
    || { log "${COLOR_RED}❌ TC-D03b${COLOR_RESET}  Không thấy audit log unlock"; FAIL=$((FAIL+1)); }

# ---------- TC-D04: Tra cứu nhật ký đăng nhập ----------
RESP=$(http GET "/admin/login-logs?identifier=$TARGET_EMAIL&limit=20" "" "$ADMIN_TOKEN")
STATUS=$(echo "$RESP" | head -1); BODY=$(echo "$RESP" | tail -n +2)
assert_status "TC-D04" "GET login-logs filter → 200" "200" "$STATUS"
LOGIN_COUNT=$(echo "$BODY" | jq -r '.total // 0')
log "    Tổng login attempts cho $TARGET_EMAIL: $LOGIN_COUNT"

# ---------- TC-D05: Tra cứu nhật ký điều chỉnh điểm ----------
RESP=$(http GET "/admin/point-adjustments?limit=10" "" "$ADMIN_TOKEN")
STATUS=$(echo "$RESP" | head -1); BODY=$(echo "$RESP" | tail -n +2)
assert_status "TC-D05" "GET point-adjustments → 200" "200" "$STATUS"
log "    Sample size: $(echo "$BODY" | jq -r '.items | length')"

# ---------- TC-D06: Tra cứu nhật ký quản trị ----------
RESP=$(http GET "/admin/audit-logs?limit=20" "" "$ADMIN_TOKEN")
STATUS=$(echo "$RESP" | head -1); BODY=$(echo "$RESP" | tail -n +2)
assert_status "TC-D06" "GET audit-logs → 200" "200" "$STATUS"
ITEMS_COUNT=$(echo "$BODY" | jq -r '.items | length')
log "    Sample audit logs: $ITEMS_COUNT"
HAS_BEFORE_AFTER=$(echo "$BODY" | jq -r '[.items[] | select(.before_snapshot != null and .after_snapshot != null)] | length')
[ "${HAS_BEFORE_AFTER:-0}" -ge 1 ] && { log "${COLOR_GREEN}✅ TC-D06b${COLOR_RESET}  Có entry với before+after snapshot"; PASS=$((PASS+1)); } \
    || { log "${COLOR_YELLOW}⚠️  TC-D06b${COLOR_RESET}  Không có entry nào có before+after (cần seed thêm test data)"; }

# ---------- TC-D07: Dòng sự kiện gần đây ----------
RESP=$(http GET "/admin/audit-feed?limit=20" "" "$ADMIN_TOKEN")
STATUS=$(echo "$RESP" | head -1); BODY=$(echo "$RESP" | tail -n +2)
assert_status "TC-D07" "GET audit-feed → 200" "200" "$STATUS"
EVENT_COUNT=$(echo "$BODY" | jq -r 'length // 0')
log "    Số sự kiện gần đây: $EVENT_COUNT"

[ "${BASH_SOURCE[0]}" = "${0}" ] && summary
