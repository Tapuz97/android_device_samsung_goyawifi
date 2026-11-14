"""Read the current linear scanout page; no framebuffer writes or live feed."""
from pathlib import Path
import json,subprocess,sys
from PIL import Image
ADB=r'C:\Users\Gal\AppData\Local\Android\Sdk\platform-tools\adb.exe'
def adb(command):
    result=subprocess.run([ADB,'-s','3004523270272200','exec-out',command],capture_output=True,timeout=40)
    assert result.returncode==0,result.stderr.decode(errors='replace')[-200:]
    return result.stdout
meta=adb('cat /sys/class/graphics/fb0/virtual_size /sys/class/graphics/fb0/stride /sys/class/graphics/fb0/pan').decode().splitlines()
width,virtual_height=map(int,meta[0].split(','));stride=int(meta[1]);x,y=map(int,meta[2].split(','))
assert width==1024 and virtual_height==1800 and stride==4096 and x==0
height=600;assert y in (0,600,1200)
raw=adb('dd if=/dev/graphics/fb0 bs=4096 skip=%d count=600 2>/dev/null'%y)
assert len(raw)==stride*height,len(raw)
target=Path(sys.argv[1]);target.parent.mkdir(parents=True,exist_ok=True)
target.with_suffix('.raw').write_bytes(raw)
rotation=int(sys.argv[2]) if len(sys.argv)>2 else 270
frame=Image.frombytes('RGB',(width,height),raw,'raw','RGBX',stride)
if rotation:frame=frame.rotate(rotation,expand=True)
frame.save(target)
target.with_suffix('.json').write_text(json.dumps({'source':'read-only current fb0 scanout page',
    'width':width,'height':height,'stride':stride,'yoffset':y,'presentation_rotation':rotation,
    'pixel_decode':'RGBX; native palette byte order checked on installed Settings'},indent=2),encoding='utf-8')
print(target)
