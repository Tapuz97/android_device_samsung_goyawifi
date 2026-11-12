"""Publish the verified offline checkpoint only after the pair is complete."""
from pathlib import Path
import json
p=Path(__file__).resolve().parents[1]
pair=json.loads((p/'artifacts/android13-full-v25/system-pair.json').read_text())
assert pair['status']=='OFFLINE_VERIFIED_NOT_BOOT_TESTED'
host=json.loads((p/'artifacts/lineage20-rom-v16/host-verification.json').read_text())
entry=f'''## v25/v16 OFFLINE VERIFIED - 2026-11-07

Keystore/user-unlock and SystemUI corrections are implemented, built and verified offline. NO tablet access, transfer, flash, emulator/kernel/tablet boot this pass. Last hardware state remains TWRP with installed v24 BOOT/staged v15; previous failed hardware result is unchanged. No automatic test scheduled.

Authoritative pair: artifacts/android13-full-v25/system-pair.json, OFFLINE_VERIFIED_NOT_BOOT_TESTED. Correct system is artifacts/lineage20-rom-v16/system.raw.img, SHA {pair['system_sha256']}, MD5 {pair['system_md5']}. Matching padded BOOT SHA {pair['boot_sha256']}, MD5 {pair['boot_md5']}. This pair needs the NEW kernel; old v24 BOOT does not contain the keystore fix. Kernel/module/config provenance is artifacts/kernel-binder-secctx/provenance.json. All other ramdisk files preserved and verified after unpacking.

Patch0044 adds kernel delivery of requested Binder caller security contexts with opener SID snapshot, protected tail, cleanup/error handling, legacy ABI and synchronous stack compatibility. No caller-ID fabrication or keystore-check/assertion bypass. Patch0045 accepts AppOpsService's valid null result in SystemUI, retaining live callbacks. Full ARM kernel/module and system builds passed; host extracted-code ASan/UBSan and Java/ABI checks passed. Actual image contains the new DEX guard and matching precompiled SystemUI; keystore2/framework.jar/services.jar byte-identical to v15. All v24 startup/graphics fixes retained. Ext4/fsck0, exact partition fit1594884096, exported Linux/Windows hashes and boot unpacking passed.

Final system log {host['build_log']}. SSD read retries interrupted the initial build; after user reconnect, final build/export/checks completed. Do not treat that interruption as a source-code failure or hide future drive errors. See OFFLINE-V25.md and evidence/offline-v25. Full user unlocking/UI, kernel runtime and all hardware still require a later authorized test. No GPS/audio/codec-functionality claim.

'''
f=p/'CURRENT-STATUS.md';s=f.read_text(encoding='utf-8');assert '## v25/v16 OFFLINE VERIFIED' not in s
f.write_text(s.replace('\n\n','\n\n'+entry,1),encoding='utf-8')
f=p/'OFFLINE-V25.md';s=f.read_text();start=s.index('Status:');end=s.index('\n\n',start)
s=s[:start]+'Status: **OFFLINE VERIFIED, NOT BOOT TESTED**. Both corrections are built into the v25/v16 pair. No tablet access, flash, kernel/emulator boot or tablet boot occurred in this pass. The previous failed hardware result is unchanged.'+s[end:]
s=s.replace('Completion additionally requires both full ARM builds','Completed checks include both full ARM builds')
paragraph='The internal-drive kernel build completed successfully. The external build SSD then logged repeated Windows Event 153 read retries, interrupting the System UI rebuild. The new ROM pair has not been exported or marked ready. Source patches and passing host tests are preserved on C:.'
s=s.replace(paragraph,'The initial system build was interrupted by repeated SSD read retries. After the user reconnected the drive, the final system build, export and checks completed. This is an offline-ready candidate; successful user unlocking and usable UI are not yet established.')
s+=f'''
## Verified outputs

- [System raw image](artifacts/lineage20-rom-v16/system.raw.img), with sparse `system.img` alongside it.
- [Matching boot and system manifest](artifacts/android13-full-v25/system-pair.json).
- [Kernel and module provenance](artifacts/kernel-binder-secctx/provenance.json).
- [Image contents](evidence/v16-startup-fixes-contents.json), [actual SystemUI DEX](evidence/offline-v25/systemui-dex-verification.json), and [host checks](evidence/offline-v25/regressions.json).
- [Filesystem/partition checks](artifacts/lineage20-rom-v16/system-verification.json) and [Windows hash verification](artifacts/lineage20-rom-v16/host-verification.json).

Raw system SHA-256: `{pair['system_sha256']}`.

Padded BOOT SHA-256: `{pair['boot_sha256']}`.

The raw image is 1,594,884,096 bytes and fits the existing SYSTEM partition. The boot package fits the 16 MiB BOOT partition. The kernel configuration matches the parent, and the boot image was unpacked to verify kernel/module hashes and unchanged ramdisk contents. The new Binder command is present in the ARM object code. These checks do not replace a future hardware boot test.
'''
f.write_text(s)
print('Documented verified v25/v16; no boot scheduled')
