"""Independently verify packaged Android boot header, CPIO, and v28 contents."""
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

old = unpack(p/'artifacts/android13-full-v27/KERNEL.img')
new = unpack(p/'artifacts/android13-full-v28/KERNEL.img')
dest = p/'artifacts/android13-full-v28'
pair = json.loads((dest/'system-pair.json').read_text())
prov = json.loads((dest/'provenance.json').read_text())
kernel = p/'artifacts/kernel-display-i2c'
assert sha(new[0]) == pair['boot_sha256'] == prov['full_boot_sha256']
assert hashlib.md5(new[0]).hexdigest() == pair['boot_md5']
assert new[1] == (kernel/'zImage').read_bytes() and old[1] != new[1]
assert old[4] == new[4] and set(old[3]) == set(new[3])
changed = sorted(k for k in old[3] if old[3][k] != new[3][k])
assert set(changed).issubset({'lib/modules/galcore.ko'})
assert new[3]['lib/modules/galcore.ko'] == (kernel/'galcore.ko').read_bytes()
assert sha(new[3]['lib/modules/galcore.ko']) == pair['module_sha256']
for name, digest in prov['unchanged_ramdisk_files'].items():
    assert sha(new[3][name]) == digest
assert sha(new[3]['t110-preload-policy']) == pair['bootstrap_policy_sha256']
assert new[3]['t110-preload-policy'] == (p/'evidence/offline-v26/embedded-policy.bin').read_bytes()
assert new[0][:new[5]] == (dest/'boot.img').read_bytes()
assert new[2] == (dest/'ramdisk.cpio.gz').read_bytes()
assert new[0][12:16] == old[0][12:16] and new[0][20:576] == old[0][20:576]
assert 'CONFIG_EXT4_FS_POSIX_ACL=y' in (kernel/'kernel.config').read_text()
result = dict(status='PASS', boot_sha256=sha(new[0]), boot_md5=pair['boot_md5'],
              changed_ramdisk_files=changed, kernel_changed=True,
              cpio_metadata_unchanged=True, embedded_policy_matches_system=True,
              header_id_verified=True, partition_bytes=len(new[0]),
              android_boots=0, tablet_access=False)
(p/'evidence/offline-v34/boot-verification.json').write_text(json.dumps(result, indent=2)+'\n')
pair['status'] = 'OFFLINE_VERIFIED_NOT_BOOT_TESTED'
(dest/'system-pair.json').write_text(json.dumps(pair, indent=2)+'\n')
print(json.dumps(result, indent=2))
