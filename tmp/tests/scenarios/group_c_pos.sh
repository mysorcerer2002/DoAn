#!/usr/bin/env bash
# Nhóm C — Tích điểm và đổi quà (TC-C01..C16 + TC-C13b)
source "$(dirname "$0")/../setup.sh"

log ""
log "${COLOR_BOLD}>>> Nhóm C — Tích điểm và đổi quà${COLOR_RESET}"

# ---------- Setup tokens ----------
OWNER_CAFE_TOKEN=$(login "$OWNER_CAFE_EMAIL" "$OWNER_CAFE_PWD")
PARTNER_CAFE_ID=$(resolve_partner_id "$OWNER_CAFE_TOKEN")
OWNER_LALA_TOKEN=$(login "$OWNER_LALA_EMAIL" "$OWNER_LALA_PWD")
PARTNER_LALA_ID=$(resolve_partner_id "$OWNER_LALA_TOKEN")
CUSTOMER1_TOKEN=$(login "$CUSTOMER1_EMAIL" "$CUSTOMER_PWD")

if [ -z "$PARTNER_CAFE_ID" ]; then
    log "${COLOR_RED}Setup fail: không lấy được PARTNER_CAFE_ID${COLOR_RESET}"
    summary; exit 1
fi
log "    Partner Cafe ID = $PARTNER_CAFE_ID; Lala ID = $PARTNER_LALA_ID"

# Top-up khach1 để chắc chắn có đủ điểm cho mọi TC (50k điểm)
KHACH1_USER_ID=$(db_exec "SELECT id FROM users WHERE email='$CUSTOMER1_EMAIL';")
db_exec "UPDATE users SET points_balance = GREATEST(points_balance, 50000) WHERE id=$KHACH1_USER_ID;" >/dev/null
log "    Top-up khach1 (id=$KHACH1_USER_ID) → ≥ 50.000 điểm"

# ---------- TC-C01: Tích điểm POS với khách đã có hồ sơ ----------
# Spec yêu cầu KHÁCH ĐÃ CÓ HỒ SƠ ở shop. Dùng phone thực của khach1 (đã có
# membership ở Cafe). Đảm bảo earn_percent=1.00 và use_tiers=FALSE (cleanup
# state từ test trước nếu có) để 200k @ 1% = đúng 2000 điểm (không nhân hệ số).
KHACH1_REAL_PHONE=$(db_exec "SELECT phone FROM users WHERE email='$CUSTOMER1_EMAIL';")
db_exec "UPDATE point_rules SET earn_percent=1.00, use_tiers=FALSE WHERE partner_id=$PARTNER_CAFE_ID AND is_active=TRUE;" >/dev/null
LIFETIME_BEFORE_C01=$(db_exec "SELECT lifetime_earned FROM memberships WHERE user_id=(SELECT id FROM users WHERE email='$CUSTOMER1_EMAIL') AND partner_id=$PARTNER_CAFE_ID;")
RESP=$(http POST /partner/transactions \
    "{\"phone\":\"$KHACH1_REAL_PHONE\",\"gross_amount\":200000}" \
    "$OWNER_CAFE_TOKEN" "$PARTNER_CAFE_ID")
STATUS=$(echo "$RESP" | head -1); BODY=$(echo "$RESP" | tail -n +2)
assert_status "TC-C01" "POS khach1 ($KHACH1_REAL_PHONE) tích 200k @ 1% → 201" "201" "$STATUS" "$BODY"
POINTS=$(echo "$BODY" | jq -r '.transaction.points_earned // 0')
if [ "$POINTS" = "2000" ]; then
    log "${COLOR_GREEN}✅ TC-C01b${COLOR_RESET}  Điểm cộng = 2000 (chính xác công thức 200k × 1%)"
    PASS=$((PASS+1))
else
    log "${COLOR_RED}❌ TC-C01b${COLOR_RESET}  Điểm cộng = $POINTS (expected 2000)"
    FAIL=$((FAIL+1))
