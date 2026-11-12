from pathlib import Path
import datetime,hashlib,json
p=Path(__file__).resolve().parents[1];a=p/'artifacts/lineage20-rom-v25'
checks=json.loads((p/'evidence/offline-v35/contents.json').read_text());assert checks['status']=='PASS'
fit=json.loads((a/'system-verification.json').read_text());assert fit['status']=='FIT_AND_EXT4_VERIFIED' and fit['fsck_exit']==0
assert 'build completed successfully' in (a/'system-build.log').read_text(errors='replace')
source=a/'system.raw.img';digests=[hashlib.sha256(),hashlib.md5()]
with source.open('rb') as stream:
    while block:=stream.read(8*1024*1024):
        for digest in digests:digest.update(block)
sha,md5=[h.hexdigest() for h in digests]
assert sha==fit['sha256']==checks['system_sha256'] and source.stat().st_size==1594884096
prov=json.loads((p/'artifacts/android13-full-v28/provenance.json').read_text())
assert hashlib.sha256((p/'artifacts/android13-full-v28/KERNEL.img').read_bytes()).hexdigest()==checks['boot_sha256']==prov['full_boot_sha256']
host=dict(status='VERIFIED',sha256=sha,md5=md5,bytes=source.stat().st_size,build_exit=0,verified_at=datetime.datetime.now().astimezone().isoformat())
(a/'host-verification.json').write_text(json.dumps(host,indent=2)+'\n',encoding='utf-8')
pair=dict(status='OFFLINE_VERIFIED_NOT_BOOT_TESTED',system_artifact='system.raw.img',boot_artifact='../android13-full-v28/KERNEL.img',system_sha256=sha,system_md5=md5,system_bytes=source.stat().st_size,boot_sha256=checks['boot_sha256'],boot_md5=checks['boot_md5'],existing_boot_reused=True,hardware_tested=False,hardware_validated=False,full_boot_passed=False,fixes=['Physical Home and Recents mappings','Physical navigation suppressed when touch navigation enabled','Expose Lineage navigation-mode switch','SystemUI respects diagnostic opt-out','Rotate in cached RAM before streaming to display','Reuse only idle EGL swap spare buffers','Settings speed precompilation'],limits=['Software window rendering remains','Frame-rate improvement requires hardware measurement','Other unported hardware remains incomplete'])
(a/'rom-pair.json').write_text(json.dumps(pair,indent=2)+'\n',encoding='utf-8');print(json.dumps(pair,indent=2))
