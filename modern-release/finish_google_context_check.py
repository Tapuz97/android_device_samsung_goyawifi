"""Complete the candidate's SELinux xattr checks; never touches the tablet."""
from pathlib import Path
import gzip
import hashlib
import json
import shutil
import subprocess

root = Path("/root/t110-lineage14-ui/artifacts-modern-google-20261115")
report_path = root / "google-integration-verification.json"
report = json.loads(report_path.read_text())
assert report["status"] == "OFFLINE_CHECKED_GOOGLE_CANDIDATE_NOT_BOOT_TESTED"
image = root / "system.raw.img"
def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        while data := f.read(1024 * 1024):
            h.update(data)
    return h.hexdigest()
assert sha(image) == report["files"][0]["sha256"]
context = root / "system-file-context.bin"
context.write_bytes(b"u:object_r:system_file:s0\0")
paths = set()
for entry in report["added_files"]:
    p = Path(entry["file"])
    paths.add("/" + str(p))
    for parent in p.parents:
        if str(parent) != ".":
            paths.add("/" + str(parent))
# Only label new directories, never alter pre-existing native parent inodes.
base = Path("/root/t110-lineage14-ui/artifacts-settings-lock-20261115/system.raw.img")
new_paths = []
for p in sorted(paths):
    old = subprocess.run(["/usr/sbin/debugfs", "-R", "stat " + p, str(base)],
                         capture_output=True, text=True, check=True)
    if "Inode:" not in old.stdout:
        new_paths.append(p)
commands = root / "selinux-label-fix.txt"
commands.write_text("".join("ea_set -f " + str(context) + " " + p +
                           " security.selinux\n" for p in new_paths))
subprocess.run(["/usr/sbin/debugfs", "-w", "-f", str(commands), str(image)],
               capture_output=True, text=True, check=True)
temp = root / "readback-context.bin"
for p in new_paths:
    subprocess.run(["/usr/sbin/debugfs", "-R", "ea_get -f " + str(temp) + " " + p +
                    " security.selinux", str(image)], capture_output=True, check=True)
    assert temp.read_bytes() == context.read_bytes(), p
    temp.unlink()
subprocess.run(["/usr/sbin/e2fsck", "-fn", str(image)], check=True, capture_output=True)
with image.open("rb") as source, (root / "system.raw.img.gz").open("wb") as target:
    with gzip.GzipFile(fileobj=target, mode="wb", mtime=0, compresslevel=6) as output:
        shutil.copyfileobj(source, output)
for entry in report["files"]:
    path = root / entry["name"]
    entry.update(bytes=path.stat().st_size, sha256=sha(path))
report["selinux_labels_checked"] = len(new_paths)
report["selinux_label_terminator_checked"] = True
report_path.write_text(json.dumps(report, indent=2) + "\n")
(root / "SHA256SUMS.txt").write_text("".join(x["sha256"] + "  " + x["name"] + "\n"
                                            for x in report["files"]))
print(json.dumps({"status": report["status"], "labels_checked": len(new_paths),
                  "files": report["files"]}), flush=True)
