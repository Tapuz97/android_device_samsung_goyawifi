"""Seal offline-verified v25 boot/v16 system and document limits."""
from pathlib import Path
import gzip,hashlib,json,struct
p=Path(__file__).resolve().parents[1]; system=p/'artifacts/lineage20-rom-v16'; boot=p/'artifacts/android13-full-v25'
read=lambda f:json.loads(f.read_text())
sha=lambda data:hashlib.sha256(data).hexdigest()
host=read(system/'host-verification.json'); fs=read(system/'system-verification.json')
assert host['status']=='VERIFIED' and fs['status']=='FIT_AND_EXT4_VERIFIED'
assert read(p/'evidence/v16-startup-fixes-contents.json')['status']=='PASS'
assert read(p/'evidence/offline-v25/systemui-dex-verification.json')['status']=='PASS'
assert read(p/'evidence/offline-v25/regressions.json')['status']=='PASS'
assert fs['ext4_features']==read(p/'artifacts/lineage20-rom-v15/system-verification.json')['ext4_features']
checks={line.split()[1]:line.split()[0] for line in (system/'SHA256SUMS').read_text().splitlines()}
assert checks['system.raw.img']==host['sha256']
with (system/'system.img').open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==checks['system.img']
meta=read(boot/'provenance.json'); data=(boot/'KERNEL.img').read_bytes()
assert len(data)==16777216 and sha(data)==meta['full_boot_sha256']
k=struct.unpack_from('<I',data,8)[0];r=struct.unpack_from('<I',data,16)[0];page=struct.unpack_from('<I',data,36)[0]; assert page==2048
kernel=data[page:page+k]; assert sha(kernel)==meta['kernel_sha256']
start=page+(k+page-1)//page*page;rd=data[start:start+r];assert sha(rd)==meta['ramdisk_sha256']
assert data[:8]==b'ANDROID!'; h=hashlib.sha1()
for payload in [kernel,rd,b'']:h.update(payload);h.update(struct.pack('<I',len(payload)))
assert data[576:608]==h.digest()+bytes(12)
raw=gzip.decompress(rd);i=0;files={}
while i+110<=len(raw):
 head=raw[i:i+110];assert head[:6]==b'070701'
 fields=[int(head[j:j+8],16) for j in range(6,110,8)];size,ns=fields[6],fields[11]
 name=raw[i+110:i+110+ns-1].decode();i=(i+110+ns+3)&~3
 files[name]=raw[i:i+size];i=(i+size+3)&~3
 if name=='TRAILER!!!':break
assert sha(files['lib/modules/galcore.ko'])==meta['module_sha256']
for name,digest in meta['unchanged_ramdisk_files'].items():assert sha(files[name])==digest,name
result=dict(status='OFFLINE_VERIFIED_NOT_BOOT_TESTED',system_artifact='../lineage20-rom-v16/system.raw.img',
 system_sha256=host['sha256'],system_md5=host['md5'],system_bytes=host['bytes'],sparse_system_sha256=checks['system.img'],
 boot_sha256=meta['full_boot_sha256'],boot_md5=meta['full_boot_md5'],kernel_sha256=meta['kernel_sha256'],
 module_sha256=meta['module_sha256'],bootstrap_policy_sha256=meta['bootstrap_policy_sha256'],
 hardware_tested=False,hardware_validated=False,boot_completed=False,full_boot_passed=False,
 hardware_boots_this_pass=0,flashes_this_pass=0,tablet_access_this_pass=False,
 fixes=['Kernel Binder sender security-context delivery for keystore permission checks',
        'SystemUI handles null AppOps package list without aborting KeyguardService startup'],
 checks=['Full ARM kernel/module and system builds','Host extracted-source regressions and Binder UAPI',
         'Actual SystemUI DEX guard and precompiled APK/OAT match','Keystore/framework/services bytes unchanged',
         'Ext4 integrity, partition fit, Linux/Windows hashes, unpacked matching boot/module'],
 limits=['No kernel runtime or hardware test this pass; full unlock/UI remains unverified',
         'Existing GPS/audio/other unported hardware and captured media codec failure remain',
         'Snapshot SID applies to ordinary flagged Binder nodes; extended context-manager registration remains unsupported'])
(boot/'system-pair.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
