from pathlib import Path
import subprocess,tempfile,hashlib,shutil
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
with tempfile.TemporaryDirectory(prefix='t110-shader-') as td:
    f=Path(td)/'libGLESv2SC.so'
    subprocess.run(['debugfs','-R','dump /lib/libGLESv2SC.so '+str(f),'/root/t110-build/stock-system.raw.img'],check=True)
    data=f.read_bytes()
    assert len(data)==527012 and data[:4]==b'\x7fELF'
    target=p/'stock/T110XXUANI7/system/lib/libGLESv2SC.so'
    target.write_bytes(data)
    print(hashlib.sha256(data).hexdigest())
    print(subprocess.check_output(['readelf','-d',str(f)],text=True))
