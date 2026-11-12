"""Stage only the verified SD8777 driver and its stock firmware."""
from pathlib import Path
import hashlib
import json
import sys

project = Path(__file__).resolve().parents[1]
source = project / "evidence/stock-radio-reference/rebuilt"
destination = Path(sys.argv[1]) / "device/samsung/t110_bringup/wifi/assets"
manifest = json.loads((source / "manifest.json").read_text())
destination.mkdir(parents=True, exist_ok=True)
for name in ("mlan.ko", "sd8xxx.ko", "sd8777_uapsta.bin", "cal_data.conf"):
    payload = (source / name).read_bytes()
    if len(payload) != manifest[name]["bytes"] or hashlib.sha256(payload).hexdigest() != manifest[name]["sha256"]:
        raise ValueError(f"SD8777 artifact failed its integrity check: {name}")
    (destination / name).write_bytes(payload)