fi
# Verify ledger entry có actor_user_id
TXN_ID=$(echo "$BODY" | jq -r '.transaction.id')
ACTOR=$(db_exec "SELECT actor_user_id FROM point_ledger WHERE ref_id=$TXN_ID AND reason='earn' ORDER BY id DESC LIMIT 1;")
OWNER_ID=$(db_exec "SELECT id FROM users WHERE email='$OWNER_CAFE_EMAIL';")
if [ "$ACTOR" = "$OWNER_ID" ]; then
    log "${COLOR_GREEN}✅ TC-C01c${COLOR_RESET}  Ledger có actor_user_id=$ACTOR (=owner Cafe)"
    PASS=$((PASS+1))
else
    log "${COLOR_RED}❌ TC-C01c${COLOR_RESET}  Ledger actor_user_id='$ACTOR' (expected owner=$OWNER_ID)"
    FAIL=$((FAIL+1))
fi

# ---------- TC-C02: Tích điểm POS với khách lần đầu giao dịch ----------
NEW_PHONE_C02="091$(printf '%07d' $((RANDOM*RANDOM % 10000000)))"
RESP=$(http POST /partner/transactions \
    "{\"phone\":\"$NEW_PHONE_C02\",\"gross_amount\":100000}" \
    "$OWNER_CAFE_TOKEN" "$PARTNER_CAFE_ID")
STATUS=$(echo "$RESP" | head -1); BODY=$(echo "$RESP" | tail -n +2)
assert_status "TC-C02" "Khách mới qua phone → 201, auto-create membership" "201" "$STATUS" "$BODY"

# ---------- Setup tier IDs đúng theo spec ----------
# Cafe có 4 hạng theo seed: Đồng (id=1, min=0), Bạc (id=2, min=500),
# Vàng (id=3, min=2000), Bạch Kim (id=4, min=5000).
# Spec QT3: hệ số hạng được áp khi use_tiers=TRUE.
# Spec TC-C03: "Khách hạng Vàng (hệ số 1.5)" → dùng Hạng Vàng = OFFSET 2.
# Spec TC-C04: "Khách Bạc → đạt Vàng" → từ Bạc (id=2) lên Vàng (id=3).
KHACH1_ID=$(db_exec "SELECT id FROM users WHERE email='$CUSTOMER1_EMAIL';")
KHACH4_ID=$(db_exec "SELECT id FROM users WHERE email='khach4@gmail.com';")
TIER_BAC_ID=$(db_exec   "SELECT id FROM tiers WHERE partner_id=$PARTNER_CAFE_ID ORDER BY min_points ASC OFFSET 1 LIMIT 1;")
TIER_VANG_ID=$(db_exec  "SELECT id FROM tiers WHERE partner_id=$PARTNER_CAFE_ID ORDER BY min_points ASC OFFSET 2 LIMIT 1;")
TIER_VANG_MIN=$(db_exec "SELECT min_points FROM tiers WHERE id=$TIER_VANG_ID;")

# ---------- TC-C03: Tích điểm có áp dụng hệ số hạng ----------
# Khách hạng Vàng (hệ số 1.5), bill 200k @ 1% → 200k × 1% × 1.5 = 3000 điểm.
db_exec "UPDATE tiers SET earn_multiplier=1.50 WHERE id=$TIER_VANG_ID;" >/dev/null
db_exec "UPDATE point_rules SET earn_percent=1.00, use_tiers=TRUE WHERE partner_id=$PARTNER_CAFE_ID AND is_active=TRUE;" >/dev/null
db_exec "UPDATE memberships SET lifetime_earned=$TIER_VANG_MIN, current_tier_id=$TIER_VANG_ID WHERE user_id=$KHACH1_ID AND partner_id=$PARTNER_CAFE_ID;" >/dev/null
KHACH1_PHONE=$(db_exec "SELECT phone FROM users WHERE id=$KHACH1_ID;")
RESP=$(http POST /partner/transactions "{\"phone\":\"$KHACH1_PHONE\",\"gross_amount\":200000}" "$OWNER_CAFE_TOKEN" "$PARTNER_CAFE_ID")
BODY=$(echo "$RESP" | tail -n +2)
POINTS=$(echo "$BODY" | jq -r '.transaction.points_earned')
if [ "$POINTS" = "3000" ]; then
    log "${COLOR_GREEN}✅ TC-C03${COLOR_RESET}  Bill 200k @ 1% × Vàng 1.5 = $POINTS điểm"
    PASS=$((PASS+1))
