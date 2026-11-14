"""Install verified Android13 loop image + KERNEL from TWRP; no reboot here.

Preserve14.1 ROMs on C/online and its isolated tablet data. Never write SYSTEM
or recovery. The old13 data is first archived privately and validated separately.
"""
from pathlib import Path
import json,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from recovery_transport import adb,shell,remote_hash,digest,BASE

AUDIT=Path(r'\\wsl.localhost\Ubuntu\root\t110-android13-audit')
IMAGE=AUDIT/'complete-image';BACKUP=AUDIT/'complete-candidate-backup'
WORK=AUDIT/'hardware-test-20261114';WORK.mkdir(exist_ok=True)
LOCAL=BASE/'tests/android13-complete-20261114';LOCAL.mkdir(exist_ok=True)
PRESERVED=Path(r'\\wsl.localhost\Ubuntu\root\t110-lineage14\artifacts\lineage14-first-build')
SYSTEM='470961893c93aa228c5722108ab15b364b970d6d143c3a5546401bb6ac7563ee'
BOOT='f2d735c3fea57b853147b6a846fc80ff0ed9e2df3d168ef398fc7d3a1a8365c7'
OLD_SYSTEM='01165196d103ecb5939bea6ec367497d956b606ac789178413169fc5f6cb95ea'
OLD_BOOT='93aa73c2cd75efee0441513967a878eb9b92161109d326febc26a61a48b2b0f2'
RECOVERY='f7f0bcf8a0cee4ecf265a2e1d75de028e97e9401c640e8cbc29d4b256d39452e'
def say(text):
    print(text,flush=True)
    with (LOCAL/'install.log').open('a',encoding='utf-8') as out:out.write(time.strftime('%Y-%m-%d %H:%M:%S')+' '+text+'\n')
