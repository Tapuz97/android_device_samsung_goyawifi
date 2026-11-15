"""Locally integrate upstream Google components without changing our native UI.

No tablet access. No prebuilt Google payload is published by this tool.
Requires Linux, lzip, debugfs, e2fsck and the existing checked release input.
"""
from pathlib import Path, PurePosixPath
import gzip
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import tarfile
import zipfile

ROOT = Path("/root/t110-lineage14-ui")
BASE = ROOT / "artifacts-settings-lock-20261115"
INPUT = ROOT / "google-input"
DEST = ROOT / "artifacts-modern-google-20261115"
RAW_SHA = "eb9d8955ef8df81f04f424f2b3d0c4bc2d3451395ed36ca7648fd696212067f1"
ZIP_SHA = "8c26062b0a54b6b6433e9cce11d76a6a12c13cc8fc3dcaee5875af1662a4b74b"
AAPT = ROOT / "out/host/linux-x86/bin/aapt"

def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as source:
        while data := source.read(1024 * 1024):
            h.update(data)
    return h.hexdigest()

def run(*args, **kwargs):
    result = subprocess.run(list(map(str, args)), check=True, capture_output=True, **kwargs)
    return result.stdout.decode(errors="replace")

assert sha(BASE / "system.raw.img") == RAW_SHA
package = INPUT / "open_gapps-arm-7.1-pico-20220215.zip"
assert sha(package) == ZIP_SHA
assert not DEST.exists(), "Never overwrite a previous candidate."
DEST.mkdir()
stage = DEST / "added-files"
stage.mkdir()
context_file = DEST / "system-file-context.bin"
context_file.write_bytes(b"u:object_r:system_file:s0\0")
selected = [
    "Core/defaultetc-common.tar.lz", "Core/defaultframework-common.tar.lz",
    "Core/googlebackuptransport-all.tar.lz", "Core/googlecontactssync-all.tar.lz",
    "Core/googlefeedback-all.tar.lz", "Core/googleonetimeinitializer-all.tar.lz",
    "Core/googlepartnersetup-all.tar.lz", "Core/gmscore-arm.tar.lz",
    "Core/gsfcore-all.tar.lz", "Core/vending-arm.tar.lz",
    "Core/setupwizardtablet-all.tar.lz", "Core/configupdater-all.tar.lz",
    "Core/gsflogin-all.tar.lz", "GApps/calsync-all.tar.lz",
]
origins = {}
with zipfile.ZipFile(package) as archive:
    for name in selected:
        print("Selecting " + name, flush=True)
        raw = subprocess.check_output(["lzip", "-dc"], input=archive.read(name))
        with tarfile.open(fileobj=io.BytesIO(raw), mode="r:") as tar:
            members = tar.getmembers()
            densities = {PurePosixPath(m.name).parts[1] for m in members
                         if len(PurePosixPath(m.name).parts) > 1}
            # Density200 chooses the next higher upstream resource set240.
            density = "240" if "240" in densities else "nodpi"
            for member in members:
                parts = PurePosixPath(member.name).parts
                if len(parts) < 3 or parts[1] not in ("common", density):
                    continue
                relative = PurePosixPath(*parts[2:])
                assert not relative.is_absolute() and ".." not in relative.parts
                assert relative.parts[0] in ("app", "priv-app", "framework", "etc", "lib")
                assert member.isdir() or member.isfile(), "Unexpected archive link/device"
                if member.isdir():
                    continue
                assert str(relative) not in origins, str(relative)
                target = stage / str(relative)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(tar.extractfile(member).read())
                target.chmod(0o644)
                origins[str(relative)] = name

apks = []
for path in sorted(stage.rglob("*.apk")):
    badging = run(AAPT, "dump", "badging", path)
    package_name = re.search(r"package: name='([^']+)'", badging).group(1)
    minimum = re.search(r"sdkVersion:'(\d+)'", badging)
    assert minimum and int(minimum.group(1)) <= 25, path
    with zipfile.ZipFile(path) as apk:
        abis = sorted({x.split("/")[1] for x in apk.namelist()
                       if x.startswith("lib/") and len(x.split("/")) > 2})
        assert not abis or "armeabi-v7a" in abis or "armeabi" in abis
        # Universal APKs may include additional ABIs. Android selects their ARM
        # implementation; rejecting unused ABI folders would reject valid APKs.
    apks.append({"file": str(path.relative_to(stage)), "package": package_name,
                 "minimum_sdk": int(minimum.group(1)), "abis": abis, "sha256": sha(path)})
assert len({x["package"] for x in apks}) == len(apks)
required = {"com.google.android.gms", "com.android.vending", "com.google.android.gsf",
            "com.google.android.gsf.login"}
assert required <= {x["package"] for x in apks}