else
    log "${COLOR_RED}❌ TC-C03${COLOR_RESET}  Expected 3000, got $POINTS"
    FAIL=$((FAIL+1))
fi

# ---------- TC-C04: Vượt ngưỡng nâng hạng (Bạc → Vàng) ----------
# Spec: "Khách đang ở hạng Bạc, sau giao dịch đạt ngưỡng hạng Vàng → tự nâng hạng".
# Bạc multiplier mặc định = 1.25 (verified seed). 200k @ 1% × 1.25 = 2500 điểm.
# Setup: lifetime = (Vàng_min - 500) → cộng 2500 → Vàng_min + 2000 > Vàng_min → upgrade.
LIFETIME_BEFORE=$((TIER_VANG_MIN - 500))
db_exec "UPDATE memberships SET lifetime_earned=$LIFETIME_BEFORE, current_tier_id=$TIER_BAC_ID WHERE user_id=$KHACH4_ID AND partner_id=$PARTNER_CAFE_ID;" >/dev/null
# Verify khach4 có membership tại Cafe (nếu chưa có thì insert)
HAS_MEM=$(db_exec "SELECT 1 FROM memberships WHERE user_id=$KHACH4_ID AND partner_id=$PARTNER_CAFE_ID;")
if [ -z "$HAS_MEM" ]; then
    db_exec "INSERT INTO memberships (partner_id, user_id, lifetime_earned, current_tier_id, joined_at, created_at, updated_at) VALUES ($PARTNER_CAFE_ID, $KHACH4_ID, $LIFETIME_BEFORE, $TIER_BAC_ID, NOW(), NOW(), NOW());" >/dev/null
fi
KHACH4_PHONE=$(db_exec "SELECT phone FROM users WHERE id=$KHACH4_ID;")
RESP=$(http POST /partner/transactions "{\"phone\":\"$KHACH4_PHONE\",\"gross_amount\":200000}" "$OWNER_CAFE_TOKEN" "$PARTNER_CAFE_ID")
BODY=$(echo "$RESP" | tail -n +2)
UPGRADED=$(echo "$BODY" | jq -r '.tier_upgraded')
NEW_TIER=$(echo "$BODY" | jq -r '.new_tier_name // empty')
NEW_LIFETIME=$(echo "$BODY" | jq -r '.new_lifetime_earned // 0')
if [ "$UPGRADED" = "true" ] && [ -n "$NEW_TIER" ]; then
    log "${COLOR_GREEN}✅ TC-C04${COLOR_RESET}  tier_upgraded=true, new_tier='$NEW_TIER', lifetime=$NEW_LIFETIME (vượt ngưỡng Vàng=$TIER_VANG_MIN)"
    PASS=$((PASS+1))
else
    log "${COLOR_RED}❌ TC-C04${COLOR_RESET}  tier_upgraded=$UPGRADED, lifetime=$NEW_LIFETIME (expected upgrade từ Bạc lên Vàng=$TIER_VANG_MIN)"
    FAIL=$((FAIL+1))
fi
# Cleanup: tắt use_tiers (để các test sau không bị ảnh hưởng)
db_exec "UPDATE point_rules SET use_tiers=FALSE WHERE partner_id=$PARTNER_CAFE_ID;" >/dev/null

# Refresh CUSTOMER1_TOKEN trước các TC dùng token customer
# (rate limit bypass + tránh stale token sau setup steps)
CUSTOMER1_TOKEN=$(login "$CUSTOMER1_EMAIL" "$CUSTOMER_PWD")
if [ -z "$CUSTOMER1_TOKEN" ]; then
    log "${COLOR_RED}LOGIN FAIL cho $CUSTOMER1_EMAIL — abort customer-side TCs${COLOR_RESET}"
    summary; exit 1
fi
log "    Re-logged in $CUSTOMER1_EMAIL (token len=${#CUSTOMER1_TOKEN})"

