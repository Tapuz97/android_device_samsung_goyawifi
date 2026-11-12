"""Back up eMMC boot regions and leading 4 MiB via root recovery.
Only device write is a temporary file in TWRP's RAM-backed /tmp.
"""
from pathlib import Path
import subprocess,hashlib,json
base=['C:/Users/Gal/AppData/Local/Android/Sdk/platform-tools/adb.exe','-s','T110_ADB_SERIAL']
def sh(c):return subprocess.check_output(base+['shell',c],timeout=60).decode().strip()
assert sh('getprop ro.product.model')=='SM-T110' and 'uid=0' in sh('id')
assert 'Starting TWRP' in sh('head -10 /tmp/recovery.log')
assert int(sh('cat /sys/class/block/mmcblk0p1/start'))==8192
out=Path('backups/20261104T201457Z');report={}
for name in ['mmcblk0boot0','mmcblk0boot1','mmcblk0-prefix']:
 if name=='mmcblk0-prefix':
  result=sh('dd if=/dev/block/mmcblk0 of=/tmp/emmc-prefix-backup.bin bs=512 count=8192')
  remote='/tmp/emmc-prefix-backup.bin';size=4194304
 else:
  remote='/dev/block/'+name;size=int(sh('cat /sys/class/block/'+name+'/size'))*512
 path=out/(name+'.bin');assert not path.exists()
 subprocess.run(base+['pull',remote,str(path)],check=True,timeout=120)
 b=path.read_bytes();assert len(b)==size
 md5=hashlib.md5(b).hexdigest();assert sh('md5sum '+remote).split()[0]==md5
 report[name]={'bytes':size,'md5':md5,'sha256':hashlib.sha256(b).hexdigest()}
(out/'emmc-regions.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
