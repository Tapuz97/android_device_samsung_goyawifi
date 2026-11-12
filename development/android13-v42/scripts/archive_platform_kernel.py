"""Archive the compiled kernel after its ambient capability regression passes."""
import difflib
import hashlib
import json
from pathlib import Path
import shutil

PROJECT = Path(__file__).resolve().parents[1]
BASE = Path("/root/t110-build")
baseline = BASE / "kernel-binder-modern"
source = BASE / "kernel-platform"
output = BASE / "out-platform"
evidence = PROJECT / "evidence/qemu-ambient-test.log"
assert "T110_AMBIENT_REGRESSION_PASS" in evidence.read_text()
destination = PROJECT / "artifacts/kernel-platform"
destination.mkdir()
patch_files = [
    "fs/proc/array.c", "include/linux/cred.h", "include/linux/prctl.h",
    "include/linux/securebits.h", "kernel/user_namespace.c",
    "security/commoncap.c", "security/keys/process_keys.c",
]
patch = []
for name in patch_files:
    patch.extend(difflib.unified_diff(
        (baseline / name).read_text().splitlines(True),
        (source / name).read_text().splitlines(True),
        fromfile="a/" + name, tofile="b/" + name,
    ))
patch_path = PROJECT / "patches/0018-kernel-ambient-capabilities.patch"
patch_path.write_text("".join(patch))
modules = list(output.rglob("galcore.ko"))
assert len(modules) == 1
files = {
    "zImage": output / "arch/arm/boot/zImage",
    "kernel.config": output / ".config",
    "galcore.ko": modules[0],
    "build.log": BASE / "logs/platform-kernel-build.log",
}
records = {}
for name, path in files.items():
    shutil.copyfile(path, destination / name)
    records[name] = {
        "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }
config = (destination / "kernel.config").read_text()
assert 'CONFIG_CMDLINE="androidboot.hardware=mrvl"' in config
assert "CONFIG_CMDLINE_EXTEND=y" in config
assert "# CONFIG_USER_NS is not set" in config
metadata = {
    "status": "COMPILED_QEMU_AMBIENT_TEST_PASSED_HARDWARE_PENDING",
    "files": records,
    "incremental_patch": str(patch_path.relative_to(PROJECT)),
    "regression": str(evidence.relative_to(PROJECT)),
    "ambient_upstream_commit": "58319057b7847667f0c9585b9de0e8932b0fdb08",
    "adaptations": "3.4 UID API and preallocated prctl credentials; ambient always copied on ordinary exec; securebit raise restriction",
}
(destination / "provenance.json").write_text(json.dumps(metadata, indent=2) + "\n")
print(json.dumps(metadata, indent=2))