# ---------- TC-C05: Đổi quà thành công ----------
# Tạo reward dedicated 100 điểm để khach1 chắc chắn đủ
RESP=$(http POST /partner/rewards \
    "{\"name\":\"E2E C05 redeem $(date +%s)\",\"points_cost\":100,\"stock\":5,\"offer_type\":\"ITEM_GIFT\",\"offer_label\":\"Đổi 100 điểm\"}" \
    "$OWNER_CAFE_TOKEN" "$PARTNER_CAFE_ID")
C05_REWARD_ID=$(echo "$RESP" | tail -n +2 | jq -r '.id')
if [ -n "$C05_REWARD_ID" ]; then
    RESP=$(http POST /users/me/redemptions "{\"reward_id\":$C05_REWARD_ID}" "$CUSTOMER1_TOKEN")
    STATUS=$(echo "$RESP" | head -1); BODY=$(echo "$RESP" | tail -n +2)
    assert_status "TC-C05" "Đổi reward 100 điểm → 201" "201" "$STATUS" "$BODY"
    CODE=$(echo "$BODY" | jq -r '.redemption_code // empty')
    [ "${#CODE}" = "8" ] && { log "${COLOR_GREEN}✅ TC-C05b${COLOR_RESET}  Mã 8 ký tự: $CODE"; PASS=$((PASS+1)); } \
        || { log "${COLOR_RED}❌ TC-C05b${COLOR_RESET}  Mã không 8 ký tự: '$CODE'"; FAIL=$((FAIL+1)); }
    SAVED_REDEMPTION_CODE="$CODE"
fi

# ---------- TC-C06: Đổi quà khi không đủ điểm ----------
# Lấy reward đắt nhất, dùng customer khác có ít điểm
CUST5_TOKEN=$(login "khach5@gmail.com" "$CUSTOMER_PWD")
if [ -n "$CUST5_TOKEN" ]; then
    RESP=$(http GET /users/me/rewards "" "$CUST5_TOKEN")
    BODY=$(echo "$RESP" | tail -n +2)
    EXPENSIVE_ID=$(echo "$BODY" | jq -r '[.[] | select(.can_redeem == false and .points_cost > 0)][0].id // empty')
    if [ -n "$EXPENSIVE_ID" ]; then
        RESP=$(http POST /users/me/redemptions "{\"reward_id\":$EXPENSIVE_ID}" "$CUST5_TOKEN")
        STATUS=$(echo "$RESP" | head -1)
        assert_status "TC-C06" "Không đủ điểm → 409" "409" "$STATUS"
    fi
fi

# ---------- TC-C07: Đổi quà khi hết tồn kho ----------
# Tạo reward riêng cho test này (stock=0 ngay từ đầu, points_cost=10 cho khach1 đủ điểm)
RESP=$(http POST /partner/rewards \
    "{\"name\":\"E2E C07 OutOfStock $(date +%s)\",\"points_cost\":10,\"stock\":0,\"offer_type\":\"ITEM_GIFT\",\"offer_label\":\"Hết hàng\"}" \
    "$OWNER_CAFE_TOKEN" "$PARTNER_CAFE_ID")
C07_REWARD_ID=$(echo "$RESP" | tail -n +2 | jq -r '.id')
if [ -n "$C07_REWARD_ID" ]; then
    RESP=$(http POST /users/me/redemptions "{\"reward_id\":$C07_REWARD_ID}" "$CUSTOMER1_TOKEN")
    STATUS=$(echo "$RESP" | head -1)
    assert_status "TC-C07" "stock=0 → 409 out_of_stock" "409" "$STATUS"
fi

# ---------- TC-C08: Đổi quà ngoài thời gian hiệu lực ----------
RESP=$(http POST /partner/rewards \
    "{\"name\":\"E2E C08 Expired $(date +%s)\",\"points_cost\":10,\"stock\":5,\"offer_type\":\"ITEM_GIFT\",\"offer_label\":\"Quá hạn\"}" \
    "$OWNER_CAFE_TOKEN" "$PARTNER_CAFE_ID")
