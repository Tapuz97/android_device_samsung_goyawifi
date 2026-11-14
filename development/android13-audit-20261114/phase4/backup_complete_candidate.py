from pathlib import Path
import gzip
import hashlib
import json
import shutil
import zipfile

audit=Path('/root/t110-android13-audit');image_dir=audit/'complete-image'
image=json.loads((audit/'complete-image-verification.json').read_text())
ns=json.loads((audit/'production-namespace-verification.json').read_text())
boot=json.loads((audit/'candidate-boot-verification.json').read_text())
policy=json.loads((audit/'complete-image-policy-verification.json').read_text())
assert image['status']==ns['status']==policy['status']=='PASS'
assert boot['status']=='PASS_OFFLINE_NOT_HARDWARE_QUALIFIED'
assert image['raw_image_sha256']==ns['image_sha256']==policy['image_sha256']==boot['system_sha256']
dest=audit/'complete-candidate-backup';dest.mkdir(exist_ok=True)
raw=image_dir/'system.raw.img'
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
assert sha(raw)==image['raw_image_sha256']
assert sha(image_dir/'boot.img')==boot['sha256']
packed=dest/'system-android13-candidate-20261114.raw.img.gz'
with packed.open('wb') as output:
    with gzip.GzipFile(filename='',mode='wb',compresslevel=6,fileobj=output,mtime=0) as compressor:
        with raw.open('rb') as source:shutil.copyfileobj(source,compressor,1024*1024)
# Verify every uncompressed byte of the backup, not just gzip's header/footer.
check=hashlib.sha256();count=0
with gzip.open(packed,'rb') as source:
    for data in iter(lambda:source.read(1024*1024),b''):
        check.update(data);count+=len(data)
assert check.hexdigest()==image['raw_image_sha256'] and count==image['raw_bytes']
boot_copy=dest/'boot-android13-candidate-20261114.img';shutil.copy2(image_dir/'boot.img',boot_copy)
verification=dest/'android13-candidate-offline-verification-20261114.zip'
with zipfile.ZipFile(verification,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for name in ('complete-image-verification.json','production-namespace-verification.json',
                 'complete-image-policy-verification.json','candidate-boot-verification.json',
                 'kernel-carryover-verification.json','complete-image-geometry.json',
                 'preserved-rom-verification.json'):
        z.write(audit/name,'verification/'+name)
    for name in ('filesystem-check.txt','filesystem-header.txt','candidate-init.mrvl.rc'):
        z.write(image_dir/name,name)
    for path in sorted(Path('/root/t110-android13/logs').glob('complete-image-*.log')):
        z.write(path,'logs/'+path.name)
    for path in sorted(Path('/root/t110-android13/logs').glob('complete-image-*-oom.txt')):
        z.write(path,'logs/'+path.name)
    fixture=Path(ns['fixture'])
    z.write(fixture/'namespace-run.log','logs/production-namespace.log')
    for path in sorted((fixture/'generated-linkerconfig').rglob('*')):
        if path.is_file():z.write(path,'linkerconfig/'+str(path.relative_to(fixture/'generated-linkerconfig')))
with zipfile.ZipFile(verification) as z:assert z.testzip() is None
records=[dict(name=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in (packed,boot_copy,verification)]
(dest/'SHA256SUMS-image-candidate.txt').write_text(''.join(x['sha256']+'  '+x['name']+'\n' for x in records))
result=dict(status='PASS_LOCAL_BACKUP_READBACK',files=records,raw_system_sha256=image['raw_image_sha256'],
            raw_system_bytes=image['raw_bytes'],online_verified=False,hardware_qualified=False,flashed=False)
(dest/'backup-manifest.json').write_text(json.dumps(result,indent=2)+'\n')
(dest/'README-CANDIDATE.md').write_text('''# SM-T110 Android13 engineering candidate — offline verification only

This is a complete userspace/boot candidate for the existing userdata-backed
read-only loop mechanism. The raw system MUST NOT be flashed to the tablet's
faulty physical SYSTEM partition. It is not a standard recovery-install ZIP.

Both image hashes, ext4 compatibility, actual namespace/library loading, audio
module/config selection and compiled policy passed offline checks. The boot
uses the working14.1 kernel's archive fix with identical13 configuration and GPU
module, new policy, exact GPU-node access/alias, retained memory/logging fixes,
and the corrected accelerated window path. The Canvas fallback remains available.

No tablet was flashed or rebooted to qualify this candidate. GPU rendering,
audio/microphone, touch, radio/navigation and suspend/wake still require a real
combined test. Live userdata free space must be checked before staging. Camera
and complete13 hardware functionality are not claimed. Google apps are not added
by this source build. This is not a public stable release or a security-qualified
production ROM. Keep the GitHub backup release unpublished.

The working14.1 ROM, rollback pair and original13 restoration capsules are kept
separately and unchanged. See source branch t110/android13-offline-audit-20261114,
development/android13-audit-20261114/phase4 for source and reproducible check tools.
''')
print(json.dumps(result,indent=2))
