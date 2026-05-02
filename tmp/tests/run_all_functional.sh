#!/usr/bin/env bash
# Chạy toàn bộ 4 nhóm kịch bản chức năng tuần tự.
set -uo pipefail
cd "$(dirname "$0")"

export LOG_FILE="${LOG_FILE:-results/run-all-$(date +%Y%m%d-%H%M%S).log}"

bash scenarios/group_a_auth.sh
bash scenarios/group_b_partner.sh
bash scenarios/group_c_pos.sh
bash scenarios/group_d_admin.sh

echo ""
echo "Tổng hợp các log riêng lẻ ở results/. Mỗi script đã in summary cuối."
echo "Kiểm tra bằng: grep -c ✅ results/*.log; grep -c ❌ results/*.log"
