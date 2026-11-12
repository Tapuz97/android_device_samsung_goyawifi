"""Check exported boot/system pairing without accessing a device."""
from pathlib import Path
import gzip,hashlib,json,struct
project=Path(__file__).resolve().parents[1]
boot=project/'artifacts/android13-full-v22'
system=project/'artifacts/lineage20-rom-v12'
provenance=json.loads((boot/'provenance.json').read_text())
host=json.loads((system/'host-verification.json').read_text())
assert host['status']=='VERIFIED'
payload=(boot/'KERNEL.img').read_bytes()
assert len(payload)==16777216
assert hashlib.sha256(payload).hexdigest()==provenance['full_boot_sha256']
assert payload[:8]==b'ANDROID!'
kernel_size=struct.unpack_from('<I',payload,8)[0]
ramdisk_size=struct.unpack_from('<I',payload,16)[0]
page=struct.unpack_from('<I',payload,36)[0]
assert page==2048
assert hashlib.sha256(payload[page:page+kernel_size]).hexdigest()==provenance['kernel_sha256']
start=page+(kernel_size+page-1)//page*page
archive=gzip.decompress(payload[start:start+ramdisk_size])
files={}; offset=0
while offset+110<=len(archive):
    header=archive[offset:offset+110];assert header[:6]==b'070701'
    fields=[int(header[i:i+8],16) for i in range(6,110,8)]
    size=fields[6];namesize=fields[11]
    name=archive[offset+110:offset+110+namesize-1].decode()
    offset=(offset+110+namesize+3)&~3
    files[name]=archive[offset:offset+size]
    offset=(offset+size+3)&~3
    if name=='TRAILER!!!': break
rc=files['init.mrvl.rc']
assert rc==(project/'work/core-boot/init.mrvl.rc').read_bytes()
assert b'on post-fs-data && property:ro.crypto.state=unencrypted\n    trigger nonencrypted' in rc
assert hashlib.sha256(files['t110-preload-policy']).hexdigest()==provenance['bootstrap_policy_sha256']
assert hashlib.sha256(files['lib/modules/galcore.ko']).hexdigest()==provenance['module_sha256']
kernel=json.loads((project/'artifacts/kernel-alarm/provenance.json').read_text())
assert provenance['kernel_sha256']==kernel['files']['zImage']['sha256']
assert provenance['module_sha256']==kernel['files']['galcore.ko']['sha256']
assert b'T110_ALARM_REGRESSION_PASS' in (project/'evidence/qemu-alarm-test.log').read_bytes()
contents=json.loads((project/'evidence/v12-combined-fixes-contents.json').read_text())
assert contents['status']=='PASS'
result=dict(status='OFFLINE_VERIFIED_NOT_BOOT_TESTED',
    system_artifact='../lineage20-rom-v12/system.raw.img',system_sha256=host['sha256'],
    system_md5=host['md5'],system_bytes=host['bytes'],
    boot_sha256=provenance['full_boot_sha256'],boot_md5=provenance['full_boot_md5'],
    bootstrap_policy_sha256=provenance['bootstrap_policy_sha256'],
    hardware_tested=False,hardware_validated=False,boot_completed=False,
    hardware_boots_this_pass=0,flashes_this_pass=0,
    fixes=['Kernel alarm and boottime timerfd support with CAP_WAKE_ALARM',
           'GLES compositor with FBO resolve/finish before target handoff',
           'PXA ION synchronization before CPU scanout read',
           'Disable invalid Vivante graphics preloading in zygote'],
    checks=['System fits original SYSTEM size; e2fsck clean; export hashes match',
            'Actual image contains new composer, matching libui, installd and Health HAL',
            'Actual boot ramdisk contains startup fix and pinned kernel/module/policy'])
(boot/'system-pair.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
