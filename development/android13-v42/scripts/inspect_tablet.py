"""Collect read-only SM-T110 diagnostics through an already authorized ADB connection.

Usage: python inspect_tablet.py --adb C:/path/to/adb.exe [--serial SERIAL]
No root request, reboot, flash, partition readout, or device writes are performed.
"""
import argparse
import json
from pathlib import Path
import subprocess
from datetime import datetime, timezone

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adb", default="adb")
    parser.add_argument("--serial")
    args = parser.parse_args()
    base = [args.adb] + (["-s", args.serial] if args.serial else [])
    def run(*command):
        result = subprocess.run(base + list(command), capture_output=True, text=True, timeout=25)
        return {"exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr}
    model = run("shell", "getprop ro.product.model")
    if model["exit_code"] or model["stdout"].strip() != "SM-T110":
        raise SystemExit("Expected one authorized SM-T110. No further commands sent. " + json.dumps(model))
    commands = {
        "identity": "getprop ro.product.device; getprop ro.build.fingerprint; getprop ro.build.version.release",
        "kernel": "uname -a; cat /proc/version",
        "boot_command_line": "cat /proc/cmdline",
        "partitions": "cat /proc/partitions; ls -l /dev/block/platform/sdhci-pxav3.2/by-name",
        "mounts": "cat /proc/mounts",
        "usb": "ls /sys/class/android_usb/android0; ls /dev/usb-ffs; ls /dev/android_adb",
        "graphics": "ls -l /dev/graphics; ls -l /dev/galcore; cat /sys/class/graphics/fb0/name; cat /sys/class/graphics/fb0/virtual_size",
        "security": "getenforce; cat /proc/filesystems; ls /sys/fs/selinux; ls /sys/fs/cgroup",
    }
    result = {"model": model, "checks": {key: run("shell", command) for key, command in commands.items()}}
    folder = Path(__file__).resolve().parents[1] / "device-reports"
    folder.mkdir(exist_ok=True)
    target = folder / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + ".json")
    target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(target)

if __name__ == "__main__":
    main()
