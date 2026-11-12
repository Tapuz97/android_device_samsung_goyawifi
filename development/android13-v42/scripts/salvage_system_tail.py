from pathlib import Path
import subprocess,hashlib,json
adb=['C:/Users/Gal/AppData/Local/Android/Sdk/platform-tools/adb.exe','-s','T110_ADB_SERIAL'];folder=Path('backups/20261104T201457Z');start=1026932736;size=1594884096;tail=folder/'SYSTEM.tail-after-unreadable-block.bin';assert not tail.exists()
report={'status':'PARTIAL_BACKUP_WITH_UNREADABLE_RANGE','prefix':'SYSTEM.img.partial','prefix_bytes':1026928640,'unreadable_offset':1026928640,'unreadable_bytes':4096,'tail':tail.name,'tail_offset':start,'system_partition_bytes':size,'chunks':[]}
with tail.open('xb') as dst:
 for off in range(start,size,16*1024**2):
  count=min(16*1024**2,size-off)//4096
  cmd=f'dd if=/dev/block/mmcblk0p15 of=/tmp/system-backup-chunk.bin bs=4096 skip={off//4096} count={count}'
  r=subprocess.run(adb+['shell',cmd],capture_output=True,timeout=60)
  if b'I/O error' in r.stdout+r.stderr:raise RuntimeError((off,r.stdout,r.stderr))
  chunk=folder/'system-transfer.tmp';subprocess.run(adb+['pull','/tmp/system-backup-chunk.bin',str(chunk)],capture_output=True,check=True,timeout=60)
  b=chunk.read_bytes();assert len(b)==count*4096
  remote=subprocess.check_output(adb+['shell','md5sum /tmp/system-backup-chunk.bin'],timeout=30).decode().split()[0]
  assert hashlib.md5(b).hexdigest()==remote
  dst.write(b);dst.flush();report['chunks'].append({'offset':off,'bytes':len(b),'md5':remote});(folder/'system-salvage-map.json').write_text(json.dumps(report,indent=2))
  print('Verified tail through',off+len(b),'of',size,flush=True)
report['tail_sha256']=hashlib.sha256(tail.read_bytes()).hexdigest();(folder/'system-salvage-map.json').write_text(json.dumps(report,indent=2));print('Complete tail; 4096-byte gap remains explicitly unrecovered')
