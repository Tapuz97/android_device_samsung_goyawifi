"""Read-only, bounded startup observations from one existing full ROM boot."""
import argparse
import json
import os
from pathlib import Path
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('trial', type=Path)
p.add_argument('--label', default='startup')
args = p.parse_args()
assert args.trial.is_dir() and args.label.replace('-', '').isalnum()
base = [str(Path(os.environ['LOCALAPPDATA']) / 'Android/Sdk/platform-tools/adb.exe'),
        '-s', 'T110_ADB_SERIAL']
guard = subprocess.run(base + ['shell', '[ -f /init.t110-core.rc ] && cat /sys/block/mmcblk0/device/cid'],
                       capture_output=True, timeout=8, check=True)
assert guard.stdout.decode().strip() == '1101003030384745T110_ADB_SERIAL'
commands = {
    'state': 'cat /proc/uptime; getprop sys.boot_completed; getprop init.svc.bootanim; pidof system_server; dumpsys activity users; ps -A',
    'logcat': "logcat -b all -d -t 12000 'snet_event_log:S' '*:V'",
    'crash': 'logcat -b crash -d',
    'window': 'dumpsys window windows',
    'services': 'service check wifi; service check mount; service check media.codec; getprop external_storage.sdcardfs.enabled; getprop init.svc.media.swcodec; getprop init.svc.media.codec',
    'storage': 'cat /proc/mounts; dumpsys mount; ls -ldZ /storage/emulated/0 /mnt/user/0/emulated/0 /mnt/runtime/default/emulated/0',
    'activity': 'dumpsys activity activities',
    'kernel': 'dmesg',
}
report = {'device_writes': False}
for name, command in commands.items():
    filename = args.label + '-' + name + '.txt'
    try:
        result = subprocess.run(base + ['shell', command], capture_output=True, timeout=18)
        data = result.stdout
        report[name] = dict(returncode=result.returncode, bytes=len(data), stderr=result.stderr.decode(errors='replace'))
    except subprocess.TimeoutExpired as error:
        data = b'CAPTURE_TIMEOUT\n' + (error.stdout or b'')
        report[name] = dict(timeout_seconds=18, bytes=len(data))
    (args.trial / filename).write_bytes(data)
    print(filename, report[name], flush=True)
(args.trial / (args.label + '-capture.json')).write_text(json.dumps(report, indent=2) + '\n')