C08_REWARD_ID=$(echo "$RESP" | tail -n +2 | jq -r '.id')
if [ -n "$C08_REWARD_ID" ]; then
    db_exec "UPDATE rewards SET valid_until = CURRENT_DATE - 1 WHERE id=$C08_REWARD_ID;" >/dev/null
    RESP=$(http POST /users/me/redemptions "{\"reward_id\":$C08_REWARD_ID}" "$CUSTOMER1_TOKEN")
    STATUS=$(echo "$RESP" | head -1)
    assert_status "TC-C08" "valid_until quá khứ → 404 not_found_or_expired" "404" "$STATUS"
fi

# ---------- TC-C09: Sử dụng voucher hợp lệ tại quầy ----------
if [ -n "${SAVED_REDEMPTION_CODE:-}" ]; then
    # Inspect trước
    RESP=$(http GET "/partner/redemptions/inspect/$SAVED_REDEMPTION_CODE" "" "$OWNER_CAFE_TOKEN" "$PARTNER_CAFE_ID")
    STATUS=$(echo "$RESP" | head -1); BODY=$(echo "$RESP" | tail -n +2)
    assert_status "TC-C09a" "Inspect voucher → 200" "200" "$STATUS"
    OFFER_TYPE=$(echo "$BODY" | jq -r '.reward.offer_type // empty')

    # Use voucher
    USE_BODY="{\"code\":\"$SAVED_REDEMPTION_CODE\""
    [ "$OFFER_TYPE" != "ITEM_GIFT" ] && USE_BODY="$USE_BODY,\"original_amount\":200000"
    USE_BODY="$USE_BODY}"
    RESP=$(http POST /partner/redemptions/use "$USE_BODY" "$OWNER_CAFE_TOKEN" "$PARTNER_CAFE_ID")
    STATUS=$(echo "$RESP" | head -1); BODY=$(echo "$RESP" | tail -n +2)
    assert_status "TC-C09" "Use voucher → 200" "200" "$STATUS" "$BODY"
    USED_AT=$(echo "$BODY" | jq -r '.used_at // empty')
    [ -n "$USED_AT" ] && { log "${COLOR_GREEN}✅ TC-C09b${COLOR_RESET}  used_at = $USED_AT"; PASS=$((PASS+1)); }
fi

# ---------- TC-C10: Voucher đã quá hạn ----------
# Tạo reward riêng + redeem + force expires_at past + use → 404
RESP=$(http POST /partner/rewards \
    "{\"name\":\"E2E C10 Voucher $(date +%s)\",\"points_cost\":10,\"stock\":5,\"offer_type\":\"ITEM_GIFT\",\"offer_label\":\"Voucher hết hạn\"}" \
    "$OWNER_CAFE_TOKEN" "$PARTNER_CAFE_ID")
C10_REWARD_ID=$(echo "$RESP" | tail -n +2 | jq -r '.id')
if [ -n "$C10_REWARD_ID" ]; then
    RESP=$(http POST /users/me/redemptions "{\"reward_id\":$C10_REWARD_ID}" "$CUSTOMER1_TOKEN")
    C10_CODE=$(echo "$RESP" | tail -n +2 | jq -r '.redemption_code')
    if [ -n "$C10_CODE" ]; then
        db_exec "UPDATE redemptions SET expires_at = NOW() - INTERVAL '1 day' WHERE redemption_code='$C10_CODE';" >/dev/null
        RESP=$(http POST /partner/redemptions/use "{\"code\":\"$C10_CODE\",\"original_amount\":100000}" "$OWNER_CAFE_TOKEN" "$PARTNER_CAFE_ID")
        STATUS=$(echo "$RESP" | head -1)
        assert_status "TC-C10" "Voucher expires_at quá khứ → 404" "404" "$STATUS"
    fi
fi

# ---------- TC-C11: Sử dụng voucher đã dùng trước đó ----------
if [ -n "${SAVED_REDEMPTION_CODE:-}" ]; then
    RESP=$(http POST /partner/redemptions/use \
        "{\"code\":\"$SAVED_REDEMPTION_CODE\",\"original_amount\":100000}" \
        "$OWNER_CAFE_TOKEN" "$PARTNER_CAFE_ID")
    STATUS=$(echo "$RESP" | head -1)
    assert_status "TC-C11" "Voucher đã dùng → 404" "404" "$STATUS"
