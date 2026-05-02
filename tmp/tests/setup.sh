#!/usr/bin/env bash
# Helper functions + env vars cho test scripts.
# Source file này trong mỗi script: `source "$(dirname "$0")/../setup.sh"`

set -uo pipefail  # fail-fast on undefined vars + pipe failures, NOT on cmd error

BASE_URL="${BASE_URL:-http://localhost:3199/api}"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
RESULTS_DIR="$(cd "$(dirname "$0")/.." 2>/dev/null && pwd)/results"
[ -d "$RESULTS_DIR" ] || mkdir -p "$RESULTS_DIR"
LOG_FILE="${LOG_FILE:-$RESULTS_DIR/run-$TIMESTAMP.log}"

PASS=0
FAIL=0

# ---------- color output ----------
COLOR_GREEN='\033[0;32m'
COLOR_RED='\033[0;31m'
COLOR_YELLOW='\033[1;33m'
COLOR_BOLD='\033[1m'
COLOR_RESET='\033[0m'

log() { echo -e "$1" | tee -a "$LOG_FILE"; }

# ---------- assertion helpers ----------

# assert_status TC_ID DESCRIPTION EXPECTED_STATUS ACTUAL_STATUS [BODY]
assert_status() {
    local tc_id="$1"
    local desc="$2"
    local expected="$3"
    local actual="$4"
    local body="${5:-}"
    if [ "$expected" = "$actual" ]; then
        log "${COLOR_GREEN}✅ $tc_id${COLOR_RESET}  $desc — got $actual"
        PASS=$((PASS+1))
    else
        log "${COLOR_RED}❌ $tc_id${COLOR_RESET}  $desc — expected $expected, got $actual"
        [ -n "$body" ] && log "    body: $(echo "$body" | head -c 300)"
        FAIL=$((FAIL+1))
    fi
}

# assert_contains TC_ID DESCRIPTION HAYSTACK NEEDLE
assert_contains() {
    local tc_id="$1"
    local desc="$2"
    local haystack="$3"
    local needle="$4"
    if echo "$haystack" | grep -q "$needle"; then
        log "${COLOR_GREEN}✅ $tc_id${COLOR_RESET}  $desc — found '$needle'"
        PASS=$((PASS+1))
    else
        log "${COLOR_RED}❌ $tc_id${COLOR_RESET}  $desc — '$needle' not in response"
        log "    body: $(echo "$haystack" | head -c 300)"
        FAIL=$((FAIL+1))
    fi
}

# ---------- JSON parser (jq nếu có, fallback python3) ----------
if command -v jq >/dev/null 2>&1; then
    json_get() { echo "$1" | jq -r "${2}"; }
else
    json_get() {
        python3 -c "
import json, sys
data = json.loads(sys.stdin.read() or 'null')
expr = '''${2}'''
# Hỗ trợ cú pháp đơn giản: .access_token, .[0].id, .items[0].reason
def walk(d, path):
    if not path or path == '.':
        return d
    parts = path.lstrip('.').split('.')
    for p in parts:
        if d is None: return None
        if '[' in p:
            key, idx = p.split('[', 1)
            idx = int(idx.rstrip(']'))
            if key: d = d.get(key) if isinstance(d, dict) else None
            d = d[idx] if d and idx < len(d) else None
        else:
            d = d.get(p) if isinstance(d, dict) else None
    return d
try:
    v = walk(data, expr)
    print('' if v is None else (str(v).lower() if isinstance(v, bool) else str(v)))
except Exception:
    print('')
" <<< "$1"
    }
fi

# ---------- HTTP helpers ----------

# Random X-Forwarded-For mỗi request → bypass rate limit per-IP của slowapi
# (backend key rate limit theo X-Forwarded-For trong limiter._get_real_ip)
random_ip() {
    echo "10.$((RANDOM % 256)).$((RANDOM % 256)).$((RANDOM % 256))"
}

# http METHOD PATH [BODY] [TOKEN] [PARTNER_ID]
# Returns "STATUS\nBODY" via stdout
http() {
    local method="$1"
    local path="$2"
    local body="${3:-}"
    local token="${4:-}"
    local partner_id="${5:-}"

    local url="$BASE_URL$path"
    local args=(-s -o /tmp/_resp.json -w "%{http_code}")
    args+=(-X "$method")
    args+=(-H "Content-Type: application/json")
    args+=(-H "X-Forwarded-For: $(random_ip)")
    [ -n "$token" ] && args+=(-H "Authorization: Bearer $token")
    [ -n "$partner_id" ] && args+=(-H "X-Partner-Id: $partner_id")
    [ -n "$body" ] && args+=(-d "$body")

    local status
    status=$(curl "${args[@]}" "$url")
    local resp
    resp=$(cat /tmp/_resp.json 2>/dev/null || echo "")
    echo "$status"
    echo "$resp"
}

