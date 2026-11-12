"""Read existing framebuffer memory only; does not wake, draw, or pan the display."""
from pathlib import Path
import argparse
import json
import os
import subprocess
from PIL import Image

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('trial', nargs='?', type=Path)
parser.add_argument('--label', default='framebuffer')
args = parser.parse_args()
p = args.trial or Path(__file__).resolve().parents[1]/'hardware-tests/20261107-105547-core'
assert p.is_dir() and args.label.replace('-', '').isalnum()
base = [str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'), '-s', 'T110_ADB_SERIAL']
guard = subprocess.run(base+['shell', '[ -f /init.t110-core.rc ] && cat /sys/block/mmcblk0/device/cid'], capture_output=True, timeout=8, check=True)
assert guard.stdout.decode().strip() == '1101003030384745T110_ADB_SERIAL'
def geometry():
    r = subprocess.run(base+['shell', 'cat /sys/class/graphics/fb0/virtual_size /sys/class/graphics/fb0/bits_per_pixel /sys/class/graphics/fb0/stride /sys/class/graphics/fb0/pan'], capture_output=True, timeout=8, check=True)
    return r.stdout.decode().splitlines()
before = geometry()
assert before[:3] == ['1024,1200', '32', '4096']
r = subprocess.run(base+['exec-out', 'dd if=/dev/graphics/fb0 bs=4096 count=1200 2>/dev/null'], capture_output=True, timeout=15, check=True)
(p/(args.label+'-read-result.json')).write_text(json.dumps(dict(bytes=len(r.stdout), stderr=r.stderr.decode(errors='replace'), sample=r.stdout[:160].decode(errors='replace') if len(r.stdout)<160 else 'binary', device_writes=False), indent=2)+'\n')
assert len(r.stdout) == 4096*1200, (len(r.stdout), r.stderr)
after = geometry()
(p/(args.label+'.raw')).write_bytes(r.stdout)
for index in (0, 1):
    page = r.stdout[index*4096*600:(index+1)*4096*600]
    Image.frombytes('RGB', (1024,600), page, 'raw', 'BGRX').save(p/f'{args.label}-page-{index}.png')
report = dict(before=before, after=after, bytes=len(r.stdout), unchanged_pan=before==after,
              device_writes=False, note='Raw framebuffer pages decoded as BGRX; channel order is not independently confirmed. Panel visibility requires user observation.')
(p/(args.label+'-capture.json')).write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report))
