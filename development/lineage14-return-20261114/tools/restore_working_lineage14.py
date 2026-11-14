"""Restore the verified working14.1 pair and retained data from TWRP.

The faulty physical SYSTEM and recovery are never written.13 source/images and
its current data remain backed up; only its redundant tablet system file is freed.
"""
from pathlib import Path
import json,time
from recovery_transport import adb,shell,remote_hash,digest,BASE
ART=Path(r'\\wsl.localhost\Ubuntu\root\t110-lineage14\artifacts\lineage14-first-build')
A13=Path(r'\\wsl.localhost\Ubuntu\root\t110-android13-audit')
DEST=BASE/'tests/lineage14-restored-20261114';DEST.mkdir(exist_ok=True)
SYSTEM='01165196d103ecb5939bea6ec367497d956b606ac789178413169fc5f6cb95ea'
BOOT='93aa73c2cd75efee0441513967a878eb9b92161109d326febc26a61a48b2b0f2'
GZIP='fd362c7c072d6720f78f135e2a0640d720747f8eed8c9ee85ab7272eeda10125'
OLD_SYSTEM='470961893c93aa228c5722108ab15b364b970d6d143c3a5546401bb6ac7563ee'
OLD_BOOT='f2d735c3fea57b853147b6a846fc80ff0ed9e2df3d168ef398fc7d3a1a8365c7'
RECOVERY='f7f0bcf8a0cee4ecf265a2e1d75de028e97e9401c640e8cbc29d4b256d39452e'
def say(message):
    print(message,flush=True)
    with (DEST/'restore.log').open('a',encoding='utf-8') as out:out.write(time.strftime('%Y-%m-%d %H:%M:%S')+' '+message+'\n')
for path,expected in ((ART/'system.raw.img',SYSTEM),(ART/'system.raw.img.gz',GZIP),
                      (ART/'boot.img',BOOT),(A13/'complete-image/system.raw.img',OLD_SYSTEM),
                      (A13/'complete-image/boot.img',OLD_BOOT)):
    assert digest(path)==expected,path
receipt=json.loads((A13/'complete-candidate-backup/online-backup-verification.json').read_text(encoding='utf-8-sig'))
assert receipt['status']=='PASS_ONLINE_DOWNLOAD_HASH_READBACK'
assert json.loads((A13/'device/development/android13-audit-20261114/hardware-test-1/hardware-test-verification.json').read_text())['full_candidate_boots']==1
say('Working14.1 pair/compressed transfer and preserved13 pair/online receipt verified.')
assert adb('get-state').strip()=='recovery'
assert adb('shell','cat /sys/block/mmcblk0/device/cid').strip()=='11010030303847453004523270272200'
assert remote_hash('/dev/block/mmcblk0p10')==OLD_BOOT
assert remote_hash('/dev/block/mmcblk0p9')==RECOVERY
shell('''[ "$(cat /sys/class/block/mmcblk0p16/size)" = 10760192 ]
[ "$(cat /sys/class/block/mmcblk0p10/size)" = 32768 ]
[ "$(readlink /dev/block/platform/sdhci-pxav3.2/by-name/KERNEL)" = /dev/block/mmcblk0p10 ]
grep -q '^/dev/block/mmcblk0p16 /data ext4 ' /proc/mounts
[ ! -e /sys/block/loop0/loop/backing_file ]
[ "$(/sbin/busybox readlink -f /data/local/tmp)" = /data/local/tmp ]
[ -d /data/local/tmp/t110-lineage14-data ]
[ ! -L /data/local/tmp/t110-lineage14-data ]
[ -d /data/local/tmp/t110-rom-data ]
[ -f /data/local/tmp/t110-rom-system.raw ]
[ ! -L /data/local/tmp/t110-rom-system.raw ]
[ ! -e /data/local/tmp/t110-lineage14-system.raw ]
[ ! -e /data/local/tmp/t110-lineage14-system.raw.restoring ]
''')
say('Comparing the13 tablet system file with its intact C: backup before reclaiming its space.')
assert remote_hash('/data/local/tmp/t110-rom-system.raw',timeout=900)==OLD_SYSTEM
shell('''[ ! -e /sys/block/loop0/loop/backing_file ]
rm /data/local/tmp/t110-rom-system.raw
sync
''')
free=int(adb('shell','df /data').splitlines()[-1].split()[2])*1024
assert free>1594884096+383232412+256*1024*1024,free
say(f'Restored-image space available: {free//(1024*1024)} MiB. Both isolated data directories retained.')
incoming='/data/local/tmp/t110-restore14.system.gz'
boot_in='/data/local/tmp/t110-restore14.boot.img'
adb('push',ART/'system.raw.img.gz',incoming,timeout=1200)
adb('push',ART/'boot.img',boot_in,timeout=300)
assert remote_hash(incoming,timeout=600)==GZIP
assert remote_hash(boot_in)==BOOT
say('Compressed14.1 system/boot transfers verified; expanding into the original14.1 system path.')
shell('''[ ! -e /sys/block/loop0/loop/backing_file ]
/sbin/busybox gzip -dc /data/local/tmp/t110-restore14.system.gz > /data/local/tmp/t110-lineage14-system.raw.restoring
sync
''',timeout=1200)
assert remote_hash('/data/local/tmp/t110-lineage14-system.raw.restoring',timeout=900)==SYSTEM
shell('mv /data/local/tmp/t110-lineage14-system.raw.restoring /data/local/tmp/t110-lineage14-system.raw\nsync')
say('Full14.1 system readback matches. Restoring only its matching KERNEL image.')
shell('''[ "$(cat /sys/class/block/mmcblk0p10/size)" = 32768 ]
[ "$(readlink /dev/block/platform/sdhci-pxav3.2/by-name/KERNEL)" = /dev/block/mmcblk0p10 ]
dd if=/data/local/tmp/t110-restore14.boot.img of=/dev/block/mmcblk0p10 bs=4096
sync
''')
assert remote_hash('/dev/block/mmcblk0p10')==BOOT
assert remote_hash('/dev/block/mmcblk0p9')==RECOVERY
shell('rm /data/local/tmp/t110-restore14.system.gz /data/local/tmp/t110-restore14.boot.img\nsync')
result=dict(status='WORKING14_RESTORED_READBACK_VERIFIED_NOT_BOOTED',system_sha256=SYSTEM,boot_sha256=BOOT,
    recovery_sha256=RECOVERY,recovery_unchanged=True,physical_system_written=False,
    original14_data_preserved=True,android13_data_preserved=True,android13_source_and_images_preserved=True,
    normal_exit_command='/sbin/reboot recovery_done',ui_direction='Modernize14.1 selectively; retain native Lineage features and navigation')
(DEST/'restore-verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
say('Working14.1 pair fully restored and readback-verified. Recovery and both data directories unchanged.')
