"""Save the physical build's current PNG, stripping only any linker prefix."""
from pathlib import Path
import io,os,re,subprocess,sys
from PIL import Image
p=Path(__file__).resolve().parents[1]
version='v34' if '--v34' in sys.argv else 'v33' if '--v33' in sys.argv else 'v32' if '--v32' in sys.argv else 'v31' if '--v31' in sys.argv else 'v30'
e=p/f'evidence/offline-v41/gapps-{version}-test'
name=sys.argv[1];assert re.fullmatch(r'[a-z0-9-]+',name)
a=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
r=subprocess.run(a+['exec-out','screencap','-p'],capture_output=True,timeout=50,check=True)
off=r.stdout.find(bytes.fromhex('89504e470d0a1a0a'));assert 0<=off<4096
png=r.stdout[off:];im=Image.open(io.BytesIO(png));assert im.size==(600,1024);im.verify()
(e/(name+'.png')).write_bytes(png)
if off or r.stderr:(e/(name+'-capture-diagnostics.txt')).write_bytes(r.stdout[:off]+r.stderr)
print(e/(name+'.png'))
