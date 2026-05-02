#!/usr/bin/env bash
# Nhóm A — Xác thực và phân quyền (TC-A01..A10)
source "$(dirname "$0")/../setup.sh"

log ""
log "${COLOR_BOLD}>>> Nhóm A — Xác thực và phân quyền${COLOR_RESET}"

# ---------- TC-A01: Đăng ký tài khoản hợp lệ ----------
NEW_EMAIL="testuser+$(date +%s)@e2e.vn"
NEW_PHONE="09$(printf '%08d' $((RANDOM*RANDOM % 100000000)))"
RESP=$(http POST /auth/register "{\"email\":\"$NEW_EMAIL\",\"phone\":\"$NEW_PHONE\",\"password\":\"e2etest1234\",\"full_name\":\"Test User\"}")
STATUS=$(echo "$RESP" | head -1); BODY=$(echo "$RESP" | tail -n +2)
assert_status "TC-A01" "Đăng ký hợp lệ" "201" "$STATUS" "$BODY"
NEW_USER_TOKEN=$(echo "$BODY" | jq -r '.access_token // empty')

# ---------- TC-A02: Đăng ký với email đã tồn tại ----------
RESP=$(http POST /auth/register "{\"email\":\"$NEW_EMAIL\",\"phone\":\"09$(printf '%08d' $((RANDOM*RANDOM % 100000000)))\",\"password\":\"another1234\",\"full_name\":\"Dup\"}")
STATUS=$(echo "$RESP" | head -1)
assert_status "TC-A02" "Email đã tồn tại → 409" "409" "$STATUS"

# ---------- TC-A03: Đăng nhập đúng ----------
TOKEN=$(login "$CUSTOMER1_EMAIL" "$CUSTOMER_PWD")
if [ -n "$TOKEN" ]; then
    log "${COLOR_GREEN}✅ TC-A03${COLOR_RESET}  Đăng nhập đúng → JWT"
    PASS=$((PASS+1))
else
    log "${COLOR_RED}❌ TC-A03${COLOR_RESET}  Đăng nhập không trả token"
    FAIL=$((FAIL+1))
fi

# ---------- TC-A04: Đăng nhập sai mật khẩu ----------
RESP=$(http POST /auth/login "{\"identifier\":\"$CUSTOMER1_EMAIL\",\"password\":\"wrong-password\"}")
STATUS=$(echo "$RESP" | head -1)
assert_status "TC-A04" "Sai mật khẩu → 401" "401" "$STATUS"

# ---------- TC-A05: Quên mật khẩu ----------
RESP=$(http POST /auth/forgot-password "{\"email\":\"$CUSTOMER2_EMAIL\"}")
STATUS=$(echo "$RESP" | head -1)
assert_status "TC-A05" "Forgot password → 200 (idempotent)" "200" "$STATUS"
# Verify side-effect: must_change_password=TRUE
FLAG=$(db_exec "SELECT must_change_password FROM users WHERE email='$CUSTOMER2_EMAIL';")
if [ "$FLAG" = "t" ]; then
    log "${COLOR_GREEN}✅ TC-A05b${COLOR_RESET}  must_change_password=TRUE cho $CUSTOMER2_EMAIL"
    PASS=$((PASS+1))
else
    log "${COLOR_RED}❌ TC-A05b${COLOR_RESET}  flag='$FLAG' (expected 't')"
    FAIL=$((FAIL+1))
fi
# Restore khach2 password để các TC sau dùng được
restore_user_password "$CUSTOMER2_EMAIL" "$CUSTOMER_PWD"

# ---------- TC-A06: Truy cập tính năng khi must_change_password=true ----------
# Setup: dùng khach3 — set known temp pwd + must_change_password=TRUE qua DB
TEMP_PWD="tempABC123!"
TARGET_TC_A06="khach3@gmail.com"
set_temp_password "$TARGET_TC_A06" "$TEMP_PWD"
TEMP_TOKEN=$(login "$TARGET_TC_A06" "$TEMP_PWD")
if [ -n "$TEMP_TOKEN" ]; then
    RESP=$(http GET /users/me/memberships "" "$TEMP_TOKEN")
    STATUS=$(echo "$RESP" | head -1); BODY=$(echo "$RESP" | tail -n +2)
    assert_status "TC-A06" "must_change_password=true → 423" "423" "$STATUS" "$BODY"
    DETAIL=$(echo "$BODY" | jq -r '.detail // empty')
    [ "$DETAIL" = "password_change_required" ] && \
        { log "${COLOR_GREEN}✅ TC-A06b${COLOR_RESET}  detail=password_change_required"; PASS=$((PASS+1)); } || \
        { log "${COLOR_RED}❌ TC-A06b${COLOR_RESET}  detail='$DETAIL' (expected 'password_change_required')"; FAIL=$((FAIL+1)); }