def record(name):return json.loads((AUDIT/name).read_text(encoding='utf-8-sig'))
image=record('complete-image-verification.json');ns=record('production-namespace-verification.json')
policy=record('complete-image-policy-verification.json');boot=record('candidate-boot-verification.json')
assert image['status']==ns['status']==policy['status']=='PASS'
assert boot['status']=='PASS_OFFLINE_NOT_HARDWARE_QUALIFIED'
assert image['raw_image_sha256']==ns['image_sha256']==policy['image_sha256']==boot['system_sha256']==SYSTEM
online=json.loads((BACKUP/'online-backup-verification.json').read_text(encoding='utf-8-sig'))
assert online['status']=='PASS_ONLINE_DOWNLOAD_HASH_READBACK' and online['draft']
metadata={x['name']:x for x in online['assets']}
compressed=BACKUP/'system-android13-candidate-20261114.raw.img.gz'
assert digest(compressed)==metadata[compressed.name]['sha256']
assert digest(IMAGE/'system.raw.img')==SYSTEM and digest(IMAGE/'boot.img')==BOOT
assert digest(PRESERVED/'boot.img')==OLD_BOOT and digest(PRESERVED/'system.raw.img')==OLD_SYSTEM
private=json.loads((WORK/'private-data-backup-verification.json').read_text())
assert private['status']=='PASS_PRIVATE_LOCAL_ARCHIVE_READBACK'
assert digest(private['archive'])==private['sha256']
say('Host candidate, online-backup receipt, working14.1 pair and private old-data archive verified.')
assert adb('get-state').strip()=='recovery'
assert adb('shell','cat /sys/block/mmcblk0/device/cid').strip()=='11010030303847453004523270272200'
assert int(adb('shell','cat /sys/class/power_supply/battery/capacity').strip())>=30
assert remote_hash('/dev/block/mmcblk0p10')==OLD_BOOT
assert remote_hash('/dev/block/mmcblk0p9')==RECOVERY
shell('''[ "$(cat /sys/class/block/mmcblk0p16/size)" = 10760192 ]
[ "$(cat /sys/class/block/mmcblk0p10/size)" = 32768 ]
[ "$(readlink /dev/block/platform/sdhci-pxav3.2/by-name/KERNEL)" = /dev/block/mmcblk0p10 ]
grep -q '^/dev/block/mmcblk0p16 /data ext4 ' /proc/mounts
[ ! -e /sys/block/loop0/loop/backing_file ]
[ "$(/sbin/busybox readlink -f /data/local/tmp)" = /data/local/tmp ]
[ -d /data/local/tmp/t110-lineage14-data ]
[ -f /data/local/tmp/t110-lineage14-system.raw ]
[ ! -L /data/local/tmp/t110-lineage14-system.raw ]
[ ! -e /data/local/tmp/t110-rom-system.raw ]
[ ! -e /data/local/tmp/t110-rom-system.raw.incoming ]
''')
say('Checking tablet14.1 system against the preserved C: image before reclaiming its file space.')
assert remote_hash('/data/local/tmp/t110-lineage14-system.raw',timeout=900)==OLD_SYSTEM
shell('''[ ! -e /sys/block/loop0/loop/backing_file ]
for name in t110-rom-data t110-rom-data.pre-gapps t110-bootlogs; do
    [ -d /data/local/tmp/$name ]
    [ ! -L /data/local/tmp/$name ]
    [ "$(/sbin/busybox readlink -f /data/local/tmp/$name)" = /data/local/tmp/$name ]
done
rm -rf /data/local/tmp/t110-rom-data /data/local/tmp/t110-rom-data.pre-gapps /data/local/tmp/t110-bootlogs
rm /data/local/tmp/t110-lineage14-system.raw
mkdir -p /data/local/tmp/t110-rom-data
chown 1000:1000 /data/local/tmp/t110-rom-data
chmod 0771 /data/local/tmp/t110-rom-data
sync
''',timeout=300)
free=int(adb('shell','df /data').splitlines()[-1].split()[2])*1024
assert free>image['raw_bytes']+compressed.stat().st_size+512*1024*1024,free
say(f'Storage ready: {free//(1024*1024)} MiB free;14.1 data retained; old13 data archived on C:.')
incoming='/data/local/tmp/t110-android13-candidate-20261114.system.gz'
boot_in='/data/local/tmp/t110-android13-candidate-20261114.boot.img'
adb('push',compressed,incoming,timeout=1800)
adb('push',IMAGE/'boot.img',boot_in,timeout=300)
assert remote_hash(incoming,timeout=600)==metadata[compressed.name]['sha256']
assert remote_hash(boot_in)==BOOT
say('Transferred compressed system/boot hashes match; expanding the isolated system file.')
shell('''[ ! -e /sys/block/loop0/loop/backing_file ]
/sbin/busybox gzip -dc /data/local/tmp/t110-android13-candidate-20261114.system.gz > /data/local/tmp/t110-rom-system.raw.incoming
sync
''',timeout=1800)
assert remote_hash('/data/local/tmp/t110-rom-system.raw.incoming',timeout=900)==SYSTEM
shell('mv /data/local/tmp/t110-rom-system.raw.incoming /data/local/tmp/t110-rom-system.raw\nsync')
owner=Path.home()/'.android/adbkey.pub';assert owner.is_file()
adb('push',owner,'/tmp/t110-owner-adb.pub')
shell('''mkdir -p /data/local/tmp/t110-rom-data/misc/adb
chown 1000:9998 /data/local/tmp/t110-rom-data/misc
chmod 01771 /data/local/tmp/t110-rom-data/misc
chown 1000:2000 /data/local/tmp/t110-rom-data/misc/adb
chmod 02750 /data/local/tmp/t110-rom-data/misc/adb
cp /tmp/t110-owner-adb.pub /data/local/tmp/t110-rom-data/misc/adb/adb_keys
chown 1000:2000 /data/local/tmp/t110-rom-data/misc/adb/adb_keys
chmod 0640 /data/local/tmp/t110-rom-data/misc/adb/adb_keys
dd if=/dev/block/mmcblk0p10 of=/data/local/tmp/t110-lineage14-boot.rollback-20261114.img bs=4096
sync
''')
assert remote_hash('/data/local/tmp/t110-lineage14-boot.rollback-20261114.img')==OLD_BOOT
say('Full system readback passed. Writing only the verified KERNEL image; recovery/SYSTEM remain untouched.')
try:
    shell('''[ "$(cat /sys/class/block/mmcblk0p10/size)" = 32768 ]
[ "$(readlink /dev/block/platform/sdhci-pxav3.2/by-name/KERNEL)" = /dev/block/mmcblk0p10 ]
dd if=/data/local/tmp/t110-android13-candidate-20261114.boot.img of=/dev/block/mmcblk0p10 bs=4096
sync
''')
    assert remote_hash('/dev/block/mmcblk0p10')==BOOT
    assert remote_hash('/dev/block/mmcblk0p9')==RECOVERY
except Exception:
    shell('dd if=/data/local/tmp/t110-lineage14-boot.rollback-20261114.img of=/dev/block/mmcblk0p10 bs=4096\nsync')
    assert remote_hash('/dev/block/mmcblk0p10')==OLD_BOOT
    raise
shell('rm /data/local/tmp/t110-android13-candidate-20261114.system.gz /data/local/tmp/t110-android13-candidate-20261114.boot.img\nsync')
result=dict(status='ANDROID13_CANDIDATE_INSTALLED_READBACK_VERIFIED_NOT_BOOTED',
    system_sha256=SYSTEM,boot_sha256=BOOT,recovery_sha256=RECOVERY,recovery_unchanged=True,
    physical_system_written=False,working14_host_pair_preserved=True,working14_data_preserved=True,
    private_old_data_archive_sha256=private['sha256'],normal_exit_command='/sbin/reboot recovery_done',
    single_full_boot_test_requested=True)
for dest in (LOCAL,WORK):(dest/'install-verification.json').write_text(json.dumps(result,indent=2)+'\n')
say('Installation readback verified. Tablet remains in recovery, ready for its one full boot test.')
