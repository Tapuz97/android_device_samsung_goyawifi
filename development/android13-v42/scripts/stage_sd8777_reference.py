"""Stage the rebuilt driver and firmware extracted from the verified stock image."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess

base = Path("/root/t110-build")
project = Path(__file__).resolve().parents[1]
output = project / "evidence/stock-radio-reference/rebuilt"
output.mkdir(exist_ok=True)
source = base / "kernel-display-i2c/drivers/marvell/sd8787/wlan_src"
for name in ("mlan.ko", "sd8xxx.ko"):
    target = output / name
    shutil.copyfile(source / name, target)
    subprocess.run([str(base / "toolchain/bin/arm-eabi-strip"), "--strip-debug", str(target)],
                   check=True)
    assert b"vermagic=3.4.5 SMP preempt mod_unload ARMv7" in target.read_bytes()

raw = base / "stock-radio-extract/system.raw"
for name, size in {"sd8777_uapsta.bin": 453612, "cal_data.conf": 294,
                   "WlanCalData_ext.conf": 370}.items():
    content = subprocess.check_output(["debugfs", "-R", f"cat /etc/firmware/mrvl/{name}", str(raw)])
    assert len(content) == size
    (output / name).write_bytes(content)
report = {}
for path in output.iterdir():
    if path.name == "manifest.json":
        continue
    report[path.name] = {"bytes": path.stat().st_size,
                         "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
(output / "manifest.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
