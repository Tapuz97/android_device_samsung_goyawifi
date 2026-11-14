from pathlib import Path
import gzip
import hashlib
import json
import struct

source = Path('/root/t110-lineage14/reference/current-private/artifacts/android13-boot-v48/KERNEL.img')
blob = source.read_bytes()
assert blob[:8] == b'ANDROID!'
kernel_size, ramdisk_size, page = (struct.unpack_from('<I', blob, p)[0] for p in (8,16,36))
assert page in (2048,4096)
offset = page + ((kernel_size+page-1)//page)*page
data = gzip.decompress(blob[offset:offset+ramdisk_size])
records = []; selected = {}; cursor = 0
while True:
    assert data[cursor:cursor+6] in (b'070701',b'070702')
    fields = [int(data[n:n+8],16) for n in range(cursor+6,cursor+110,8)]
    name = data[cursor+110:cursor+110+fields[11]-1].decode()
    cursor = (cursor+110+fields[11]+3)&~3
    body = data[cursor:cursor+fields[6]]
    cursor = (cursor+fields[6]+3)&~3
    if name == 'TRAILER!!!': break
    records.append(dict(name=name, mode=oct(fields[1]), bytes=len(body), sha256=hashlib.sha256(body).hexdigest()))
    if (name.endswith('.rc') or name.endswith('.prop')) and (name.startswith('init') or name.startswith('default')):
        selected[name] = body.decode(errors='replace')
out = Path('/root/t110-android13-audit')
(out/'preserved-android13-boot.json').write_text(json.dumps(dict(path=str(source),
    sha256=hashlib.sha256(blob).hexdigest(), kernel_sha256=hashlib.sha256(blob[page:page+kernel_size]).hexdigest(),
    kernel_bytes=kernel_size, page=page, ramdisk_bytes=ramdisk_size, files=records, init_files=selected), indent=2)+'\n')
for name,text in selected.items():
    print(name+'\n'+text[:10000])
print('Saved immutable Android13 boot contents and hashes; no image changed.')
