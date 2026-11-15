"""Assemble both modernized editions locally, keeping the Google candidate private."""
from pathlib import Path
import hashlib
import io
import json
import re
import shutil
import sys
import tarfile
import zipfile

sys.path.insert(0, str(Path(__file__).parent))
from verify_modern_package import verify

SCRIPTS = Path(__file__).parent
PROJECT = SCRIPTS.parent
WORK = Path("/root/t110-lineage14-ui")
DEST = SCRIPTS / "lineage14-modern-20261115"
DEST.mkdir(exist_ok=True)
DOCS = DEST / "docs"
DOCS.mkdir(exist_ok=True)

def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()

def entry(path):
    return {"bytes": path.stat().st_size, "sha256": sha(path)}

docs = {
    "XDA-POST.md": SCRIPTS / "XDA-MODERN-POST.md",
    "RELEASE-PLAN.md": SCRIPTS / "MODERN-RELEASE-PLAN.md",
    "INSTALLATION.md": SCRIPTS / "lineage14-20261114/docs/INSTALLATION.md",
    "SOURCE-AND-CREDITS.md": SCRIPTS / "lineage14-20261114/docs/SOURCE-AND-CREDITS.md",
    "RECOVERY-PROVENANCE.md": SCRIPTS / "lineage14-20261114/docs/RECOVERY-PROVENANCE.md",
}
for name, path in docs.items():
    shutil.copyfile(path, DOCS / name)
readme = """# SM-T110 Modernized LineageOS14.1 — release preparation

Both editions contain our current modern icons, drawer gestures, Settings,
navigation and clean lock fade. Neither reverts to the original/old UI.

The edition without Google apps is the accepted installed image. The Google
edition is a separately built, offline-checked candidate, NOT boot/account/Play
qualified. Do not publish or call it tested yet.

These ROM ZIPs are computer-side transport archives, not TWRP/Odin update ZIPs.
Extract on the computer and read docs/INSTALLATION.md. The public clean-install
flow remains pending; never flash the raw image to physical SYSTEM.

The matching T110 TWRP and retained Odin3.13.1 toolkit are in third-party.
The developer-linked Odin3.07 is a separate upstream download. The toolkit is a
local preparation copy; public instructions use original download references.

The Google archive is LOCAL-PRIVATE and is not uploaded/mirrored. A public Google
installation must use the exact upstream package with a qualified local
integration flow, or separately established distribution permission.

Source branch: release/lineage14.1-modern-t110-20261115
Repository: https://github.com/Tapuz97/android_device_samsung_goyawifi
XDA draft: docs/XDA-POST.md. No XDA post or tablet flash is made by this script.

Verify either ROM archive on Windows with:
  py -3 verify_modern_package.py <archive-name.zip>
Use Python explicitly; launching .py through its file association can open VS Code.
"""
(DEST / "README.md").write_text(readme, encoding="utf-8")
shutil.copyfile(SCRIPTS / "verify_modern_package.py", DEST / "verify_modern_package.py")
inventory = []
for directory, edition, name, google in (
    (WORK / "artifacts-settings-lock-20261115", "Modernized — without Google apps",
     "SM-T110-Lineage14.1-Modernized-20261115-without-Google-apps.zip", False),
    (WORK / "artifacts-modern-google-20261115", "Modernized — with Google apps (local qualification candidate)",
     "LOCAL-PRIVATE-SM-T110-Lineage14.1-Modernized-20261115-with-Google-apps.zip", True),
):
    report_name = "google-integration-verification.json" if google else "ui-image-verification.json"
    report = json.loads((directory / report_name).read_text())
    files = {x["name"]: x for x in report["files"]}
    if google:
        assert report["native_apps_and_ui_preserved"] and report["native_files_unchanged"] >= 1800
        assert report["selinux_label_terminator_checked"]
    else:
        assert files["system.raw.img"]["sha256"] == (
            "eb9d8955ef8df81f04f424f2b3d0c4bc2d3451395ed36ca7648fd696212067f1")
    for filename in ("system.raw.img.gz", "boot.img"):
        assert sha(directory / filename) == files[filename]["sha256"]
    manifest = {
        "edition": edition, "model": "SM-T110", "codename": "goyawifi",
        "android": "7.1.2", "android_sdk": 25, "lineage": "14.1", "architecture": "arm",
        "modernized_ui": True, "google_apps": google,
        "container_format": "computer_transport_not_recovery_update",
        "system_raw_sha256": files["system.raw.img"]["sha256"],
        "physical_system_write_allowed": False,
        "files": {n: files[n] for n in ("system.raw.img.gz", "boot.img")},
        "qualification": "OFFLINE_ONLY_GOOGLE_TESTS_PENDING" if google else "INSTALLED_OWNER_CONFIRMED_MODERN_UI",
        "public_upload_allowed": not google,
    }
    target = DEST / name
    print("Packaging " + edition, flush=True)
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_STORED, allowZip64=True) as archive:
        for filename in ("system.raw.img.gz", "boot.img"):
            archive.write(directory / filename, filename)
        archive.writestr("manifest.json", json.dumps(manifest, indent=2) + "\n")
        archive.writestr("README.md", readme)
        archive.write(SCRIPTS / "verify_modern_package.py", "verify_modern_package.py")
        for filename in docs:
            archive.write(DOCS / filename, "docs/" + filename)
        archive.write(directory / report_name, "checks/" + report_name)
        if not google:
            for filename in ("native-icon-verification.json", "settings-lock-verification.json"):
                archive.write(directory / filename, "checks/" + filename)
    verify(target)
    inventory.append({"name": name, "edition": edition, **entry(target),
                      "public_upload_allowed": not google, "manifest": manifest})
    (DEST / (name + ".manifest.json")).write_text(json.dumps(manifest, indent=2) + "\n")

