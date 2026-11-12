"""Capture fast, coherent framebuffer snapshots around notification shade scrolling."""
from pathlib import Path
import argparse,json,os,subprocess,uuid
from PIL import Image

parser=argparse.ArgumentParser();parser.add_argument('label');parser.add_argument('--action',default='')
parser.add_argument('--evidence',default='offline-v40',choices=['offline-v40','functional-audit-20261110','offline-v41','offline-v41/boot32-test'])
args=parser.parse_args();assert args.label.replace('-','').isalnum()
p=Path(__file__).resolve().parents[1];e=p/'evidence'/args.evidence;e.mkdir(exist_ok=True)
a=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(s):return subprocess.check_output(a+['shell',s],timeout=30).decode().strip()
assert sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
if args.action:print(sh(args.action),flush=True)
remote='/dev/t110-shade-snapshot-'+uuid.uuid4().hex
try:
    for n in range(5):
        state=sh(f'pan=$(cat /sys/class/graphics/fb0/pan); case "$pan" in 0,0) skip=0;; 0,600) skip=600;; *) exit 2;; esac; dd if=/dev/graphics/fb0 of={remote} bs=4096 skip=$skip count=600 2>/dev/null; echo $pan; cat /sys/class/graphics/fb0/pan').splitlines()
        if len(state)==2 and state[0]==state[1]:break
    else:raise RuntimeError(state)
    raw=subprocess.check_output(a+['exec-out','cat '+remote],timeout=30);assert len(raw)==4096*600
    Image.frombytes('RGB',(1024,600),raw,'raw','BGRX').transpose(Image.Transpose.ROTATE_270).save(e/(args.label+'.png'))
    meta={'pan':state[0],'focus':sh('dumpsys window | grep mCurrentFocus'),'boot':sh('cat /proc/sys/kernel/random/boot_id')}
    (e/(args.label+'.json')).write_text(json.dumps(meta,indent=2)+'\n')
    print(meta)
finally:sh('rm '+remote)