# Work only on a new regular image file. Never mount or address tablet storage.
image = DEST / "system.raw.img"
shutil.copyfile(BASE / "system.raw.img", image)
baseline = BASE / "system.raw.img"
dirs = set()
labeled = set()
commands = []
for relative in sorted(origins):
    # Abort on every overwrite, including permissions/framework configuration.
    stat = run("/usr/sbin/debugfs", "-R", "stat /" + relative, baseline)
    assert "Inode:" not in stat, "Refusing to overwrite native file: " + relative
    path = PurePosixPath(relative)
    for parent in reversed(path.parents):
        if str(parent) == "." or str(parent) in dirs:
            continue
        dirs.add(str(parent))
        existing = run("/usr/sbin/debugfs", "-R", "stat /" + str(parent), baseline)
        if "Inode:" not in existing:
            labeled.add(str(parent))
            commands += ["mkdir /" + str(parent),
                         "set_inode_field /" + str(parent) + " mode 040755",
                         "ea_set -f " + str(context_file) + " /" + str(parent) + " security.selinux"]
    commands += ["write " + str(stage / relative) + " /" + relative,
                 "set_inode_field /" + relative + " mode 0100644",
                 "ea_set -f " + str(context_file) + " /" + relative + " security.selinux"]
    labeled.add(relative)
script = DEST / "debugfs-add-files.txt"
script.write_text("\n".join(commands) + "\n")
result = subprocess.run(["/usr/sbin/debugfs", "-w", "-f", str(script), str(image)],
                        capture_output=True, text=True)
(DEST / "image-write.log").write_text(result.stdout + result.stderr)
assert result.returncode == 0
assert not any(x in result.stderr for x in ("File not found", "Could not", "Ext2 inode is not"))
check = subprocess.run(["/usr/sbin/e2fsck", "-fn", str(image)], capture_output=True, text=True)
(DEST / "filesystem-check.txt").write_text(check.stdout + check.stderr)
assert check.returncode == 0
verified = []
readback = DEST / "readback"
readback.mkdir()
for relative in sorted(origins):
    target = readback / Path(relative).name
    run("/usr/sbin/debugfs", "-R", "dump /" + relative + " " + str(target), image)
    assert sha(target) == sha(stage / relative), relative
    verified.append({"file": relative, "upstream_archive": origins[relative], "sha256": sha(target)})
    target.unlink()
readback.rmdir()
context_readback = DEST / "readback-context.bin"
for relative in sorted(labeled):
    run("/usr/sbin/debugfs", "-R", "ea_get -f " + str(context_readback) +
        " /" + relative + " security.selinux", image)
    assert context_readback.read_bytes() == context_file.read_bytes(), relative
    context_readback.unlink()

# Native tree byte comparison via debugfs rdump (including app icons and drivers).
for label, source in (("base-tree", baseline), ("google-tree", image)):
    directory = DEST / label
    directory.mkdir()
    run("/usr/sbin/debugfs", "-R", "rdump / " + str(directory), source)
oldtree, newtree = DEST / "base-tree", DEST / "google-tree"
native = 0
for path in oldtree.rglob("*"):
    other = newtree / path.relative_to(oldtree)
    if path.is_symlink():
        assert other.is_symlink() and os.readlink(path) == os.readlink(other)
    elif path.is_file():
        assert other.is_file() and sha(path) == sha(other), str(path)
        native += 1
assert {str(p.relative_to(newtree)) for p in newtree.rglob("*") if p.is_file() and not p.is_symlink()} - {
    str(p.relative_to(oldtree)) for p in oldtree.rglob("*") if p.is_file() and not p.is_symlink()
} == set(origins)
base_packages = set()
for path in oldtree.rglob("*.apk"):
    # AAPT1 badging tries to resolve framework labels in Settings and can return
    # failure after printing a valid package. Read the manifest directly instead.
    base_packages.add(re.search(r'A: package="([^"]+)"',
                               run(AAPT, "dump", "xmltree", path, "AndroidManifest.xml")).group(1))
assert not base_packages & {x["package"] for x in apks}, "Duplicate Android package"
for directory in (oldtree, newtree):
    assert directory.resolve().parent == DEST.resolve()
    shutil.rmtree(directory)
shutil.copyfile(BASE / "boot.img", DEST / "boot.img")
print("Compressing separate Google-enabled candidate", flush=True)
with image.open("rb") as source, (DEST / "system.raw.img.gz").open("wb") as target:
    with gzip.GzipFile(fileobj=target, mode="wb", mtime=0, compresslevel=6) as output:
        shutil.copyfileobj(source, output)
files = [{"name": name, "bytes": (DEST / name).stat().st_size, "sha256": sha(DEST / name)}
         for name in ("system.raw.img", "system.raw.img.gz", "boot.img")]
report = {"status": "OFFLINE_CHECKED_GOOGLE_CANDIDATE_NOT_BOOT_TESTED",
          "base_system_sha256": RAW_SHA, "upstream_zip_sha256": ZIP_SHA,
          "native_files_unchanged": native, "native_apps_and_ui_preserved": True,
          "selinux_labels_checked": len(labeled),
          "selinux_label_terminator_checked": True,
          "google_payload_public_upload_allowed": False,
          "excluded": ["Google launcher", "Google WebView", "GoogleExtServices",
                       "GoogleExtShared", "Google TTS", "Google keyboard"],
          "packages": apks, "added_files": verified, "files": files,
          "qualification_pending": ["first boot", "native setup handoff", "Google sign-in",
                                    "Play Store install", "reboot persistence", "responsiveness"]}
(DEST / "google-integration-verification.json").write_text(json.dumps(report, indent=2) + "\n")
(DEST / "SHA256SUMS.txt").write_text("".join(x["sha256"] + "  " + x["name"] + "\n" for x in files))
print(json.dumps({k: report[k] for k in ("status", "native_files_unchanged", "files")}), flush=True)
