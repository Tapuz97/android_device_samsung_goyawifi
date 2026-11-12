"""Verify the Windows export and record the v18 system/existing-v26 boot pair."""
from datetime import datetime
import hashlib
import json
from pathlib import Path

p=Path(__file__).resolve().parents[1]
artifact=p/'artifacts/lineage20-rom-v18'
e=p/'evidence/offline-v27'
contents=json.loads((e/'contents.json').read_text())
regressions=json.loads((e/'regressions.json').read_text())
fit=json.loads((artifact/'system-verification.json').read_text())
assert contents['status']==regressions['status']=='PASS'
assert fit['status']=='FIT_AND_EXT4_VERIFIED' and fit['fsck_exit']==0
assert 'build completed successfully' in (artifact/'system-build.log').read_text(errors='replace')
source=artifact/'system.raw.img'
hashes=[hashlib.sha256(),hashlib.md5()]
with source.open('rb') as stream:
    while block:=stream.read(8*1024*1024):
        for digest in hashes: digest.update(block)
sha,md5=[h.hexdigest() for h in hashes]
assert sha==fit['sha256']==contents['system_sha256']
assert source.stat().st_size==1594884096==contents['system_bytes']
boot=p/'artifacts/android13-full-v26'
prov=json.loads((boot/'provenance.json').read_text())
boot_bytes=(boot/'KERNEL.img').read_bytes()
assert hashlib.sha256(boot_bytes).hexdigest()==contents['boot_sha256']==prov['full_boot_sha256']
assert hashlib.md5(boot_bytes).hexdigest()==prov['full_boot_md5']
host=dict(status='VERIFIED',sha256=sha,md5=md5,bytes=source.stat().st_size,
          build_exit=0,build_log='system-image-20261107T104621Z.log',
          verified_at=datetime.now().astimezone().isoformat())
(artifact/'host-verification.json').write_text(json.dumps(host,indent=2)+'\n')
pair=dict(status='OFFLINE_VERIFIED_NOT_BOOT_TESTED',system_artifact='system.raw.img',
    boot_artifact='../android13-full-v26/KERNEL.img',system_sha256=sha,system_md5=md5,
    system_bytes=source.stat().st_size,boot_sha256=prov['full_boot_sha256'],
    boot_md5=prov['full_boot_md5'],kernel_sha256=prov['kernel_sha256'],
    bootstrap_policy_sha256=prov['bootstrap_policy_sha256'],
    existing_boot_reused=True,hardware_tested=False,hardware_validated=False,
    boot_completed=False,full_boot_passed=False,hardware_boots_this_pass=0,
    flashes_this_pass=0,tablet_access_this_pass=False,
    fixes=['Wi-Fi feature/service startup declaration',
           'NetworkStats global-alert service error handling with polling retained',
           'netd global-alert state committed only after successful kernel operation',
           'MediaProvider FUSE selected instead of incompatible Samsung sdcardfs',
           'FUSE protocol/capability bit31 masks made unsigned'],
    retained=['Codec allocator error handling','App EGL/gralloc initialization',
              'Binder security-context/user unlock','SystemUI AppOps guard','Existing display bridge'],
    limits=['This candidate has not been booted on Android, emulator or tablet',
            'Wi-Fi feature publication does not establish working radio/HAL',
            'FUSE host protocol check does not establish a working hardware storage mount',
            'Complete usable UI, touch and other unported hardware remain unverified'])
