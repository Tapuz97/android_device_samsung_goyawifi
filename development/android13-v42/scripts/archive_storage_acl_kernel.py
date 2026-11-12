"""Archive the ACL-enabled kernel with exact configuration and linked-code checks."""
from pathlib import Path
import difflib
import hashlib
import json
import shutil
import subprocess

b = Path('/root/t110-build')
p = Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
src, out = b/'kernel-binder-secctx', b/'out-storage-acl'
dest = p/'artifacts/kernel-storage-acl'
evidence = p/'evidence/offline-v28'
evidence.mkdir(exist_ok=True)
old = (p/'artifacts/kernel-binder-secctx/kernel.config').read_text()
new = (out/'.config').read_text()
assert new == old.replace('# CONFIG_EXT4_FS_POSIX_ACL is not set', 'CONFIG_EXT4_FS_POSIX_ACL=y')
patch = ''.join(difflib.unified_diff(old.splitlines(True), new.splitlines(True), 'a/kernel.config', 'b/kernel.config'))
(p/'patches/0052-kernel-ext4-posix-acl.config.patch').write_text(patch)
symbols = subprocess.check_output([str(b/'toolchain/bin/arm-eabi-nm'),str(out/'vmlinux')], text=True)
required = ['ext4_set_acl', 'ext4_get_acl', 'ext4_init_acl', 'ext4_acl_chmod',
            'ext4_xattr_acl_default_handler', 'ext4_xattr_acl_access_handler']
lines = symbols.splitlines()
for symbol in required:
    assert any(line.split()[-1] == symbol for line in lines), symbol
(evidence/'linked-acl-symbols.txt').write_text('\n'.join(line for line in lines if line.split()[-1] in required)+'\n')
assert (out/'fs/ext4/acl.o').is_file()
assert (src/'fs/ext4/super.c').read_text().count('set_opt(sb, POSIX_ACL);') == 1
modules = list(out.rglob('galcore.ko'))
assert len(modules) == 1
assert 'error:' not in (b/'logs/storage-acl-build.log').read_text()
dest.mkdir(exist_ok=False)
sha = lambda data: hashlib.sha256(data).hexdigest()
files = {}
for name, path in {'zImage':out/'arch/arm/boot/zImage', 'galcore.ko':modules[0],
                   'kernel.config':out/'.config', 'build.log':b/'logs/storage-acl-build.log',
                   'acl.o':out/'fs/ext4/acl.o', 'System.map':out/'System.map'}.items():
    shutil.copyfile(path, dest/name)
    data = path.read_bytes()
    files[name] = dict(bytes=len(data), sha256=sha(data))
source_hashes = {}
for name in ['fs/ext4/acl.c','fs/ext4/xattr.c','fs/ext4/super.c','fs/ext4/Makefile',
             'drivers/staging/android/binder.c','drivers/staging/android/uapi/binder.h']:
    source_hashes[name] = sha((src/name).read_bytes())
for name, hashes in json.loads((p/'artifacts/kernel-binder-secctx/provenance.json').read_text())['source_files'].items():
    assert source_hashes[name] == hashes['after']
result = dict(status='COMPILED_OFFLINE_VERIFIED_NOT_BOOT_TESTED', files=files,
              parent='artifacts/kernel-binder-secctx/provenance.json',
              configuration_changes={'CONFIG_EXT4_FS_POSIX_ACL':['n','y']},
              source_files_unchanged=True, source_files=source_hashes,
              acl_code_linked=True, acl_enabled_by_default=True,
              hardware_tested=False, hardware_validated=False)
(dest/'provenance.json').write_text(json.dumps(result, indent=2)+'\n')
(evidence/'kernel-verification.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result, indent=2))
