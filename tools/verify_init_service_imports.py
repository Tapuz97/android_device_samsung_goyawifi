"""Check the import graph in the actual boot image against actual system RCs."""
from pathlib import Path
import gzip, hashlib, json, re, struct, subprocess, tempfile

BASE = Path('/root/t110-lineage14')
ART = BASE / 'artifacts/lineage14-first-build'
boot = (ART / 'boot.img').read_bytes()
kernel_size, = struct.unpack_from('<I', boot, 8)
ramdisk_size, = struct.unpack_from('<I', boot, 16)
page, = struct.unpack_from('<I', boot, 36)
start = page + (kernel_size + page - 1) // page * page
raw = gzip.decompress(boot[start:start + ramdisk_size])
files = {}
offset = 0
while True:
    assert raw[offset:offset+6] == b'070701'
    fields = [int(raw[i:i+8], 16) for i in range(offset+6, offset+110, 8)]
    size, namesize = fields[6], fields[11]
    name = raw[offset+110:offset+110+namesize-1].decode()
    offset = (offset+110+namesize+3) & ~3
    body = raw[offset:offset+size]
    offset = (offset+size+3) & ~3
    if name == 'TRAILER!!!':
        break
    files['/' + name] = body

with tempfile.TemporaryDirectory(prefix='t110-init-graph-') as temp:
    result = subprocess.run(['debugfs', '-R', 'rdump /etc/init ' + temp,
                             str(ART / 'system.raw.img')], capture_output=True, text=True)
    rc_files = list(Path(temp).rglob('*.rc'))
    assert len(rc_files) >= 30, result.stderr
    for path in rc_files:
        files['/system/etc/init/' + path.name] = path.read_bytes()

def graph(source):
    seen, services = set(), {}
    def visit(path):
        if path in seen:
            return
        seen.add(path)
        if path == '/system/etc/init':
            for name in sorted(source):
                if name.startswith(path + '/'):
                    visit(name)
            return
        assert path in source, 'Unresolved import: ' + path
        imports = []
        for line in source[path].decode().splitlines():
            if line.startswith('import '):
                target = line.split()[1].replace('${ro.hardware}', 'mrvl').replace('${ro.zygote}', 'zygote32')
                imports.append(target)
            elif line.startswith('service '):
                parts = line.split()
                assert parts[1] not in services, 'Duplicate service: ' + parts[1]
                services[parts[1]] = {'file': path, 'executable': parts[2]}
        for target in imports:
            visit(target)
    visit('/init.rc')
    return seen, services

required = {'vold', 'logd', 'debuggerd', 'servicemanager', 'surfaceflinger',
            'zygote', 'adbd', 'bootanim', 'audioserver', 'cameraserver', 'netd',
            'installd', 'keystore', 'gatekeeperd', 'lmkd'}
seen, services = graph(files)
assert required <= services.keys(), 'Missing services: ' + str(required-services.keys())
assert b'socket cryptd ' in files[services['vold']['file']]
assert b'    start vold\n' in files['/init.rc']
assert files['/init.rc'].index(b'    start vold\n') < files['/init.rc'].index(b'    init_user0\n')
# Regression: the previous configuration must reproduce the missing-service graph.
old = dict(files)
old['/init.mrvl.rc'] = old['/init.mrvl.rc'].replace(b'import /system/etc/init\n', b'')
_, old_services = graph(old)
assert {'vold', 'logd', 'surfaceflinger'}.isdisjoint(old_services)
report = {'status': 'PASS', 'scope': 'Actual boot/system import graph; not hardware boot proof',
          'boot_sha256': hashlib.sha256(boot).hexdigest(),
          'rc_files_loaded': sorted(seen), 'services': services,
          'previous_configuration_regression': 'Missing vold/logd/surfaceflinger reproduced'}
(ART / 'init-service-verification.json').write_text(json.dumps(report, indent=2)+'\n')
print('PASS:', len(services), 'native services reachable; prior omission reproduced.')