(artifact/'rom-pair.json').write_text(json.dumps(pair,indent=2)+'\n')
doc=f'''# v18 system: combined offline startup corrections

The three failures from the v26/v17 hardware test were traced to source and addressed in one candidate. This build is offline verified and has not been flashed or booted. It reuses the existing v26 BOOT because its kernel, early policy and classpath remain compatible; no duplicate boot package was created.

## Corrections

- **Setup/Wi-Fi service:** the tablet product lacked `android.hardware.wifi.xml`. SystemServer gates WifiService startup on that feature, even though its service JAR was already installed. The feature declaration is now included. The radio HAL remains unported; this addresses the missing framework service, not wireless connectivity certification.
- **Network statistics:** patch0049 catches netd's ServiceSpecificException during optional global-alert registration, retaining scheduled polling and provider callbacks. Patch0050 commits the netd quota state only when the kernel operation succeeds, so failed insertion no longer leads to updating an absent quota entry.
- **Emulated storage:** saved kernel logs show Samsung sdcardfs rejecting the modern `fsuid` option. The product now sets `external_storage.sdcardfs.enabled=false`, selecting the existing MediaProvider FUSE implementation. No data formatting, direct app access to raw media, or unsupported ext4 quota/casefold enable was introduced.
- **FUSE initialization:** patch0051 makes both bit31 passthrough masks unsigned. Host sanitizers exposed the signed-shift issue; the corrected protocol exchange passes with sanitizer recovery disabled.

Android documents its [MediaProvider FUSE storage path](https://source.android.com/docs/core/storage/scoped) and the separate [SDCardFS replacement concerns](https://source.android.com/docs/core/storage/sdcardfs-deprecate). This candidate selects the existing FUSE path for the current unencrypted test data; it does not adopt modern filesystem casefold/quota configuration or claim full storage compatibility from a host test.

## Validation and limits

Full ARM system build completed: `system-image-20261107T104621Z.log`. Host tests use production Java/native method bodies for network error/retry state and callback retention. The complete pinned libfuse library plus MediaProvider's actual initialization callback exchanged FUSE7.18 requests over a socketpair with this kernel's advertised flags. No host filesystem was mounted and no Android system was booted. Final ASan/UBSan checks pass; an earlier protocol result with recoverable UBSan warnings was superseded and preserved in the evidence folder. The initial ARM build was stopped before input edits, then resumed with all corrections together.

The exported filesystem passed read-only ext4 checks, exact partition fit, native-to-Windows SHA256 comparison, actual network-service DEX catch-handler inspection, Wi-Fi XML and storage-property checks. Existing codec/EGL/gralloc, SystemUI, keystore, framework and display binaries were retained. The new system's compiled policy and root classpath match the existing v26 BOOT.

- Raw system size: {source.stat().st_size:,} bytes.
- System SHA256: `{sha}`
- System MD5: `{md5}`
- Existing v26 BOOT SHA256: `{prov['full_boot_sha256']}`
- Pair manifest: `artifacts/lineage20-rom-v18/rom-pair.json`.
- Evidence: `evidence/offline-v27/contents.json`, `regressions.json`, DEX inspection and sanitizer logs.

The last hardware result remains the failed v26/v17 test. The tablet was last confirmed in TWRP; it was not accessed during this pass. A later full boot must establish setup completion, storage mounting, sustained system_server stability and actual screen/touch behavior. No working-ROM or working-Wi-Fi claim is made.
'''
(p/'OFFLINE-V27.md').write_text(doc,encoding='utf-8')
note=f'''## v18 SYSTEM OFFLINE VERIFIED - NOT FLASHED - 2026-11-07

Combined startup fixes are built and verified. No tablet access, transfer, flash, emulator/Android/tablet boot this pass. Last installed system remains v17 with v26 BOOT in TWRP. User's late visual replies were recovery observations only; they were absent for the prior test.

New candidate artifacts/lineage20-rom-v18/system.raw.img SHA{sha}, MD5{md5}, bytes1594884096. Reuse artifacts/android13-full-v26/KERNEL.img SHA{prov['full_boot_sha256']}, MD5{prov['full_boot_md5']}; exact policy/classpath compatibility checked. Authoritative pair artifacts/lineage20-rom-v18/rom-pair.json has hardware_tested=false and full_boot_passed=false. No need to repackage unchanged BOOT.

Wi-Fi feature XML now starts existing framework service, radio still unported. external_storage.sdcardfs.enabled=false selects existing MediaProvider FUSE instead of Samsung sdcardfs that rejected fsuid. Patches0049/0050 fix the observed network alert exception and failed-insert state caching. Patch0051 fixes signed bit31 FUSE masks found in host sanitizer checks. Earlier protocol report with UBSan warnings was superseded; final checks disable sanitizer recovery and PASS. Initial build2690 was canceled before changes; successful resumed build73061 log system-image-20261107T104621Z.log. Full ARM build, actual DEX/feature/property/retained-binary/policy checks, ext4/fsck/fit and Windows hashes PASS. See OFFLINE-V27.md and evidence/offline-v27. Later hardware validation still required; do not report usable ROM from offline checks.

'''
status=p/'CURRENT-STATUS.md'
first,rest=status.read_text(encoding='utf-8-sig').split('\n',1)
status.write_text(first+'\n\n'+note+rest.lstrip('\n'),encoding='utf-8')
print(json.dumps(pair,indent=2))
