"""Seal verified v15 system with unchanged, verified v23 boot inputs. No device IO."""
from pathlib import Path
import gzip, hashlib, json, shutil, struct

project=Path(__file__).resolve().parents[1]
system=project/'artifacts/lineage20-rom-v15'
previous=project/'artifacts/android13-full-v23'
boot=project/'artifacts/android13-full-v24'
contents=json.loads((project/'evidence/v15-startup-fixes-contents.json').read_text())
assert contents['status']=='PASS'
host=json.loads((system/'host-verification.json').read_text())
assert host['status']=='VERIFIED'
report=json.loads((system/'system-verification.json').read_text())
assert report['status']=='FIT_AND_EXT4_VERIFIED'
assert report['expanded_bytes']==1594884096
old_fs=json.loads((project/'artifacts/lineage20-rom-v13/system-verification.json').read_text())
assert report['ext4_features']==old_fs['ext4_features']
expected={line.split()[1]:line.split()[0] for line in (system/'SHA256SUMS').read_text().splitlines()}
with (system/'system.img').open('rb') as stream:
    sparse_sha=hashlib.file_digest(stream,'sha256').hexdigest()
assert sparse_sha==expected['system.img']
assert host['sha256']==expected['system.raw.img']

sha=lambda data:hashlib.sha256(data).hexdigest()
provenance=json.loads((previous/'provenance.json').read_text())
payload=(previous/'KERNEL.img').read_bytes()
assert len(payload)==16777216
assert sha(payload)==provenance['full_boot_sha256']=='811a3dbfa08e83005236def1b86eae3495bca49f5c1f13a43e82c804d9c195b5'
assert payload[:8]==b'ANDROID!'
ksize=struct.unpack_from('<I',payload,8)[0]
rsize=struct.unpack_from('<I',payload,16)[0]
page=struct.unpack_from('<I',payload,36)[0]
assert page==2048
assert sha(payload[page:page+ksize])==provenance['kernel_sha256']
start=page+(ksize+page-1)//page*page
archive=gzip.decompress(payload[start:start+rsize])
files={}; offset=0
while offset+110<=len(archive):
    header=archive[offset:offset+110]; assert header[:6]==b'070701'
    fields=[int(header[i:i+8],16) for i in range(6,110,8)]
    size,namesize=fields[6],fields[11]
    name=archive[offset+110:offset+110+namesize-1].decode()
    offset=(offset+110+namesize+3)&~3
    files[name]=archive[offset:offset+size]; offset=(offset+size+3)&~3
    if name=='TRAILER!!!': break
assert files['init.environ.rc']==(project/'work/core-boot/init.environ.rc').read_bytes()
assert files['init.mrvl.rc']==(project/'work/core-boot/init.mrvl.rc').read_bytes()
assert sha(files['t110-preload-policy'])==provenance['bootstrap_policy_sha256']
assert sha(files['lib/modules/galcore.ko'])==provenance['module_sha256']

assert not boot.exists(),'Never overwrite an existing candidate or its hardware result'
boot.mkdir()
for name in ['boot.img','KERNEL.img']:
    shutil.copyfile(previous/name,boot/name)
    assert (boot/name).read_bytes()==(previous/name).read_bytes()
provenance.update(status='VERIFIED_UNCHANGED_BOOT_INPUTS',reused_from='../android13-full-v23',
                  reason='All v24 startup corrections are in system; kernel and ramdisk unchanged')
(boot/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
result=dict(status='OFFLINE_VERIFIED_NOT_BOOT_TESTED',system_artifact='../lineage20-rom-v15/system.raw.img',
    system_sha256=host['sha256'],system_md5=host['md5'],system_bytes=host['bytes'],
    sparse_system_sha256=sparse_sha,
    boot_sha256=provenance['full_boot_sha256'],boot_md5=provenance['full_boot_md5'],
    bootstrap_policy_sha256=provenance['bootstrap_policy_sha256'],
    hardware_tested=False,hardware_validated=False,boot_completed=False,
    hardware_boots_this_pass=0,flashes_this_pass=0,tablet_access_this_pass=False,
    boot_inputs_changed=False,previous_hardware_result='../../hardware-tests/20261106-211758-core/result.json',
    fixes=['Standard ART APEX instead of auto-selected debug ART',
           'Ahead-of-time compilation of first-boot permission/UI applications',
           'T110-only declared/ready GNSS probing; no absent-HAL waits',
           'SO_PASSCRED set on accepted lmkd sockets; sender validation retained'],
    checks=['ARM system image build','ASan/UBSan host GNSS and credential regressions',
            'Actual filesystem contains compiled changes, release ART and speed-compiled apps',
            'Ext4 integrity, SYSTEM partition fit, source/build/export hashes',
            'Reused boot unpacked and matched to current init/kernel/module/policy'],
    runtime_limits=['Full boot/UI/touch and latency improvement need a later authorized hardware test',
                    'GPS provider remains unported; unavailable GPS must not block startup',
                    'Existing audio fallback and other unported hardware remain unchanged'])
(boot/'system-pair.json').write_text(json.dumps(result,indent=2)+'\n')
(boot/'SHA256SUMS').write_text(''.join(sha((boot/n).read_bytes())+'  '+n+'\n' for n in ['boot.img','KERNEL.img']))
print(json.dumps(result,indent=2))
