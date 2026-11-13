"""Recover required ALSA runtime inputs from the already verified stock ext4 image."""
from pathlib import Path
import subprocess
root=Path('/root/t110-lineage14/reference/stock-ani7')
image=root/'system.raw.img'
if not image.is_file():
    image=root/'system.raw'
assert image.is_file(), 'Extract/unsparse the verified ANI7 stock SYSTEM first.'
for source,parent in [('/usr/share/alsa','usr/share'),('/usr/lib/alsa-lib','usr/lib')]:
    dest=root/'extracted'/parent
    dest.mkdir(parents=True,exist_ok=True)
    subprocess.run(['debugfs','-R',f'rdump {source} {dest}',str(image)],check=True)
assert (root/'extracted/usr/share/alsa/alsa.conf').is_file()
assert (root/'extracted/usr/lib/alsa-lib/libasound_module_ctl_codec.so').is_file()
print('Recovered stock ALSA configurations and dynamically loaded plugins.')
