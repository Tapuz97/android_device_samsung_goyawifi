"""Verify actual linked display code, config and modules before packaging."""
from pathlib import Path
import hashlib, json, shutil, subprocess
b = Path('/root/t110-build')
p = Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
src, out = b/'kernel-display-i2c', b/'out-display-i2c'
e = p/'evidence/offline-v34'
dest = p/'artifacts/kernel-display-i2c'
sha = lambda data: hashlib.sha256(data).hexdigest()
record = json.loads((e/'display-i2c-source.json').read_text())
assert sha((src/record['source']).read_bytes()) == record['after_sha256']
assert sha((b/'kernel-binder-secctx'/record['source']).read_bytes()) == record['before_sha256']
assert (out/'.config').read_bytes() == (p/'artifacts/kernel-storage-acl/kernel.config').read_bytes()
obj = record['source'].removesuffix('.c')+'.o'
nm = str(b/'toolchain/bin/arm-eabi-nm')
old_symbols = subprocess.check_output([nm, '-u', str(b/'out-storage-acl'/obj)], text=True)
new_symbols = subprocess.check_output([nm, '-u', str(out/obj)], text=True)
assert 'i2c1_pin_changed' in old_symbols and 'i2c1_pin_changed' not in new_symbols
symbols = subprocess.check_output([nm, str(out/'vmlinux')], text=True)
assert all(any(line.split()[-1] == symbol for line in symbols.splitlines())
           for symbol in ['ext4_set_acl', 'ext4_get_acl', 'vx5b3d_power', 'bt532_ts_suspend'])
cmd = (out/Path(obj).parent/('.'+Path(obj).name+'.cmd')).read_text()
assert 'kernel-display-i2c' in cmd, 'Object must compile from the patched source tree'
modules = list(out.rglob('galcore.ko'))
assert len(modules) == 1
log = (b/'logs/display-i2c-build.log').read_text(errors='replace')
assert 'Kernel: arch/arm/boot/zImage is ready' in log and 'error:' not in log
assert (out/'arch/arm/boot/zImage').read_bytes() != (p/'artifacts/kernel-storage-acl/zImage').read_bytes()
dest.mkdir(exist_ok=False)
files = {}
for name, source in {'zImage':out/'arch/arm/boot/zImage', 'galcore.ko':modules[0],
                     'kernel.config':out/'.config', 'display-power.o':out/obj,
                     'System.map':out/'System.map', 'build.log':b/'logs/display-i2c-build.log'}.items():
    shutil.copyfile(source, dest/name)
    files[name] = dict(bytes=source.stat().st_size, sha256=sha(source.read_bytes()))
result = dict(status='COMPILED_OFFLINE_VERIFIED_NOT_BOOT_TESTED', files=files,
              parent='artifacts/kernel-storage-acl/provenance.json',
              configuration_unchanged=True, display_i2c_remux_removed_from_compiled_object=True,
              preserved_acl_and_touch_pm=True, source_change=record,
              hardware_tested=False, hardware_validated=False)
(dest/'provenance.json').write_text(json.dumps(result, indent=2)+'\n')
(e/'kernel-verification.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result, indent=2))
