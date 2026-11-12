"""Back up the repaired, unmounted SYSTEM partition; never write to the tablet."""
from pathlib import Path
import subprocess,hashlib,json,datetime,re
root=Path(__file__).resolve().parents[1];diagnostic=Path((root/'storage-diagnostics/CURRENT.txt').read_text().strip())
adb=[r'C:\Users\Gal\AppData\Local\Android\Sdk\platform-tools\adb.exe','-s','T110_ADB_SERIAL']
def shell(cmd,timeout=30):
 r=subprocess.run(adb+['shell',cmd],capture_output=True,timeout=timeout)
 if r.returncode:raise RuntimeError(r.stderr.decode(errors='replace'))
 return r.stdout.decode(errors='replace').replace('\r','')
assert 'uid=0' in shell('id')
assert shell('getprop ro.product.model').strip()=='SM-T110'
assert not re.search(r'/dev/block/mmcblk0p15\s',shell('cat /proc/mounts'))
assert int(shell('cat /sys/block/mmcblk0/mmcblk0p15/size').strip())*512==1594884096
folder=root/'backups'/(datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-repaired-system');folder.mkdir()
path=folder/'SYSTEM.img.partial'
report={'status':'IN_PROGRESS','description':'Post-repair SYSTEM snapshot; four dictionary blocks reconstructed from the matching stock AP, not an untouched original dump','repair_evidence':str(diagnostic.relative_to(root)),'partition':'mmcblk0p15','bytes_expected':1594884096}
(folder/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print('Backing up repaired SYSTEM to',folder,flush=True)
r=subprocess.run(adb+['pull','/dev/block/mmcblk0p15',str(path)],capture_output=True,timeout=600)
(folder/'transfer.log').write_bytes(r.stdout+r.stderr)
assert r.returncode==0 and path.stat().st_size==1594884096,'Incomplete backup; retained as .partial'
md5=hashlib.md5();sha=hashlib.sha256()
with path.open('rb') as f:
 for chunk in iter(lambda:f.read(4*1024*1024),b''):md5.update(chunk);sha.update(chunk)
print('Transfer complete; verifying device checksum',flush=True)
remote=shell('md5sum /dev/block/mmcblk0p15; echo HASH_RC:$?',timeout=180);(folder/'device-md5.txt').write_text(remote)
assert 'HASH_RC:0' in remote and re.match(r'[0-9a-f]{32}\s',remote)
assert remote.split()[0]==md5.hexdigest(),'Checksum mismatch'
path.rename(folder/'SYSTEM.img')
report.update(status='VERIFIED_POST_REPAIR_SYSTEM_SNAPSHOT',bytes=1594884096,md5=md5.hexdigest(),sha256=sha.hexdigest(),device_host_md5_match=True)
(folder/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
(diagnostic/'repaired-system-backup.json').write_text(json.dumps({'folder':str(folder.resolve()),**report},indent=2)+'\n')
print(json.dumps(report,indent=2),flush=True)