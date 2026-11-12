"""Capture a bounded Android graphics snapshot into an existing hardware trial."""
import argparse
from pathlib import Path
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('trial', type=Path)
p.add_argument('label')
args = p.parse_args()
assert args.trial.is_dir() and args.label.replace('-', '').isalnum()
adb = str(Path.home() / 'AppData/Local/Android/Sdk/platform-tools/adb.exe')
commands = {
    'state': 'cat /proc/uptime; getprop sys.boot_completed; getprop service.sf.prime_shader_cache; getprop init.svc.surfaceflinger; getprop init.svc.vendor.hwcomposer-2-1; getprop init.svc.bootanim; ps -A; cat /sys/class/graphics/fb0/virtual_size; cat /sys/class/graphics/fb0/pan',
    'graphics': "logcat -b main -b system -b crash -d -s SurfaceFlinger RenderEngine Gralloc2 GraphicBufferAllocator v_gralloc HwcLoader HWC2OnFbAdapter AndroidRuntime DEBUG",
    'framework': "logcat -b all -d -t 2200 'snet_event_log:S' '*:V'",
    'sf': 'dumpsys SurfaceFlinger',
    'kernel': 'dmesg',
}
for name, command in commands.items():
    try:
        result = subprocess.run([adb, '-s', 'T110_ADB_SERIAL', 'shell', command], capture_output=True, timeout=18)
        data = result.stdout + result.stderr
    except subprocess.TimeoutExpired as exc:
        data = b'CAPTURE_TIMEOUT\n' + (exc.stdout or b'')
    (args.trial / (args.label + '-' + name + '.txt')).write_bytes(data)
    print(name, len(data), flush=True)