fi

# ---------- TC-C12: Sử dụng voucher giảm phần trăm ----------
RESP=$(http POST /partner/rewards \
    "{\"name\":\"E2E C12 Pct20 $(date +%s)\",\"points_cost\":10,\"stock\":5,\"offer_type\":\"PERCENT_DISCOUNT\",\"offer_value\":20,\"offer_label\":\"Giảm 20%\"}" \
    "$OWNER_CAFE_TOKEN" "$PARTNER_CAFE_ID")
C12_REWARD_ID=$(echo "$RESP" | tail -n +2 | jq -r '.id')
if [ -n "$C12_REWARD_ID" ]; then
    RESP=$(http POST /users/me/redemptions "{\"reward_id\":$C12_REWARD_ID}" "$CUSTOMER1_TOKEN")
    C12_CODE=$(echo "$RESP" | tail -n +2 | jq -r '.redemption_code')
    if [ -n "$C12_CODE" ]; then
        RESP=$(http POST /partner/redemptions/use "{\"code\":\"$C12_CODE\",\"original_amount\":200000}" "$OWNER_CAFE_TOKEN" "$PARTNER_CAFE_ID")
        STATUS=$(echo "$RESP" | head -1); BODY=$(echo "$RESP" | tail -n +2)
        assert_status "TC-C12" "Use voucher 20% → 200" "200" "$STATUS"
        DISCOUNT=$(echo "$BODY" | jq -r '.discount_amount')
        if [ "$DISCOUNT" = "40000" ]; then
            log "${COLOR_GREEN}✅ TC-C12b${COLOR_RESET}  discount_amount = 40000 (200k × 20%)"
            PASS=$((PASS+1))
        else
            log "${COLOR_RED}❌ TC-C12b${COLOR_RESET}  discount_amount=$DISCOUNT (expected 40000)"
            FAIL=$((FAIL+1))
        fi
    fi
fi

# ---------- TC-C13: Sử dụng voucher đối tác khác ----------
if [ -n "${SAVED_REDEMPTION_CODE:-}" ] && [ -n "$PARTNER_LALA_ID" ]; then
    # Voucher của Cafe nhưng quét tại Lala
    RESP=$(http GET "/partner/redemptions/inspect/$SAVED_REDEMPTION_CODE" "" "$OWNER_LALA_TOKEN" "$PARTNER_LALA_ID")
    STATUS=$(echo "$RESP" | head -1)
    assert_status "TC-C13" "Voucher Cafe quét tại Lala → 404" "404" "$STATUS"
fi

# ---------- TC-C13b: Voucher với QR khách khác (NEW) ----------
# Tạo reward dedicated 10 điểm để chắc chắn khach1 có đủ điểm đổi
RESP=$(http POST /partner/rewards \
    "{\"name\":\"E2E C13b cheap $(date +%s)\",\"points_cost\":10,\"stock\":5,\"offer_type\":\"ITEM_GIFT\",\"offer_label\":\"Test khách khác\"}" \
    "$OWNER_CAFE_TOKEN" "$PARTNER_CAFE_ID")
C13B_REWARD_ID=$(echo "$RESP" | tail -n +2 | jq -r '.id')
if [ -n "$C13B_REWARD_ID" ]; then
    RESP=$(http POST /users/me/redemptions "{\"reward_id\":$C13B_REWARD_ID}" "$CUSTOMER1_TOKEN")
    C13B_CODE=$(echo "$RESP" | tail -n +2 | jq -r '.redemption_code // empty')
    if [ -n "$C13B_CODE" ]; then
        # Lấy user_id của khach2
        CUST2_TOKEN=$(login "$CUSTOMER2_EMAIL" "$CUSTOMER_PWD")
        CUST2_ID=$(curl -s "$BASE_URL/auth/me" -H "Authorization: Bearer $CUST2_TOKEN" -H "X-Forwarded-For: $(random_ip)" | jq -r '.id // 0')
        RESP=$(http POST /partner/redemptions/use \
            "{\"code\":\"$C13B_CODE\",\"original_amount\":100000,\"expected_user_id\":$CUST2_ID}" \
            "$OWNER_CAFE_TOKEN" "$PARTNER_CAFE_ID")
        STATUS=$(echo "$RESP" | head -1); BODY=$(echo "$RESP" | tail -n +2)
        assert_status "TC-C13b" "Voucher khach1 + expected khach2 → 409 customer_mismatch" "409" "$STATUS" "$BODY"
    fi
