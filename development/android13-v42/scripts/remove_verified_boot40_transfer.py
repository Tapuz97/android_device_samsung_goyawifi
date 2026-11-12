"""Remove the single completed BOOT40 transfer after rechecking device/host hashes."""
from pathlib import Path
import hashlib,json,os,subprocess
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-v35';record=e/'boot40-transfer-cleanup.json';assert not record.exists()
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(cmd):
 r=subprocess.run(adb+['shell',cmd],capture_output=True,timeout=60);assert r.returncode==0,r.stderr.decode(errors='replace');return r.stdout.decode(errors='replace').strip()
assert sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
installation=json.loads((e/'boot40-installation.json').read_text());assert sh('cat /proc/sys/kernel/random/boot_id')==installation['boot_id']
target='/data/local/tmp/t110-network-boot40.img';sha=hashlib.sha256((p/'artifacts/android13-boot-v40/KERNEL.img').read_bytes()).hexdigest()
assert sha==installation['boot_sha256']
assert sh('test -f '+target+' && test ! -L '+target+' && readlink -f '+target)==target
assert sh('stat -c %s '+target)=='16777216'
assert sh('sha256sum '+target).split()[0]==sha==sh('sha256sum /dev/block/mmcblk0p10').split()[0]
before=sh('df -k /data');sh('rm -- '+target+' && sync')
assert sh('test ! -e '+target+' && test ! -L '+target+' && echo REMOVED')=='REMOVED'
result=dict(path=target,bytes=16777216,sha256=sha,host_image_retained=True,installed_partition_independently_verified=True,free_before=before,free_after=sh('df -k /data'))
record.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print('VERIFIED_TRANSFER_REMOVED_BYTES',result['bytes'])
