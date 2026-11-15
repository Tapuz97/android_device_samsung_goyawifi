"""Fetch the exact upstream ARM/API25 input for local integration, never mirror it."""
from pathlib import Path
import hashlib
import json
import urllib.request
import zipfile

root = Path("/root/t110-lineage14-ui/google-input")
root.mkdir(exist_ok=True)
name = "open_gapps-arm-7.1-pico-20220215.zip"
base = "https://downloads.sourceforge.net/project/opengapps/arm/20220215/"
for suffix in (".md5", ""):
    target = root / (name + suffix)
    if not target.exists():
        print("Downloading upstream " + target.name, flush=True)
        with urllib.request.urlopen(base + target.name, timeout=60) as src, target.with_suffix(target.suffix + ".partial").open("wb") as dst:
            while chunk := src.read(1024 * 1024):
                dst.write(chunk)
        target.with_suffix(target.suffix + ".partial").rename(target)
    if suffix:
        print(target.read_text()[:150], flush=True)
package = root / name
expected = (root / (name + ".md5")).read_text().split()[0]
assert hashlib.md5(package.read_bytes()).hexdigest() == expected
with zipfile.ZipFile(package) as archive:
    assert archive.testzip() is None
    members = [{"name": x.filename, "bytes": x.file_size} for x in archive.infolist()]
    for member in ("installer.sh", "app_densities.txt", "gapps-remove.txt", "g.prop"):
        if member in archive.namelist():
            (root / member).write_bytes(archive.read(member))
report = {"status": "UPSTREAM_ZIP_AND_MD5_CHECKED_NOT_INSTALLED",
          "upstream": base + name, "bytes": package.stat().st_size,
          "sha256": hashlib.sha256(package.read_bytes()).hexdigest(),
          "upstream_md5": expected, "members": members,
          "public_mirroring": False}
(root / "input-verification.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({k: v for k, v in report.items() if k != "members"}), flush=True)
