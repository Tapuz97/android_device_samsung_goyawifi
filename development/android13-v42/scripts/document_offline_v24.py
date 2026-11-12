"""Record completed offline verification; never accesses the tablet."""
from pathlib import Path
import json

root=Path(__file__).resolve().parents[1]
pair=json.loads((root/'artifacts/android13-full-v24/system-pair.json').read_text())
assert pair['status']=='OFFLINE_VERIFIED_NOT_BOOT_TESTED'
fs=json.loads((root/'artifacts/lineage20-rom-v15/system-verification.json').read_text())
assert fs['fsck_exit']==0
summary=f'''## v24/v15 OFFLINE VERIFIED - 2026-11-06

Both startup-delay and missing-GPS-provider initialization corrections are implemented, built, and verified in the exported image. No tablet access, transfer, flash, emulator boot or tablet boot occurred this pass. No test is scheduled. Last verified hardware state remains TWRP with installed v23 BOOT and staged v13 system; this has not been refreshed during offline work.

Authoritative pair: `artifacts/android13-full-v24/system-pair.json`, status `OFFLINE_VERIFIED_NOT_BOOT_TESTED`. Corrected system: `artifacts/lineage20-rom-v15/system.raw.img` (sparse `system.img` alongside it). Raw size {pair['system_bytes']} bytes fits SYSTEM exactly; e2fsck exit 0; filesystem feature masks match v13. Native and Windows raw/sparse SHA-256 match. Raw SHA-256 `{pair['system_sha256']}`, MD5 `{pair['system_md5']}`. Boot files in `artifacts/android13-full-v24` are byte-identical to v23, unpacked and reverified against current init, kernel, GPU module and policy; no boot change is needed. BOOT SHA-256 `{pair['boot_sha256']}`.

Build `system-image-20261106T202931Z.log` completed in 07:28. Actual-image contents PASS: standard ART present and debug ART absent, previous ART0039/graphics0038 retained, optional-HAL property/readable context and compiled GNSS0040 present, LMKD0041 preserves sender credential enforcement, and all three first-start apps contain ARM OAT speed-compiled code with matching APK DEX checksums. Patch0042 supplies APEX app precompilation; patch0043 selects standard ART in the separately evaluated runtime product node. GNSS/API-double and real host socket ASan/UBSan regression checks passed. These host tests do not establish Android hardware behavior.

The initial v14 export was rejected offline because the parent product ART setting did not affect runtime package selection. It is explicitly marked `OFFLINE_REJECTED_DO_NOT_FLASH`; use v15 only. The previous v23 hardware result remains failed, unchanged. GPS positioning is still unported: the new behavior avoids waiting for an absent provider. Full boot, UI/touch and actual startup-time improvement still require a later hardware test. Watchdog limits and permission completion requirements are unchanged. See `OFFLINE-V24.md` and `evidence/v15-startup-fixes-contents.json`.

'''
p=root/'CURRENT-STATUS.md'
s=p.read_text(encoding='utf-8')
assert '## v24/v15 OFFLINE VERIFIED' not in s
p.write_text(s.replace('\n\n','\n\n'+summary,1),encoding='utf-8')
p=root/'OFFLINE-V24.md'
s=p.read_text()
start=s.index('Status:')
end=s.index('\n\n',start)
s=s[:start]+('Status: **OFFLINE VERIFIED, NOT BOOT TESTED**. The corrected v24/v15 ROM is built and checked. No tablet access, flash, or boot test was performed this pass. The previous v23/v13 test failed; its evidence remains unchanged in `hardware-tests/20261106-211758-core`.')+s[end:]
s=s.replace('The completed image must also pass','The completed image passed')
s+='''
## Completed output

- [System image](artifacts/lineage20-rom-v15/system.raw.img), with sparse `system.img` in the same folder.
- [Matching boot files and pairing manifest](artifacts/android13-full-v24/system-pair.json).
- [Actual image contents and source provenance](evidence/v15-startup-fixes-contents.json).
- [Filesystem/partition report](artifacts/lineage20-rom-v15/system-verification.json).
- [Windows export hash verification](artifacts/lineage20-rom-v15/host-verification.json).
- [Host regression report](evidence/offline-v24/regressions.json).

Final build `system-image-20261106T202931Z.log` completed successfully in 07:28. Actual-image inspection confirms standard ART and absence of debug ART, compiled GNSS and credential fixes, retained graphics/ART corrections, and three speed-compiled ARM app artifacts whose DEX checksums match the packaged APKs. Ext4 checks passed with exit 0, the raw image fits the 1,594,884,096-byte SYSTEM partition, and raw/sparse hashes match between Linux and Windows. The matching boot image was unpacked and its current inputs reverified; its bytes are unchanged because these corrections are system-only.

The initial v14 export is rejected and marked DO NOT FLASH. The corrected output is v15. Neither was booted during this offline pass. A usable Android screen, touch, GPS positioning and improved physical startup time have not been established by these checks.
'''
s+=f"\nRaw system SHA-256: `{pair['system_sha256']}`.\n\nBOOT SHA-256: `{pair['boot_sha256']}`.\n"
p.write_text(s)
print('Documented verified v24/v15 outputs; no hardware operations.')
