"""Reclaim only two verified boot staging copies after a completed ROM rollback."""
from pathlib import Path
import hashlib,json,os,subprocess
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-v35';result=e/'recovery-boot-staging-reclaimed.json';assert not result.exists()
record=json.loads((p/'evidence/offline-v41/gapps-v35-test/installation.json').read_text())
assert record['normal_boot_requests']==0 and record.get('retry_after_verified_rollback') is True
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(cmd):
 r=subprocess.run(adb+['shell',cmd],capture_output=True,timeout=90);assert r.returncode==0,r.stderr.decode(errors='replace');return r.stdout.decode(errors='replace').strip()
assert sh('test -x /sbin/recovery && cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
assert not sh('losetup -a')
assert sh('sha256sum /dev/block/mmcblk0p10').split()[0]==record['previous_boot_sha256']
assert sh('sha256sum /dev/block/mmcblk0p9').split()[0]==record['recovery_sha256']
entries=[]
for version,suffix in [(40,'rollback'),(41,'incoming')]:
 target=f'/data/local/tmp/t110-boot-v{version}.{suffix}.img'
 host=p/f'artifacts/android13-boot-v{version}/KERNEL.img';digest=hashlib.sha256(host.read_bytes()).hexdigest()
 assert sh('test -f '+target+' && test ! -L '+target+' && readlink -f '+target)==target
 assert sh('sha256sum '+target).split()[0]==digest
 assert sh("stat -t "+target+" | cut -d' ' -f2")=='16777216'
 entries.append(dict(path=target,bytes=16777216,sha256=digest,host_image_retained=True))
for item in entries:
 sh('rm '+item['path']+' && sync')
 assert sh('test ! -e '+item['path']+' && echo ABSENT')=='ABSENT'
result.write_text(json.dumps(dict(removed=entries,reason='Completed rollback left staging copies; installer recreates and revalidates both after the system transfer',free_space=sh('df -k /data')),indent=2)+'\n',encoding='utf-8')
print('RECLAIMED_VERIFIED_BOOT_STAGING_BYTES',sum(x['bytes'] for x in entries))