toolkit = SCRIPTS / "lineage14-20261114/third-party"
tool_inventory = json.loads((toolkit / "toolkit-inventory.json").read_text())
for record in tool_inventory:
    path = toolkit / record["path"]
    assert entry(path) == {"bytes": record["bytes"], "sha256": record["sha256"]}, str(path)
tool_output = DEST / "third-party"
tool_output.mkdir(exist_ok=True)
recovery = toolkit / "recovery/T110.TWRP.2.7.0.1.tar.md5"
raw = recovery.read_bytes()
footer = None
for offset in range(max(0, len(raw) - 200), len(raw) - 31):
    candidate = raw[offset:offset + 32]
    if re.fullmatch(b"[0-9a-f]{32}", candidate) and hashlib.md5(raw[:offset]).hexdigest().encode() == candidate:
        footer = offset
        break
assert footer is not None, "Odin tar.md5 footer mismatch"
with tarfile.open(fileobj=io.BytesIO(raw[:footer])) as archive:
    members = archive.getmembers()
    assert len(members) == 1 and members[0].name == "recovery.img"
    image = archive.extractfile(members[0]).read()
assert hashlib.sha256(image.ljust(16777216, b"\0")).hexdigest() == (
    "f7f0bcf8a0cee4ecf265a2e1d75de028e97e9401c640e8cbc29d4b256d39452e")
shutil.copyfile(recovery, tool_output / recovery.name)
odin_zip = tool_output / "LOCAL-TOOLKIT-Odin3.13.1-and-Samsung-driver.zip"
with zipfile.ZipFile(odin_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
    for record in tool_inventory:
        if record["path"].startswith("recovery/Odin3 v3.13.1/"):
            archive.write(toolkit / record["path"], record["path"].removeprefix("recovery/"))
with zipfile.ZipFile(odin_zip) as archive:
    assert archive.testzip() is None
    assert not any("diagnostic" in n.lower() for n in archive.namelist())
receipt = {"status": "PASS_MATCHED_T110_RECOVERY_AND_RETAINED_ODIN_FILES",
           "recovery_tar": entry(tool_output / recovery.name),
           "recovery_image_bytes": len(image), "md5_footer_verified": True,
           "installed_recovery_padding_match": True,
           "odin_toolkit": entry(odin_zip), "toolkit_files_verified": len(tool_inventory),
           "public_third_party_downloads": "Use original upstream references in docs/XDA-POST.md"}
(tool_output / "verification.json").write_text(json.dumps(receipt, indent=2) + "\n")
(DEST / "ASSETS.json").write_text(json.dumps({"roms": inventory, "toolkit": receipt}, indent=2) + "\n")
(DEST / "SHA256SUMS.txt").write_text("".join(
    x["sha256"] + "  " + x["name"] + "\n" for x in inventory) +
    receipt["recovery_tar"]["sha256"] + "  third-party/" + recovery.name + "\n" +
    receipt["odin_toolkit"]["sha256"] + "  third-party/" + odin_zip.name + "\n")
print("Both modernized editions and matching recovery/Odin material prepared locally.", flush=True)
