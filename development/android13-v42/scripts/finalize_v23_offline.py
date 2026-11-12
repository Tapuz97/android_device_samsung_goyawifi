"""Verify the local v23 export and prepare its already installed v27 BOOT pairing."""
from pathlib import Path
import datetime
import hashlib
import json

p=Path(__file__).resolve().parents[1]
artifact=p/'artifacts/lineage20-rom-v23'
e=p/'evidence/offline-v33'
contents=json.loads((e/'contents.json').read_text())
assert contents['status']=='PASS'
assert 'system/framework/framework.jar' in contents['changed']
fit=json.loads((artifact/'system-verification.json').read_text())
assert fit['status']=='FIT_AND_EXT4_VERIFIED' and fit['fsck_exit']==0
assert 'build completed successfully' in (artifact/'system-build.log').read_text(errors='replace')
source=artifact/'system.raw.img'
digests=[hashlib.sha256(),hashlib.md5()]
with source.open('rb') as stream:
    while block:=stream.read(8*1024*1024):
        for digest in digests:digest.update(block)
sha,md5=[h.hexdigest() for h in digests]
assert sha==fit['sha256']==contents['system_sha256']
assert source.stat().st_size==1594884096==contents['system_bytes']
boot=p/'artifacts/android13-full-v27'
prov=json.loads((boot/'provenance.json').read_text())
boot_bytes=(boot/'KERNEL.img').read_bytes()
assert hashlib.sha256(boot_bytes).hexdigest()==contents['boot_sha256']==prov['full_boot_sha256']
host=dict(status='VERIFIED',sha256=sha,md5=md5,bytes=source.stat().st_size,
    build_exit=0,build_log='system-build.log',
    verified_at=datetime.datetime.now().astimezone().isoformat())
(artifact/'host-verification.json').write_text(json.dumps(host,indent=2)+'\n')
pair=dict(status='OFFLINE_VERIFIED_NOT_BOOT_TESTED',system_artifact='system.raw.img',
    boot_artifact='../android13-full-v27/KERNEL.img',system_sha256=sha,system_md5=md5,
    system_bytes=source.stat().st_size,boot_sha256=prov['full_boot_sha256'],
    boot_md5=prov['full_boot_md5'],kernel_sha256=prov['kernel_sha256'],
    module_sha256=prov['module_sha256'],bootstrap_policy_sha256=prov['bootstrap_policy_sha256'],
    existing_boot_reused=True,hardware_tested=False,hardware_validated=False,full_boot_passed=False,
    fixes=['T110 ordinary ViewRoot windows use software Canvas compatibility fallback',
           'Canonical app_widgets declaration starts the missing widget service',
           'Declare user-confirmed basic touchscreen capability',
           'HWC exposes natural600x1024 with no second rotation in SurfaceFlinger',
           'Bounds-checked final-frame rotation270 matching stock panel mounting',
           'Accept actual608px padded backing for600px logical rows',
           'Framebuffer OFF/ON forwarded to kernel blanking'],
    retained=['All v18 startup/storage fixes','v27 ext4 ACL kernel'],
    limits=['New launcher/window behavior needs hardware validation; this is a software UI fallback',
            'Wi-Fi radio and other unported hardware remain incomplete'])
(artifact/'rom-pair.json').write_text(json.dumps(pair,indent=2)+'\n')
print(json.dumps(pair,indent=2))
