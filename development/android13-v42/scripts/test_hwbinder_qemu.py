"""Run the actual Android 13 HIDL Binder probe in the validated native QEMU boot."""
import gzip
import argparse
import re
import hashlib
import json
from pathlib import Path
import shutil
import stat
import subprocess

base = Path('/root/t110-build')
project = Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
destination = project / 'artifacts/android13-hwbinder'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--trial', default='v3')
args = parser.parse_args()
assert re.fullmatch(r'v[0-9]+', args.trial)
trial = destination / ('qemu-' + args.trial)
trial.mkdir()
root = base / ('qemu-hwbinder-root-' + args.trial)
assert not root.exists(), 'Preserve earlier test root'
shutil.copytree(base/'native-ramdisk-v5', root, symlinks=True)
shutil.copytree(destination/'bundle', root/'t110-hwbinder', symlinks=True)
ldconfig = root/'system/etc/ld.config.txt'
ldconfig.write_text('dir.hwbinder = /t110-hwbinder/bin\n' + ldconfig.read_text() +
                    '\n[hwbinder]\nnamespace.default.isolated = false\nnamespace.default.search.paths = /t110-hwbinder/lib\n')
rc = root/'system/etc/init/hw/init.rc'
text = rc.read_text().replace('    start processgroup-probe\n', '    start processgroup-probe\n    start hwbinder-probe\n')
text += '''
service hwbinder-probe /t110-hwbinder/bin/linker /t110-hwbinder/bin/t110_hwbinder_probe
    disabled
    oneshot
    stdio_to_kmsg
    seclabel u:r:recovery:s0
    setenv LD_LIBRARY_PATH /t110-hwbinder/lib
'''
rc.write_text(text)
subprocess.run([str(base/'out-native/soong/host/linux-x86/bin/host_init_verifier'),
                '--property-contexts='+str(root/'system/etc/selinux/plat_property_contexts'), str(rc)], check=True)
archive = bytearray()
def entry(name, mode, data, ino):
    fields = [ino, mode, 0, 0, 2 if stat.S_ISDIR(mode) else 1, 0, len(data), 0, 0, 0, 0, len(name.encode())+1, 0]
    archive.extend(b'070701' + ''.join(f'{n:08x}' for n in fields).encode())
    archive.extend(name.encode()+b'\0')
    archive.extend(b'\0' * (-len(archive)%4))
    archive.extend(data)
    archive.extend(b'\0' * (-len(archive)%4))
for ino, path in enumerate(sorted(root.rglob('*')), 1):
    mode = path.lstat().st_mode
    data = str(path.readlink()).encode() if path.is_symlink() else b'' if path.is_dir() else path.read_bytes()
    entry(path.relative_to(root).as_posix(), mode, data, ino)
entry('TRAILER!!!', 0, b'', ino+1)
archive.extend(b'\0' * (-len(archive)%512))
ramdisk = trial/'ramdisk.cpio.gz'
ramdisk.write_bytes(gzip.compress(bytes(archive), compresslevel=9, mtime=0))
kernel = base/'out-qemu-binder-modern/arch/arm/boot/zImage'
cmd = ['timeout', '50s', 'qemu-system-arm', '-M', 'vexpress-a9', '-cpu', 'cortex-a9',
       '-smp', '2', '-m', '512M', '-display', 'none', '-monitor', 'none', '-serial', 'stdio',
       '-net', 'none', '-no-reboot', '-kernel', str(kernel), '-initrd', str(ramdisk),
       '-append', 'console=ttyAMA0 rdinit=/init panic=1']
log = trial/'test.log'
with log.open('wb') as output:
    run = subprocess.run(cmd, stdout=output, stderr=subprocess.STDOUT)
output = log.read_text(errors='replace')
passed = ('PASS Android 13 HIDL Binder cross-process 4099-byte SG roundtrip' in output and
          "Service 'hwbinder-probe'" in output and not any(x in output for x in ['Kernel panic', 'Unable to handle kernel', 'FAIL Android 13 HIDL']))
result = {'status': 'QEMU_PASS_HARDWARE_PENDING' if passed else 'QEMU_FAILED',
          'qemu_exit': run.returncode, 'kernel_sha256': hashlib.sha256(kernel.read_bytes()).hexdigest(),
          'ramdisk_sha256': hashlib.sha256(ramdisk.read_bytes()).hexdigest(),
          'probe_sha256': hashlib.sha256((destination/'bundle/bin/t110_hwbinder_probe').read_bytes()).hexdigest(),
          'scope': 'Actual Android 13 HIDL Binder SG transport in QEMU vexpress, not T110 hardware or a HIDL service-stack test',
          'policy': 'Engineering recovery policy; permissive recovery domain, not production validation'}
(trial/'result.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result, indent=2))
print('\n'.join(x for x in output.splitlines() if 'hwbinder-probe' in x or 'HIDL Binder' in x or 'CANNOT LINK' in x))
assert passed
