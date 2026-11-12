"""Pair the verified v17 system with corrected permissions/policy in v25 BOOT."""
from pathlib import Path
import gzip
import hashlib
import json
import struct

p = Path(__file__).resolve().parents[1]
old = p/'artifacts/android13-full-v25'
dest = p/'artifacts/android13-full-v26'
assert json.loads((p/'evidence/offline-v26/contents.json').read_text())['status'] == 'PASS'
host = json.loads((p/'artifacts/lineage20-rom-v17/host-verification.json').read_text())
assert host['status'] == 'VERIFIED'
sha = lambda data: hashlib.sha256(data).hexdigest()
image = (old/'KERNEL.img').read_bytes()
oldprov = json.loads((old/'provenance.json').read_text())
assert sha(image) == oldprov['full_boot_sha256'] == 'a63c1b36d9ce32aeae48a22b7e5b8e3dc5aaf06184fda3b420e2f5cf271450b6'
ksize = struct.unpack_from('<I', image, 8)[0]
rsize = struct.unpack_from('<I', image, 16)[0]
page = struct.unpack_from('<I', image, 36)[0]
assert page == 2048
align = lambda data: data + bytes(-len(data) % page)
kernel = image[page:page+ksize]
assert sha(kernel) == oldprov['kernel_sha256']
start = page + len(align(kernel))
rd = gzip.decompress(image[start:start+rsize])
replacements = {
    'init.mrvl.rc': (p/'work/core-boot/init.mrvl.rc').read_bytes(),
    'ueventd.mrvl.rc': b'/dev/galcore 0666 system graphics\n/dev/ion 0666 system graphics\n',
    't110-preload-policy': (p/'work/core-boot/logging-test-policy').read_bytes(),
}
assert b'chmod 0666 /dev/galcore' in replacements['init.mrvl.rc']
assert b'chmod 0666 /dev/ion' in replacements['init.mrvl.rc']
checked = json.loads((p/'evidence/offline-v26/contents.json').read_text())
assert sha(replacements['t110-preload-policy']) == checked['bootstrap_policy_sha256']
offset = 0
entries, files, replaced = [], {}, set()
while offset + 110 <= len(rd):
    header = bytearray(rd[offset:offset+110])
    assert header[:6] == b'070701'
    fields = [int(header[i:i+8],16) for i in range(6,110,8)]
    length,namesize = fields[6],fields[11]
    namebytes = rd[offset+110:offset+110+namesize]
    name = namebytes[:-1].decode()
    offset = (offset+110+namesize+3)&~3
    data = rd[offset:offset+length]
    offset = (offset+length+3)&~3
    files[name] = data
    if name in replacements:
        data = replacements[name]
        replaced.add(name)
        header[54:62] = f'{len(data):08x}'.encode()
    record = bytes(header)+namebytes
    record += bytes(-len(record)%4)
    record += data
    record += bytes(-len(record)%4)
    entries.append(record)
    if name == 'TRAILER!!!': break
assert replaced == set(replacements)
assert files['init.environ.rc'] == (p/'work/core-boot/init.environ.rc').read_bytes()
assert sha(files['lib/modules/galcore.ko']) == oldprov['module_sha256']
raw = b''.join(entries)
raw += bytes(-len(raw)%512)
newrd = gzip.compress(raw,mtime=0)
header = bytearray(image[:page])
struct.pack_into('<I',header,16,len(newrd))
digest = hashlib.sha1()
for data in [kernel,newrd,b'']:
    digest.update(data)
    digest.update(struct.pack('<I',len(data)))
header[576:608] = digest.digest()+bytes(12)
boot = bytes(header)+align(kernel)+align(newrd)
assert len(boot) < 16777216
full = boot.ljust(16777216,b'\0')
dest.mkdir(exist_ok=False)
for name,data in {'boot.img':boot,'KERNEL.img':full,'ramdisk.cpio.gz':newrd}.items():
    (dest/name).write_bytes(data)
oldprov.update(status='OFFLINE_VERIFIED_NOT_BOOT_TESTED',
    ramdisk_sha256=sha(newrd),full_boot_sha256=sha(full),
    full_boot_md5=hashlib.md5(full).hexdigest(),boot_image_bytes=len(boot),
    bootstrap_policy_sha256=sha(replacements['t110-preload-policy']),
    parent='../android13-full-v25',
    modifications=['GPU/ION node modes for app access','Matching device SELinux policy'],
    changed_ramdisk_files={name:sha(data) for name,data in replacements.items()},
    unchanged_ramdisk_files={name:sha(data) for name,data in files.items()
                            if name not in replacements and name!='TRAILER!!!'})
(dest/'provenance.json').write_text(json.dumps(oldprov,indent=2)+'\n')
(dest/'SHA256SUMS').write_text(''.join(sha((dest/name).read_bytes())+'  '+name+'\n'
    for name in ['boot.img','KERNEL.img','ramdisk.cpio.gz']))
pair = dict(status='OFFLINE_VERIFIED_NOT_BOOT_TESTED',
    system_artifact='../lineage20-rom-v17/system.raw.img',
    system_sha256=host['sha256'],system_md5=host['md5'],system_bytes=host['bytes'],
    boot_sha256=sha(full),boot_md5=hashlib.md5(full).hexdigest(),
    kernel_sha256=sha(kernel),module_sha256=oldprov['module_sha256'],
    bootstrap_policy_sha256=oldprov['bootstrap_policy_sha256'],
    hardware_tested=False,hardware_validated=False,boot_completed=False,
    full_boot_passed=False,hardware_boots_this_pass=0,flashes_this_pass=0,
    fixes=['Codec allocator error-state metadata','App EGL and gralloc process initialization',
           'GPU/ION DAC and scoped legacy gralloc ION write access'],
    limits=['Compiled and host-tested; hardware behavior not yet established',
            'Other unported hardware remains outside this correction'])
(dest/'system-pair.json').write_text(json.dumps(pair,indent=2)+'\n')
print(json.dumps(pair,indent=2))
