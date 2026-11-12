"""Read the active T110 framebuffer page; store a portrait diagnostic PNG only."""
from pathlib import Path
from PIL import Image
import argparse,json,os,subprocess,time,tempfile
parser=argparse.ArgumentParser();parser.add_argument('label');args=parser.parse_args()
assert args.label.replace('-','').isalnum()
p=Path(__file__).resolve().parents[1]/'hardware-tests/20261109-settings-wallpaper'
p.mkdir(exist_ok=True)
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def call(cmd,raw=False):return subprocess.check_output(adb+(['exec-out'] if raw else ['shell'])+[cmd],timeout=20)
assert call('cat /sys/block/mmcblk0/device/cid').decode().strip()=='1101003030384745T110_ADB_SERIAL'
assert call('cat /sys/class/graphics/fb0/virtual_size /sys/class/graphics/fb0/bits_per_pixel /sys/class/graphics/fb0/stride').decode().splitlines()==['1024,1200','32','4096']
remote='/data/local/tmp/t110-capture-'+args.label+'.bin'
assert call('test ! -e '+remote+' && test ! -L '+remote+' && echo ABSENT').decode().strip()=='ABSENT'
try:
    with tempfile.TemporaryDirectory(prefix='t110-fb-capture-') as folder:
        local=Path(folder)/'frame.bin'
        for attempt in range(3):
            pan=call('cat /sys/class/graphics/fb0/pan').decode().strip()
            offset={'0,0':0,'0,600':600}[pan]
            call(f'dd if=/dev/graphics/fb0 of={remote} bs=4096 skip={offset} count=600 2>/dev/null')
            subprocess.run(adb+['pull',remote,str(local)],capture_output=True,timeout=30,check=True)
            raw=local.read_bytes();assert len(raw)==4096*600,'Display asleep or framebuffer read failed'
            if call('cat /sys/class/graphics/fb0/pan').decode().strip()==pan:break
        else:raise RuntimeError('Framebuffer page kept changing')
finally:
    assert call('test ! -L '+remote+' && echo SAFE').decode().strip()=='SAFE'
    call('rm -f '+remote)
Image.frombytes('RGB',(1024,600),raw,'raw','BGRX').transpose(Image.Transpose.ROTATE_270).save(p/(args.label+'.png'))
(p/(args.label+'.json')).write_text(json.dumps(dict(captured_at=time.time(),pan=pan,framebuffer_writes=False)))
print(str(p/(args.label+'.png')))
