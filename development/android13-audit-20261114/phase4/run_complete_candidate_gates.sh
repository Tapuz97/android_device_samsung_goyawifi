#!/usr/bin/env bash
# Offline only: never invokes adb, a flash tool, or a tablet reboot.
set -eo pipefail
tools='/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110/android13-audit'
log="${1:-/root/t110-android13/logs/complete-image-4.log}"
grep -q T110_COMPLETE_SYSTEMIMAGE_BUILD_PASS "$log"
printf '\nRUNNING verify_complete_image.py\n'
python3 "$tools/verify_complete_image.py" "$log"
for check in check_complete_image_policy.py run_production_namespace_checks.py package_android13_candidate_boot.py verify_preserved_roms.py backup_complete_candidate.py; do
    printf '\nRUNNING %s\n' "$check"
    python3 "$tools/$check"
done
printf '\nT110_COMPLETE_CANDIDATE_OFFLINE_GATES_PASS\n'
