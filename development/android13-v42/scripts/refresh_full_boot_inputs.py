from pathlib import Path
import hashlib, shutil
out=Path('/root/t110-build/out-system/target/product/t110_bringup')
dest=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110/work/core-boot')
cil=(out/'system/vendor/etc/selinux/vendor_sepolicy.cil').read_text()
assert 'sysfs_t110_vsync' in cil
for source,target in [('root/sepolicy','logging-test-policy'),('root/init.environ.rc','init.environ.rc')]:
    content=(out/source).read_bytes()
    assert content
    (dest/target).write_bytes(content)
    print(target,hashlib.sha256(content).hexdigest())
