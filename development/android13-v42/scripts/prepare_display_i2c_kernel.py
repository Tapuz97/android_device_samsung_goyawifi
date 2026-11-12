"""Preserve the proven kernel and build a separate display power fix."""
from pathlib import Path
import difflib, hashlib, json, shutil, subprocess

b = Path('/root/t110-build')
p = Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
src, out = b/'kernel-display-i2c', b/'out-display-i2c'
assert not src.exists() and not out.exists()
subprocess.run(['cp', '-a', '--reflink=auto', str(b/'kernel-binder-secctx'), str(src)], check=True)
subprocess.run(['cp', '-a', '--reflink=auto', str(b/'out-storage-acl'), str(out)], check=True)
name = 'arch/arm/mach-mmp/onboard/Lcd_mipi2lvds_vx5b3d.c'
path = src/name
old = path.read_text()
anchor = '\t\tlcd_power(fbi, 0);\t\t\n#if defined(CONFIG_QUICKLOGIC_BRIDGE)\n'
assert old.count(anchor) == 1
new = old.replace(anchor, '''\t\tlcd_power(fbi, 0);
/* GOYA shares I2C1 with the live BT532 touchscreen. Android 13 blanks
 * fb0 without the old early-suspend touch power sequence. Remuxing
 * this bus to GPIO leaves touch timing out and prevents bridge wake.
 * Keep I2C pins active for that configuration; true touch/system PM
 * still owns its existing pin changes in board-goya-input.c.
 */
#if defined(CONFIG_QUICKLOGIC_BRIDGE) && \\
\t(!defined(CONFIG_MACH_GOYA) || defined(CONFIG_HAS_EARLYSUSPEND))
''')
path.write_text(new)
patch = ''.join(difflib.unified_diff(old.splitlines(True), new.splitlines(True), 'a/'+name, 'b/'+name))
(p/'patches/0061-kernel-goya-preserve-shared-i2c-on-fb-blank.patch').write_text(patch)
config = (out/'.config').read_bytes()
assert config == (p/'artifacts/kernel-storage-acl/kernel.config').read_bytes()
assert b'CONFIG_MACH_GOYA=y' in config and b'CONFIG_HAS_EARLYSUSPEND=y' not in config
record = dict(source=name, before_sha256=hashlib.sha256(old.encode()).hexdigest(),
              after_sha256=hashlib.sha256(new.encode()).hexdigest(),
              config_sha256=hashlib.sha256(config).hexdigest(),
              parent='artifacts/kernel-storage-acl', tablet_writes=False)
(p/'evidence/offline-v34/display-i2c-source.json').write_text(json.dumps(record, indent=2)+'\n')
print('Prepared separate GOYA display/I2C kernel source and unchanged configuration')
