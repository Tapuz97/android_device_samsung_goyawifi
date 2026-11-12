"""Record the completed bionic/Binder hardware milestone (no device actions)."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / 'hardware-tests/LATEST-RESULT.json'
data = json.loads(path.read_text())
data['current_state'] = 'Patched kernel/TWRP diagnostic in BOOT; root ADB. Stock BOOT restoration pending after native tests.'
data['native_userspace_evidence'] = {
    'bionic': 'artifacts/android13-native/bionic-result.json',
    'libbinder': 'artifacts/android13-native/binder-result.json',
    'selinux_enforcing': True,
    'scope': 'Android 13 binaries ran inside diagnostic recovery; not Android 13 init or OS boot',
}
path.write_text(json.dumps(data, indent=2) + '\n')

path = root / 'CURRENT-STATUS.md'
text = path.read_text(encoding='utf-8')
text = text.replace('Android 13 userspace has not booted.', 'Android 13 bionic and libbinder probes now pass on hardware with SELinux enforcing; Android 13 init and the OS have not booted.')
text = text.replace('The tablet is back on stock Android, with `sys.boot_completed=1` verified after both kernel trials and the checksum-verified stock BOOT restore.', 'Stock Android was restored and boot_completed=1 verified after the first kernel cycle. The second native test cycle is currently running patched-kernel TWRP in BOOT; restore stock BOOT after testing.')
text = text.replace('being seeded from the intact internal checkout', 'running the full source sync after a verified source-seed copy')
text = text.replace('but Android runtime binaries have not yet compiled', 'and Android 13 bionic/libbinder binaries compile and pass focused hardware tests')
text = text.replace('Compilation and hardware validation remain pending; this is not a completed fix.', 'Device compilation passed; a host-sysroot magic-constant compatibility fix is rebuilding. Lifecycle hardware validation remains pending; this is not a completed fix.')
path.write_text(text, encoding='utf-8')

path = root / 'NATIVE-USERSPACE.md'
text = path.read_text(encoding='utf-8')
text = text.replace('It is prepared but not compiled or run.', 'It is compiled; runtime validation awaits modern init and mounted cgroups.')
text = text.replace('Apply-check passed; compilation and runtime validation are still pending.', 'Apply-check and device compilation passed. The host build exposed a missing cgroup-v2 magic constant in its old glibc sysroot; a guarded constant definition fixes that build dependency. Runtime lifecycle validation is still pending.')
text += '''
## Hardware native milestone, 2026-11-05

Actual Android 13 static bionic passes pthread/TLS, clock, eventfd/epoll, getentropy fallback and fork/exec on both stock and patched T110 kernels. On the patched kernel, actual Android 13 libbinder also passes a two-process Parcel roundtrip on the unused diagnostic `/dev/vndbinder` context, using only the matching modern linker/library bundle. Both patched-kernel tests ran with SELinux enforcing. Logs and hashes are in `artifacts/android13-native/*-result.json` and `hardware-tests/20261105-android13-native/`.

The next components are building: first-stage init, recovery second-stage init/adbd, the real recovery SELinux policy, shell/tools and a bounded recovery fallback. Packaging script `scripts/package_native_ramdisk.py` checks ELF closure, init syntax, boot geometry and partition fit. This image has not yet been packaged or booted. Full services, libhwbinder and graphics remain unvalidated.
'''
path.write_text(text, encoding='utf-8')
