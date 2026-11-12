"""Read firmware partitions via already-rooted TWRP ADB. No device writes.
Skips USER/CACHE; stores EFS only locally. Existing outputs are never overwritten.
"""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
from datetime import datetime,timezone

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--adb',required=True);p.add_argument('--serial',required=True);a=p.parse_args()
 base=[a.adb,'-s',a.serial]
 def shell(cmd,timeout=30):
  r=subprocess.run(base+['shell',cmd],capture_output=True,timeout=timeout)
  if r.returncode:raise RuntimeError(r.stderr.decode(errors='replace'))
  return r.stdout.decode(errors='replace').strip()
 assert shell('getprop ro.product.model')=='SM-T110','Unexpected model'
 assert 'uid=0' in shell('id'),'Need root recovery ADB'
 recovery_log=shell('cat /tmp/recovery.log')
 twrp=re.search(r'Starting TWRP ([0-9.]+)',recovery_log)
 assert twrp,'Need TWRP'
 links=shell('ls -l /dev/block/platform/sdhci-pxav3.2/by-name')
 mapping=dict(re.findall(r'(\w+)\s+->\s+/dev/block/(mmcblk0p\d+)',links))
 assert mapping['KERNEL']=='mmcblk0p10' and mapping['RECOVERY']=='mmcblk0p9' and mapping['SYSTEM']=='mmcblk0p15'
 mounts=shell('cat /proc/mounts')
 assert not re.search(r'^\S+ /system \S+ rw[, ]',mounts,re.M),'System is mounted writable'
 folder=Path(__file__).resolve().parents[1]/'backups'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ');folder.mkdir(parents=True)
 report={'serial':a.serial,'model':'SM-T110','twrp_version':twrp.group(1),'cmdline':shell('cat /proc/cmdline'),'links':links,'mounts':mounts,'images':{},'note':'RECOVERY contains TWRP. Stock recovery is retained separately from matching AP archive.'}
 (folder/'recovery.log').write_text(recovery_log,encoding='utf8')
 (folder/'kernel.log').write_text(shell('dmesg'),encoding='utf8')
 for name,part in mapping.items():
  if name in ('USER','CACHE'):continue
  size=int(shell('cat /sys/class/block/'+part+'/size'))*512
  if size>2*1024**3:raise RuntimeError('Unexpected firmware partition size')
  path=folder/(name+'.img');partial=path.with_suffix('.img.partial')
  assert not partial.exists()
  r=subprocess.run(base+['pull','/dev/block/'+part,str(partial)],capture_output=True,timeout=1200)
  assert r.returncode==0 and partial.stat().st_size==size,(name,r.stderr,partial.stat().st_size,size)
  md5=hashlib.md5();sha=hashlib.sha256()
  with partial.open('rb') as src:
   for b in iter(lambda:src.read(4*1024**2),b''):md5.update(b);sha.update(b)
  remote=shell('md5sum /dev/block/'+part,timeout=600).split()[0]
  assert md5.hexdigest()==remote,(name,'device/host checksum mismatch')
  partial.rename(path);report['images'][name]={'partition':part,'bytes':size,'md5':remote,'sha256':sha.hexdigest()}
  (folder/'manifest.json').write_text(json.dumps(report,indent=2),encoding='utf8');print('Verified',name,size,flush=True)
 print(folder)
if __name__=='__main__':main()