fi

# ---------- TC-C14: Phát hành voucher miễn phí ----------
# Owner Cafe tạo reward mới với points_cost=0, stock=100
FREE_REWARD_BODY=$(cat <<EOF
{
  "name": "Free Voucher E2E $(date +%s)",
  "points_cost": 0,
  "stock": 100,
  "offer_type": "ITEM_GIFT",
  "offer_label": "1 cafe miễn phí"
}
EOF
)
RESP=$(http POST /partner/rewards "$FREE_REWARD_BODY" "$OWNER_CAFE_TOKEN" "$PARTNER_CAFE_ID")
STATUS=$(echo "$RESP" | head -1); BODY=$(echo "$RESP" | tail -n +2)
assert_status "TC-C14" "Tạo free voucher 100 stock → 201" "201" "$STATUS" "$BODY"
FREE_REWARD_ID=$(echo "$BODY" | jq -r '.id // empty')

# ---------- TC-C15: Khách nhận voucher miễn phí lần 2 ----------
if [ -n "$FREE_REWARD_ID" ]; then
    # Lần 1: claim
    RESP=$(http POST "/users/me/rewards/$FREE_REWARD_ID/claim" "" "$CUSTOMER1_TOKEN")
    STATUS=$(echo "$RESP" | head -1)
    assert_status "TC-C14b" "Khach1 claim free voucher lần 1 → 201" "201" "$STATUS"
    # Lần 2: claim → expected 409 already claimed
    RESP=$(http POST "/users/me/rewards/$FREE_REWARD_ID/claim" "" "$CUSTOMER1_TOKEN")
    STATUS=$(echo "$RESP" | head -1)
    assert_status "TC-C15" "Claim lần 2 → 409 already claimed" "409" "$STATUS"
fi

# ---------- TC-C16: Đổi voucher đổi điểm nhiều lần ----------
# Tạo reward 10 điểm, stock=5, đổi 2 lần liên tiếp — cả 2 phải 201
RESP=$(http POST /partner/rewards \
    "{\"name\":\"E2E C16 multi-redeem $(date +%s)\",\"points_cost\":10,\"stock\":5,\"offer_type\":\"ITEM_GIFT\",\"offer_label\":\"Đổi nhiều lần\"}" \
    "$OWNER_CAFE_TOKEN" "$PARTNER_CAFE_ID")
C16_REWARD_ID=$(echo "$RESP" | tail -n +2 | jq -r '.id')
if [ -n "$C16_REWARD_ID" ]; then
    RESP=$(http POST /users/me/redemptions "{\"reward_id\":$C16_REWARD_ID}" "$CUSTOMER1_TOKEN")
    STATUS1=$(echo "$RESP" | head -1)
    RESP=$(http POST /users/me/redemptions "{\"reward_id\":$C16_REWARD_ID}" "$CUSTOMER1_TOKEN")
    STATUS2=$(echo "$RESP" | head -1)
    if [ "$STATUS1" = "201" ] && [ "$STATUS2" = "201" ]; then
        log "${COLOR_GREEN}✅ TC-C16${COLOR_RESET}  Đổi paid reward 2 lần đều thành công ($STATUS1 + $STATUS2)"
        PASS=$((PASS+1))
    else
        log "${COLOR_RED}❌ TC-C16${COLOR_RESET}  status lần 1=$STATUS1, lần 2=$STATUS2 (expected 201+201)"
        FAIL=$((FAIL+1))
    fi
fi

[ "${BASH_SOURCE[0]}" = "${0}" ] && summary
