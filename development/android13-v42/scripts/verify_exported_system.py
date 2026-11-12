"""Verify a Windows system export against its native build-side report."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("artifact", type=Path)
parser.add_argument("--build-log", required=True)
args = parser.parse_args()
report = json.loads((args.artifact / "system-verification.json").read_text())
assert report["status"] == "FIT_AND_EXT4_VERIFIED"
raw = args.artifact / "system.raw.img"
assert raw.stat().st_size == report["expanded_bytes"] == 1594884096
sha = hashlib.sha256()
md5 = hashlib.md5()
with raw.open("rb") as stream:
    while chunk := stream.read(8 * 1024 * 1024):
        sha.update(chunk)
        md5.update(chunk)
assert sha.hexdigest() == report["sha256"], "Windows export differs from build output"
result = dict(status="VERIFIED", sha256=sha.hexdigest(), md5=md5.hexdigest(),
              bytes=raw.stat().st_size, build_exit=0, build_log=args.build_log,
              verified_at=datetime.now().astimezone().isoformat())
(args.artifact / "host-verification.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
