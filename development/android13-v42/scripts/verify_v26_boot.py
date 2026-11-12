"""Independently verify packaged Android boot header, CPIO, and v26 contents."""
import gzip
import hashlib
import json
from pathlib import Path
import struct

p = Path(__file__).resolve().parents[1]
sha = lambda b: hashlib.sha256(b).hexdigest()

def unpack(path):
    b = path.read_bytes()
    assert len(b) == 16777216 and b[:8] == b'ANDROID!'
    ks, ka, rs, ra, ss, sa, tags, page, dt = struct.unpack_from('<9I', b, 8)
    assert page == 2048 and ss == dt == 0
    roundup = lambda size: ((size + page - 1)//page)*page
    kernel = b[page:page+ks]
    off = page + roundup(ks)
    ramdisk = b[off:off+rs]
    end = off + roundup(rs)
    assert not any(b[end:])
    digest = hashlib.sha1()
    for blob in (kernel, ramdisk, b''):
        digest.update(blob)
        digest.update(struct.pack('<I', len(blob)))
    assert b[576:608] == digest.digest() + bytes(12)
    raw, off, files, metadata = gzip.decompress(ramdisk), 0, {}, {}
    while True:
        h = raw[off:off+110]
        assert h[:6] == b'070701'
        f = [int(h[i:i+8], 16) for i in range(6, 110, 8)]
        namesize, size = f[11], f[6]
        name = raw[off+110:off+110+namesize-1].decode()
        assert raw[off+110+namesize-1] == 0 and name not in files
        off = (off+110+namesize+3)//4*4
        payload = raw[off:off+size]
        assert len(payload) == size
        off = (off+size+3)//4*4
        if name == 'TRAILER!!!':
            break
        files[name], metadata[name] = payload, f[:6]+f[7:]
    assert not any(raw[off:])
    return b, kernel, ramdisk, files, metadata, end

old = unpack(p/'artifacts/android13-full-v25/KERNEL.img')
new = unpack(p/'artifacts/android13-full-v26/KERNEL.img')
pair = json.loads((p/'artifacts/android13-full-v26/system-pair.json').read_text())
prov = json.loads((p/'artifacts/android13-full-v26/provenance.json').read_text())
assert sha(new[0]) == pair['boot_sha256'] == prov['full_boot_sha256']
assert hashlib.md5(new[0]).hexdigest() == pair['boot_md5']
assert old[1] == new[1] and sha(new[1]) == pair['kernel_sha256']
assert old[4] == new[4] and set(old[3]) == set(new[3])
changed = sorted(k for k in old[3] if old[3][k] != new[3][k])
assert changed == ['init.mrvl.rc', 't110-preload-policy', 'ueventd.mrvl.rc']
for name, digest in prov['changed_ramdisk_files'].items():
    assert sha(new[3][name]) == digest
for name, digest in prov['unchanged_ramdisk_files'].items():
    assert sha(new[3][name]) == digest
for node in ('ion', 'galcore'):
    assert f'chmod 0666 /dev/{node}'.encode() in new[3]['init.mrvl.rc']
    assert f'/dev/{node} 0666 system graphics'.encode() in new[3]['ueventd.mrvl.rc']
assert sha(new[3]['t110-preload-policy']) == pair['bootstrap_policy_sha256']
assert new[3]['t110-preload-policy'] == (p/'evidence/offline-v26/embedded-policy.bin').read_bytes()
assert sha(new[3]['lib/modules/galcore.ko']) == pair['module_sha256']
assert new[0][:new[5]] == (p/'artifacts/android13-full-v26/boot.img').read_bytes()
assert new[2] == (p/'artifacts/android13-full-v26/ramdisk.cpio.gz').read_bytes()
result = dict(status='PASS', boot_sha256=sha(new[0]), boot_md5=pair['boot_md5'],
              changed_files=changed, kernel_and_module_unchanged=True,
              cpio_metadata_unchanged=True, embedded_policy_matches_system=True,
              header_id_verified=True, partition_bytes=len(new[0]),
              android_boots=0, tablet_access=False)
(p/'evidence/offline-v26/boot-verification.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result, indent=2))