else
    log "${COLOR_RED}❌ TC-A06${COLOR_RESET}  Không login được bằng temp password"
    FAIL=$((FAIL+1))
fi

# ---------- TC-A07: Đổi mật khẩu mới ----------
NEW_PWD="newpass4567"
RESP=$(http PATCH /auth/me/password "{\"current_password\":\"$TEMP_PWD\",\"new_password\":\"$NEW_PWD\"}" "$TEMP_TOKEN")
STATUS=$(echo "$RESP" | head -1)
assert_status "TC-A07a" "Đổi mật khẩu → 204" "204" "$STATUS"
RESP=$(http GET /users/me/memberships "" "$TEMP_TOKEN")
STATUS=$(echo "$RESP" | head -1)
assert_status "TC-A07b" "Sau đổi mật khẩu → /users/me/memberships → 200" "200" "$STATUS"
# Restore password gốc cho khach3 (idempotent)
restore_user_password "$TARGET_TC_A06" "$CUSTOMER_PWD"

# ---------- TC-A08: Super admin loại trừ khỏi cơ chế buộc đổi ----------
# Setup: trigger forgot-password cho admin → set must_change_password=true
# (theo plan: super_admin SKIP — flag KHÔNG được set)
TEMP_PWD_ADMIN="adminTempXYZ!"
# Force set temp pwd + flag (bypass code path để test rằng dep block)
set_temp_password "$ADMIN_EMAIL" "$TEMP_PWD_ADMIN"
# Sau set bằng DB direct, flag=TRUE. Reset lại flag=FALSE manually để giả lập
# behavior expected: super_admin SKIP nên flag không bị bật.
db_exec "UPDATE users SET must_change_password=FALSE WHERE email='$ADMIN_EMAIL';" >/dev/null
ADMIN_TEMP_TOKEN=$(login "$ADMIN_EMAIL" "$TEMP_PWD_ADMIN")
if [ -n "$ADMIN_TEMP_TOKEN" ]; then
    RESP=$(http GET /admin/stats "" "$ADMIN_TEMP_TOKEN")
    STATUS=$(echo "$RESP" | head -1)
    assert_status "TC-A08" "Admin với pwd mới + flag=FALSE → /admin/stats → 200" "200" "$STATUS"
    # Verify code path: forgot-password thực tế cho admin có set flag không?
    # (super_admin SKIP theo plan — auth_service line check system_role)
    db_exec "UPDATE users SET must_change_password=FALSE WHERE email='$ADMIN_EMAIL';" >/dev/null
    curl -s -X POST "$BASE_URL/auth/forgot-password" -H "Content-Type: application/json" \
        -H "X-Forwarded-For: $(random_ip)" \
        -d "{\"email\":\"$ADMIN_EMAIL\"}" >/dev/null
    FLAG_AFTER=$(db_exec "SELECT must_change_password FROM users WHERE email='$ADMIN_EMAIL';")
    if [ "$FLAG_AFTER" = "f" ]; then
        log "${COLOR_GREEN}✅ TC-A08b${COLOR_RESET}  super_admin SKIP — flag vẫn FALSE sau forgot-password"
        PASS=$((PASS+1))
    else
        log "${COLOR_RED}❌ TC-A08b${COLOR_RESET}  flag = '$FLAG_AFTER' sau forgot-password (expected 'f')"
        FAIL=$((FAIL+1))
    fi
fi
# Restore admin password
restore_user_password "$ADMIN_EMAIL" "$ADMIN_PWD"

# ---------- TC-A09: Khách truy cập API quản trị ----------
RESP=$(http GET /admin/stats "" "$TOKEN")
STATUS=$(echo "$RESP" | head -1)
assert_status "TC-A09" "Khách → /admin/stats → 403" "403" "$STATUS"

# ---------- TC-A10: Nhân viên đối tác A thao tác đối tác B ----------
OWNER_CAFE_TOKEN=$(login "$OWNER_CAFE_EMAIL" "$OWNER_CAFE_PWD")
OWNER_LALA_TOKEN=$(login "$OWNER_LALA_EMAIL" "$OWNER_LALA_PWD")
PARTNER_LALA_ID=$(resolve_partner_id "$OWNER_LALA_TOKEN")
if [ -n "$OWNER_CAFE_TOKEN" ] && [ -n "$PARTNER_LALA_ID" ]; then
    # Owner Cafe gọi POS endpoint của Lala với X-Partner-Id=Lala
    RESP=$(http POST /partner/transactions "{\"phone\":\"0901234567\",\"gross_amount\":50000}" "$OWNER_CAFE_TOKEN" "$PARTNER_LALA_ID")
    STATUS=$(echo "$RESP" | head -1)
    assert_status "TC-A10" "Owner Cafe → POS Lala → 403" "403" "$STATUS"
fi

[ "${BASH_SOURCE[0]}" = "${0}" ] && summary
