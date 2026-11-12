"""Read-only recovery capture after a full-ROM trial lost its host connection."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('trial', type=Path)
parser.add_argument('--wait', type=int, default=15)
args = parser.parse_args()
assert args.trial.is_dir()
adb = Path(os.environ['LOCALAPPDATA']) / 'Android/Sdk/platform-tools/adb.exe'
serial = 'T110_ADB_SERIAL'

def run(*command, timeout=15):
    try:
        result = subprocess.run([str(adb), '-s', serial, *map(str, command)], capture_output=True, text=True, errors='replace', timeout=timeout)
        output = result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        output = 'HOST_ADB_TIMEOUT'
    with (args.trial / 'recovery-capture.log').open('a', encoding='utf-8') as f:
        f.write(repr(command) + '\n' + output + '\n')
    return output

deadline = time.monotonic() + args.wait
while time.monotonic() < deadline:
    state = run('shell', '[ "$(id -u)" = 0 ] && [ -x /sbin/recovery ] && cat /sys/block/mmcblk0/device/cid', timeout=5)
    if '1101003030384745T110_ADB_SERIAL' in state:
        break
    time.sleep(3)
else:
    raise SystemExit('NO_RECOVERY_CONNECTION: no device writes performed')

for name, command in {
    'last-kmsg.txt': 'cat /proc/last_kmsg',
    'recovery-state.txt': 'md5sum /dev/block/mmcblk0p10 /dev/block/mmcblk0p9; cat /proc/mounts; df /data',
}.items():
    (args.trial / name).write_text(run('shell', command), encoding='utf-8')
for remote, local in [
    ('/data/local/tmp/t110-bootlogs', 'persistent-bootlogs'),
    ('/data/local/tmp/t110-rom-data/tombstones', 'tombstones'),
    ('/data/local/tmp/t110-rom-data/local/tmp', 'android-logs'),
]:
    run('pull', remote, args.trial / local, timeout=120)
snapshots = [p for p in (args.trial / 'persistent-bootlogs').rglob('kernel-*.txt') if p.stat().st_size]
report = {'tablet_state': 'TWRP', 'device_writes': False, 'persistent_kernel_snapshots': len(snapshots)}
(args.trial / 'recovery-capture-result.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
