"""Exercise the matching SD8777 driver and scan on the current Android boot."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("--android-scan", action="store_true")
options = parser.parse_args()

project = Path(__file__).resolve().parents[1]
source = project / "evidence/stock-radio-reference/rebuilt"
manifest = json.loads((source / "manifest.json").read_text())
adb = [str(Path(os.environ["LOCALAPPDATA"]) / "Android/Sdk/platform-tools/adb.exe"),
       "-s", "T110_ADB_SERIAL"]
remote = "/data/local/tmp/t110-sd8777-probe"


def shell(command, timeout=30):
    return subprocess.check_output(adb + ["shell", command], timeout=timeout, text=True).strip()


assert shell("cat /sys/block/mmcblk0/device/cid") == "1101003030384745T110_ADB_SERIAL"
assert shell("uname -r") == "3.4.5"
assert shell("test ! -e " + remote + " && test ! -L " + remote + " && echo absent") == "absent"
boot = shell("cat /proc/sys/kernel/random/boot_id")
if options.android_scan:
    assert shell("settings get global wifi_scan_always_enabled") == "0"
    assert "Wi-Fi is disabled" in shell("dumpsys wifi | grep -m1 'Wi-Fi is'")
shell(f"mkdir -p {remote}/odm/firmware/mrvl")
for name in ("load-radio", "mlan.ko", "sd8xxx.ko", "sd8777_uapsta.bin", "cal_data.conf"):
    file = source / name
    digest = hashlib.sha256(file.read_bytes()).hexdigest()
    if name != "load-radio":
        assert digest == manifest[name]["sha256"]
    target = f"{remote}/{name}" if name.endswith(".ko") or name == "load-radio" else f"{remote}/odm/firmware/mrvl/{name}"
    subprocess.run(adb + ["push", str(file), target], check=True, capture_output=True, timeout=30)
    assert shell(f"sha256sum {target}").split()[0] == digest

android_scan = """
cmd wifi set-scan-always-available enabled
sleep 5
cmd wifi start-scan
sleep 10
cmd wifi list-scan-results | awk 'NR > 1 && $1 ~ /:/ {count++} END {print "ANDROID_SCAN_BSS_COUNT=" count+0}'
""" if options.android_scan else ""
android_cleanup = "cmd wifi set-scan-always-available disabled; sleep 2" if options.android_scan else ""
command = f"""
set -eu
p={remote}
rf=/sys/class/rfkill/rfkill0
[ "$(cat "$rf/name")" = sd8xxx-wlan ]
[ "$(cat "$rf/state")" = 0 ]
[ -z "$(ls -A /odm)" ]
! grep -q ' /odm ' /proc/mounts
! grep -Eq '^(sd8xxx|mlan) ' /proc/modules
mounted=0
powered=0
cleanup() {{
    {android_cleanup}
    ip link set wlan0 down 2>/dev/null || true
    if grep -q '^sd8xxx ' /proc/modules; then rmmod sd8xxx || true; fi
    if grep -q '^mlan ' /proc/modules; then rmmod mlan || true; fi
    if [ "$powered" = 1 ]; then echo 0 > "$rf/state"; fi
    if [ "$mounted" = 1 ]; then umount /odm; fi
}}
trap cleanup EXIT
chcon u:object_r:vendor_file:s0 "$p/odm" "$p/odm/firmware" "$p/odm/firmware/mrvl"
chcon u:object_r:vendor_file:s0 "$p/odm/firmware/mrvl/"*
mount -o bind "$p/odm" /odm
mounted=1
echo 1 > "$rf/state"
powered=1
sleep 2
for d in /sys/bus/sdio/devices/*; do if [ -f "$d/modalias" ]; then cat "$d/modalias"; fi; done
chmod 0755 "$p/load-radio"
"$p/load-radio" "$p/mlan.ko" ""
"$p/load-radio" "$p/sd8xxx.ko" "drv_mode=1 sta_name=wlan cfg80211_wext=4 fw_name=mrvl/sd8777_uapsta.bin cal_data_cfg=mrvl/cal_data.conf"
sleep 2
iw dev
ip link set wlan0 up
if timeout 25 iw dev wlan0 scan > "$p/scan"; then
    awk '/^BSS / {{ count++ }} END {{ print "SCAN_BSS_COUNT=" count+0 }}' "$p/scan"
else
    echo SCAN_FAILED
fi
rm -f "$p/scan"
{android_scan}
"""
result = subprocess.run(adb + ["shell", command], capture_output=True, text=True, timeout=120)
output = source.parent
prefix = "android" if options.android_scan else "live"
(output / f"{prefix}-scan.txt").write_text(result.stdout + result.stderr)
(output / f"{prefix}-kernel.txt").write_text(shell("dmesg", 40))
cleanup = shell(f"rm -f {remote}/scan {remote}/mlan.ko {remote}/sd8xxx.ko {remote}/load-radio "
                f"{remote}/odm/firmware/mrvl/sd8777_uapsta.bin {remote}/odm/firmware/mrvl/cal_data.conf; "
                f"rmdir {remote}/odm/firmware/mrvl {remote}/odm/firmware {remote}/odm {remote}; "
                "cat /sys/class/rfkill/rfkill0/state; cat /proc/sys/kernel/random/boot_id")
assert cleanup.splitlines()[-2:] == ["0", boot]
assert shell("grep -E '^(mlan|sd8xxx) ' /proc/modules || true") == ""
if options.android_scan:
    assert shell("settings get global wifi_scan_always_enabled") == "0"
print(result.stdout + result.stderr)
raise SystemExit(result.returncode)
