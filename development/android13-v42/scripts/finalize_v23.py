"""Finalize offline-ready metadata after all build and pairing checks pass."""
from pathlib import Path
import hashlib,json,struct
project=Path(__file__).resolve().parents[1]
system=project/'artifacts/lineage20-rom-v13'
boot=project/'artifacts/android13-full-v23'
pair=json.loads((boot/'system-pair.json').read_text(encoding='utf-8'))
assert pair['status']=='OFFLINE_VERIFIED_NOT_BOOT_TESTED'
host=json.loads((system/'host-verification.json').read_text(encoding='utf-8'))
assert host['status']=='VERIFIED'
expected=dict((line.split()[1],line.split()[0]) for line in
              (system/'SHA256SUMS').read_text(encoding='utf-8').splitlines())
with (system/'system.img').open('rb') as stream:
    header=stream.read(28)
    magic,major,minor,hsize,csize,block,blocks,chunks,checksum=struct.unpack('<I4H4I',header)
    assert magic==0xed26ff3a and major==1 and block*blocks==1594884096
    stream.seek(0)
    digest=hashlib.file_digest(stream,'sha256').hexdigest()
assert digest==expected['system.img']
assert host['sha256']==expected['system.raw.img']==pair['system_sha256']
host['sparse_sha256']=digest
host['sparse_bytes']=(system/'system.img').stat().st_size
(system/'host-verification.json').write_text(json.dumps(host,indent=2)+'\n',encoding='utf-8')

status='''## v23/v13 OFFLINE VERIFIED; no tablet access - 2026-11-06

User requested an EGL window compatibility layer, correction of the startup crash, and the combined ROM built before any further boot tests. Both source changes are implemented and the complete system image is built. NO device commands, transfers, flashes, emulator boots or tablet boots this pass. Last verified hardware state remains TWRP with installed v22 BOOT and staged v12 system; the new files have not been sent to it.

Authoritative pair: artifacts/android13-full-v23/system-pair.json, status OFFLINE_VERIFIED_NOT_BOOT_TESTED. System artifacts/lineage20-rom-v13 contains sparse system.img and raw system.raw.img. Raw size 1594884096 bytes fits SYSTEM exactly; e2fsck exit0; native and Windows raw/sparse hashes match. New system SHA681292d76a46081ea70ade81e99f840218eea12f3455811b19522af6c5809ba1, MD52d4db36a08cd44a44754e3e5f7a634a3. New padded BOOT SHA811a3dbfa08e83005236def1b86eae3495bca49f5c1f13a43e82c804d9c195b5, MD554325830bda64adfb02b3f1b204ea4de. Pinned kernel-alarm, matching galcore and policy unchanged; unpacked boot checks pass.

Graphics patch0038 supersedes0037. Real EGL native window/default framebuffer/window swap around the exact target, two/three-buffer lifetime handling, fence ownership and coordinate conversion; retained libui owner and direct framebuffer composer remain. Startup patch0039 moves first-fork class-visibility checkpoint wait outside the mutator lock, before JNI method visits reacquire object access. ART assertions remain enabled. Actual image contains the new renderer, no old FBO-handoff marker, and rebuilt libart/libartd matching native output.

Build175133Z succeeded in07:55. Initial173909Z compile found a vec3/diagonal-matrix API mismatch, corrected to supported vec4 constructor before successful build. Window slot ASan/UBSan regression PASS. Extracted pre-fork function host contract regression reproduces original lock error and passes100 delayed waits+100 later forks; this is NOT full ART runtime validation. ARM compilation/link, image contents, ext4 and pairing checks PASS. See OFFLINE-V23.md and evidence/offline-v23/source-provenance.json.

Both changes are offline-ready, not hardware-proven. Physical graphics, successful full Android startup and performance remain unverified. Window-per-frame creation can be expensive. No automatic test runner or staging step was launched. Older status sections below are historical.

'''
p=project/'CURRENT-STATUS.md'
s=p.read_text(encoding='utf-8')
assert '## v23/v13 OFFLINE VERIFIED;' not in s
first,rest=s.split('\n',1)
p.write_text(first+'\n\n'+status+rest.lstrip('\n'),encoding='utf-8',newline='\n')
p=project/'OFFLINE-V23.md'
s=p.read_text(encoding='utf-8').replace(
    'Build and export verification pending. No tablet command, flash or boot is part of this pass.',
    'OFFLINE VERIFIED, NOT BOOT TESTED. Full Android build, exported image contents and hashes, partition fit, ext4 check and matching boot verification all passed. No tablet command, flash or boot occurred.')
s=s.replace('* The Android build, actual image binary comparison, filesystem/partition checks and boot/system pairing must all finish before status is changed to offline ready.',
    '* Android ARM compilation/link passed. The actual system image contains the new renderer and rebuilt libart/libartd; all match build output. Raw size is 1,594,884,096 bytes; e2fsck passed. Windows raw and sparse hashes match native exports. Unpacked boot kernel/module/policy and startup event checks passed.')
s+='''
## Outputs

* System: artifacts/lineage20-rom-v13/system.img (sparse) and system.raw.img (raw).
* Boot: artifacts/android13-full-v23/boot.img and padded KERNEL.img.
* Pairing and validation status: artifacts/android13-full-v23/system-pair.json.
* Build: system-image-20261106T175133Z.log, success in 07:55.

For a clean pinned source checkout, build_system_image.sh applies patches0038 and0039 (0037 is superseded). prepare_offline_v23.py migrates the existing v22 source tree and archives the cumulative graphics patch. The preserved first failed compile log records the matrix-constructor correction; the final artifacts come from the successful build.
'''
p.write_text(s,encoding='utf-8',newline='\n')
print(json.dumps({'status':pair['status'],'raw_sha256':host['sha256'],
    'sparse_sha256':digest,'boot_sha256':pair['boot_sha256'],'tablet_access':False},indent=2))