# login EMAIL PASSWORD → echo TOKEN (or empty if fail)
login() {
    local email="$1"
    local password="$2"
    local body
    body=$(cat <<EOF
{"identifier":"$email","password":"$password"}
EOF
    )
    local resp
    resp=$(curl -s -X POST "$BASE_URL/auth/login" \
        -H "Content-Type: application/json" \
        -H "X-Forwarded-For: $(random_ip)" \
        -d "$body")
    echo "$resp" | jq -r '.access_token // empty'
}

# Resolve partner_id from owner email (đăng nhập owner → /users/me/partners-as-staff → first id)
resolve_partner_id() {
    local owner_token="$1"
    curl -s "$BASE_URL/users/me/partners-as-staff" \
        -H "Authorization: Bearer $owner_token" \
        -H "X-Forwarded-For: $(random_ip)" | jq -r '.[0].id // empty'
}

# ---------- summary ----------
summary() {
    log ""
    log "${COLOR_BOLD}═══════════════════════════════════════${COLOR_RESET}"
    log "${COLOR_BOLD}Tổng kết: $PASS Đạt | $FAIL Không đạt${COLOR_RESET}"
    log "Log đầy đủ: $LOG_FILE"
    log "${COLOR_BOLD}═══════════════════════════════════════${COLOR_RESET}"
    [ "$FAIL" -eq 0 ] || exit 1
}

# ---------- DB + container helpers (full automation) ----------
PG_CONTAINER="${PG_CONTAINER:-loyalty-postgres-prod}"
BE_CONTAINER="${BE_CONTAINER:-loyalty-backend-prod}"

# db_exec "SQL" → trả output (tab-separated, no header) qua stdout
db_exec() {
    docker exec "$PG_CONTAINER" psql -U loyalty -d loyalty -tAc "$1" 2>/dev/null | tr -d '\r'
}

# bcrypt_hash "plain_password" → in ra hash
bcrypt_hash() {
    docker exec "$BE_CONTAINER" python -c "from app.core.security import hash_password; print(hash_password('$1'))" 2>/dev/null | tr -d '\r'
}

# set_temp_password EMAIL PLAIN_PWD [SKIP_FLAG]
# Cập nhật password + must_change_password=TRUE (trừ khi SKIP_FLAG=true)
set_temp_password() {
    local email="$1"
    local pwd="$2"
    local skip_flag="${3:-false}"
    local hash
    hash=$(bcrypt_hash "$pwd")
    if [ -z "$hash" ]; then
        log "${COLOR_RED}set_temp_password: bcrypt_hash trả empty${COLOR_RESET}"
        return 1
    fi
    if [ "$skip_flag" = "true" ]; then
        db_exec "UPDATE users SET password_hash='$hash' WHERE email='$email';" >/dev/null
    else
        db_exec "UPDATE users SET password_hash='$hash', must_change_password=TRUE WHERE email='$email';" >/dev/null
    fi
}

# restore_user_password EMAIL PLAIN_PWD — set lại pwd + clear must_change_password
restore_user_password() {
    set_temp_password "$1" "$2" "true"
    db_exec "UPDATE users SET must_change_password=FALSE WHERE email='$1';" >/dev/null
}

# ---------- demo creds ----------
ADMIN_EMAIL="admin@loyalty.vn"
ADMIN_PWD="admin1234"
OWNER_CAFE_EMAIL="owner@cafe.vn"
OWNER_CAFE_PWD="owner1234"
OWNER_LALA_EMAIL="owner@lala.vn"
OWNER_LALA_PWD="owner1234"
CUSTOMER1_EMAIL="khach1@gmail.com"
CUSTOMER2_EMAIL="khach2@gmail.com"
CUSTOMER_PWD="khach1234"

log "${COLOR_BOLD}═══════════════════════════════════════${COLOR_RESET}"
log "${COLOR_BOLD}Test run: $TIMESTAMP${COLOR_RESET}"
log "${COLOR_BOLD}BASE_URL: $BASE_URL${COLOR_RESET}"
log "${COLOR_BOLD}═══════════════════════════════════════${COLOR_RESET}"
