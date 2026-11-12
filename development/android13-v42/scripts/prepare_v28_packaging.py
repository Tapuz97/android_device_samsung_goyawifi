"""Adapt the already checked kernel-only packager; no tablet IO."""
from pathlib import Path
p = Path(__file__).resolve().parents[1]
s = (p/'scripts/package_v27_boot.py').read_text().split('\nsystem = json.loads')[0]
s = s.replace('verified v26 boot', 'verified v27 boot')
s = s.replace("old=p/'artifacts/android13-full-v26'; dest=p/'artifacts/android13-full-v27'",
              "old=p/'artifacts/android13-full-v27'; dest=p/'artifacts/android13-full-v28'")
s = s.replace("kernel-storage-acl", "kernel-display-i2c")
s = s.replace("parent='../android13-full-v26'", "parent='../android13-full-v27'")
s = s.replace('Enable ext4 POSIX ACL for FUSE-backed user storage',
              'Keep shared GOYA I2C pins active on framebuffer blank without early suspend')
s = s.replace('Packaged v27 storage ACL kernel/module', 'Packaged v28 display I2C kernel/module')
s += "\npair=dict(boot_sha256=sha(full),boot_md5=hashlib.md5(full).hexdigest(),module_sha256=sha(module),bootstrap_policy_sha256=oldprov['bootstrap_policy_sha256'],status='PACKAGED_NOT_BOOT_TESTED')\n(dest/'system-pair.json').write_text(json.dumps(pair,indent=2)+'\\n')\n"
(p/'scripts/package_v28_boot.py').write_text(s)
s = (p/'scripts/verify_v27_boot.py').read_text()
s = s.replace('v27 contents', 'v28 contents')
s = s.replace("old = unpack(p/'artifacts/android13-full-v26/KERNEL.img')", "old = unpack(p/'artifacts/android13-full-v27/KERNEL.img')")
s = s.replace("new = unpack(p/'artifacts/android13-full-v27/KERNEL.img')", "new = unpack(p/'artifacts/android13-full-v28/KERNEL.img')")
s = s.replace("dest = p/'artifacts/android13-full-v27'", "dest = p/'artifacts/android13-full-v28'")
s = s.replace('kernel-storage-acl', 'kernel-display-i2c').replace('evidence/offline-v28/boot-verification.json', 'evidence/offline-v34/boot-verification.json')
(p/'scripts/verify_v28_boot.py').write_text(s)
print('Prepared v28 kernel-only packaging and independent verification')
