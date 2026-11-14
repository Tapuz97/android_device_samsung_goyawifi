from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess

audit = Path('/root/t110-android13-audit')
product = Path('/root/t110-android13/out/target/product/t110_bringup')
root = audit / 'loader-rootfs'
shim = product / 'system/vendor/lib/libt110_audio_legacy_compat.so'
probe = Path('/root/t110-android13/out/soong/.intermediates/device/samsung/t110_bringup/audio/t110_legacy_libc_probe/android_arm_armv7-a-neon_cortex-a9/t110_legacy_libc_probe')
symbols = subprocess.check_output(['readelf', '--dyn-syms', '-W', str(shim)], text=True)
expected = json.loads((audit / 'legacy-libc-bridge.json').read_text())['symbols']
for name in expected:
    assert re.search(r'\bGLOBAL\s+DEFAULT\s+\d+\s+' + re.escape(name) + r'\b', symbols), name
dynamic = subprocess.check_output(['readelf', '-d', str(shim)], text=True)
assert 'TEXTREL' not in dynamic, dynamic
shutil.copy2(shim, root / 'vendor/lib/libt110_audio_legacy_compat.so')
exe = root / 'data/local/tmp/legacy-libc-probe'
shutil.copy2(probe, exe)
cmd = ['unshare', '--pid', '--fork', '--mount-proc', 'qemu-arm', '-cpu', 'cortex-a9',
       '-L', str(root), '-E', 'LD_LIBRARY_PATH=/vendor/lib:/system/lib', '-E', 'TMPDIR=/tmp', str(exe)]
result = subprocess.run(cmd, text=True, capture_output=True, timeout=60)
data = dict(command=cmd, exit=result.returncode, stdout=result.stdout, stderr=result.stderr,
            symbols=len(expected), shim_sha256=hashlib.sha256(shim.read_bytes()).hexdigest(),
            shim_textrel=False, diagnostic_target_sdk_lowered=False, hardware_opened=False,
            scope='Real Soong ARM shim/probe under actual Android13 Bionic and QEMU; no production namespace or device')
(audit / 'legacy-libc-probe.json').write_text(json.dumps(data, indent=2) + '\n')
print(result.stdout)
if result.stderr:print(result.stderr)
assert result.returncode == 0 and 'PASS: 26 exact Bionic helper trampolines' in result.stdout, data
# The probe is a build diagnostic, never a ROM payload. Older driver revisions
# requested its installed target; remove only that identical generated copy.
installed = product / 'system/vendor/bin/t110_legacy_libc_probe'
if installed.exists():
    assert installed.is_file() and installed.read_bytes() == probe.read_bytes(), installed
    installed.unlink()
