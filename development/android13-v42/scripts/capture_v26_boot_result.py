"""Read-only final observations from the single v26 boot; never alter runtime."""
from pathlib import Path
import json
import os
import subprocess

p = Path(__file__).resolve().parents[1]
trial = p/'hardware-tests/20261107-105547-core'
adb = Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'
base = [str(adb), '-s', 'T110_ADB_SERIAL']
report = {}
commands = {
    'final-user-state.txt': 'cat /proc/uptime; getprop sys.boot_completed; getprop init.svc.bootanim; pidof system_server; dumpsys activity users; ps -A; ls -lZ /dev/ion /dev/galcore',
    'final-logcat.txt': "logcat -b all -d -t 10000 'snet_event_log:S' '*:V'",
    'final-crash.txt': 'logcat -b crash -d',
    'final-window.txt': 'dumpsys window windows',
    'final-codec-services.txt': 'getprop init.svc.media.swcodec; getprop init.svc.media.codec; service check media.codec; service check media.extractor; service check wifi',
    'final-anr-list.txt': 'ls -t /data/anr',
}
def save(name, args, timeout=15):
    try:
        r = subprocess.run(base+args, capture_output=True, timeout=timeout)
        (trial/name).write_bytes(r.stdout)
        report[name] = dict(returncode=r.returncode, bytes=len(r.stdout), stderr=r.stderr.decode(errors='replace'))
        return r.stdout
    except subprocess.TimeoutExpired as e:
        (trial/(name+'.timeout')).write_bytes(e.stdout or b'')
        report[name] = dict(timeout_seconds=timeout)
        return b''
for name, cmd in commands.items():
    data = save(name, ['shell', cmd])
    print(name, report[name], flush=True)
    if name == 'final-anr-list.txt':
        names = [x for x in data.decode(errors='replace').splitlines() if x.startswith('anr_') and '/' not in x]
        for selected in names[:3]:
            save('final-'+selected, ['exec-out', 'cat', '/data/anr/'+selected])
shot = save('screen.png', ['exec-out', 'screencap', '-p'], 12)
report['screenshot_valid_png'] = shot.startswith(b'\x89PNG\r\n\x1a\n') and shot.endswith(b'IEND\xaeB`\x82')
(trial/'final-capture.json').write_text(json.dumps(report, indent=2)+'\n')
print('screenshot_valid_png', report['screenshot_valid_png'], flush=True)
