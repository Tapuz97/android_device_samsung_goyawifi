"""Install the verified touch-only kernel update, retaining v28 for rollback."""
from pathlib import Path
import hashlib,json,os,subprocess,time

p=Path(__file__).resolve().parents[1];e=p/'hardware-tests/20261109-touch-charger'
e.mkdir(exist_ok=True)
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def call(args,timeout=40):
    r=subprocess.run(adb+args,capture_output=True,timeout=timeout)
    assert r.returncode==0,(args,r.stdout,r.stderr)
    return r.stdout.decode(errors='replace').strip()
def sh(s,timeout=40):return call(['shell',s],timeout)
new=p/'artifacts/android13-boot-v29/KERNEL.img';old=p/'artifacts/android13-full-v28/KERNEL.img'
sha=lambda v:hashlib.sha256(v).hexdigest()
meta=json.loads(new.with_name('provenance.json').read_text())
assert meta['status']=='OFFLINE_VERIFIED' and sha(new.read_bytes())==meta['full_boot_sha256']
# Reuse the independently written parser, without executing its old v27/v28 checks.
ns={'__file__':str(p/'scripts/verify_v28_boot.py')}
exec((p/'scripts/verify_v28_boot.py').read_text().split('\nold = unpack(',1)[0],ns)
a,b=ns['unpack'](old),ns['unpack'](new)
assert a[4]==b[4] and set(a[3])==set(b[3])
assert {k for k in a[3] if a[3][k]!=b[3][k]} <= {'lib/modules/galcore.ko'}
assert a[0][12:16]==b[0][12:16] and a[0][20:576]==b[0][20:576]
assert sha(b[1])==meta['kernel_sha256'] and sha(b[3]['lib/modules/galcore.ko'])==meta['module_sha256']
before=sh('cat /proc/sys/kernel/random/boot_id')
assert before=='41cb0223-fc50-4c9a-895e-3bde12af0004'
assert sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
assert sh('id -u')=='0'
assert sh('cat /sys/class/block/mmcblk0p10/size; cat /sys/class/block/mmcblk0p10/start').split()==['32768','163840']
assert sh('sha256sum /dev/block/mmcblk0p10',90).split()[0]==sha(old.read_bytes())
recovery=sh('sha256sum /dev/block/mmcblk0p9',90).split()[0]
remote='/data/local/tmp/t110-boot-v29.img'
call(['push',str(new),remote],90)
assert sh('sha256sum '+remote).split()[0]==meta['full_boot_sha256']
result=dict(status='STAGED',boot_before=before,old_boot_sha256=sha(old.read_bytes()),new_boot_sha256=meta['full_boot_sha256'],recovery_sha256=recovery,system_replaced=False)
(e/'installation.json').write_text(json.dumps(result,indent=2)+'\n')
sh('dd if='+remote+' of=/dev/block/mmcblk0p10 bs=4096 && sync',90)
assert sh('sha256sum /dev/block/mmcblk0p10',90).split()[0]==meta['full_boot_sha256']
assert sh('sha256sum /dev/block/mmcblk0p9',90).split()[0]==recovery
result.update(status='FLASH_VERIFIED_RESTARTING',host_time=time.time())
(e/'installation.json').write_text(json.dumps(result,indent=2)+'\n')
print('TOUCH_BOOT_FLASH_VERIFIED; restarting once',flush=True)
call(['reboot'],20)
