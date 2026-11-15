"""Install the verified full swipe-up image through the established loop path."""
from pathlib import Path
import gzip, json, shutil, sys, tarfile, time
sys.path.insert(0, str(Path(__file__).parent.parent/'scripts'))
from recovery_transport import adb, shell, remote_hash, digest

WORK=Path(r'\\wsl.localhost\Ubuntu\root\t110-lineage14-ui')
ART=WORK/'artifacts-drawer-20261115'
DEST=WORK/'hardware-test-drawer-20261115'
DEST.mkdir(exist_ok=True)
R2='eb38b38a506d10b0d8b7f405951dd58e50e6521a7528e2bd83ff2157bb7baa97'
ORIGINAL='01165196d103ecb5939bea6ec367497d956b606ac789178413169fc5f6cb95ea'
BOOT='93aa73c2cd75efee0441513967a878eb9b92161109d326febc26a61a48b2b0f2'
RECOVERY='f7f0bcf8a0cee4ecf265a2e1d75de028e97e9401c640e8cbc29d4b256d39452e'
report=json.loads((ART/'ui-image-verification.json').read_text(encoding='utf-8'))
assert report['status']=='OFFLINE_COMPLETE_IMAGE_CHECKS_PASSED_NOT_HARDWARE_QUALIFIED'
files={x['name']:x for x in report['files']}
for name in ('system.raw.img','system.raw.img.gz','boot.img'):
    assert digest(ART/name)==files[name]['sha256'],name
assert files['boot.img']['sha256']==BOOT
online=json.loads((ART/'online-backup-verification.json').read_text(encoding='utf-8'))
assert online['status']=='PASS_ONLINE_DOWNLOAD_HASH_READBACK'
assert online['system_gzip_sha256']==files['system.raw.img.gz']['sha256']
assert digest(WORK/'artifacts-swipe-20261115/system.raw.img')==R2
r2report=json.loads((WORK/'artifacts-swipe-20261115/ui-image-verification.json').read_text(encoding='utf-8'))
r2files={x['name']:x for x in r2report['files']}
r2online=json.loads((WORK/'artifacts-swipe-20261115/online-backup-verification.json').read_text(encoding='utf-8'))
assert r2online['status']=='PASS_ONLINE_DOWNLOAD_HASH_READBACK'
assert r2online['system_gzip_sha256']==r2files['system.raw.img.gz']['sha256']
assert digest(WORK/'artifacts-swipe-20261115/system.raw.img.gz')==r2online['system_gzip_sha256']

def say(s):
    print(s,flush=True)
    with (DEST/'install.log').open('a',encoding='utf-8') as out:out.write(s+'\n')

assert adb('shell','cat /sys/block/mmcblk0/device/cid').strip()=='11010030303847453004523270272200'
if adb('get-state').strip()=='device':
    assert 'T110_UI_20261114_R2' in adb('shell','getprop ro.build.display.id')
    say('Requesting recovery for the full checked image installation.')
    adb('reboot','recovery')
    for _ in range(60):
        time.sleep(2)
        try:
            if adb('get-state',timeout=5).strip()=='recovery':break
        except Exception:pass
assert adb('get-state').strip()=='recovery','Recovery unavailable; nothing replaced.'
assert remote_hash('/dev/block/mmcblk0p10')==BOOT
assert remote_hash('/dev/block/mmcblk0p9')==RECOVERY
shell('''grep -q '^/dev/block/mmcblk0p16 /data ext4 ' /proc/mounts
[ ! -e /sys/block/loop0/loop/backing_file ]
[ ! -L /data/local/tmp/t110-lineage14-system.raw ]
[ ! -L /data/local/tmp/t110-lineage14-system.raw.pre-modern-ui ]
[ ! -e /data/local/tmp/t110-lineage14-system.raw.drawer-new ]
[ ! -e /data/local/tmp/t110-drawer-system.gz ]
[ ! -e /data/local/tmp/t110-pre-drawer-userdata.PRIVATE.tar.gz ]
''')
assert remote_hash('/data/local/tmp/t110-lineage14-system.raw',timeout=900)==R2
assert remote_hash('/data/local/tmp/t110-lineage14-system.raw.pre-modern-ui',timeout=900)==ORIGINAL
say('Installed R2, original on-device rollback, boot and recovery hashes match.')

backup=DEST/'pre-drawer-userdata-PRIVATE.tar.gz'
plain=DEST/'pre-drawer-userdata-PRIVATE.tar'
assert not backup.exists() and not plain.exists(),'Do not overwrite a prior private backup.'
free=int(adb('shell','/sbin/busybox df -Pk /data').splitlines()[-1].split()[3])*1024
data_bytes=int(adb('shell','/sbin/busybox du -sk /data/local/tmp/t110-lineage14-data').split()[0])*1024
assert free>data_bytes+64*1024*1024,'Not enough room for an uncompressed data snapshot.'
# Compress on the PC rather than spending minutes compressing on the T110 CPU.
shell('''/sbin/busybox tar -C /data/local/tmp -cf /data/local/tmp/t110-pre-drawer-userdata.PRIVATE.tar.gz t110-lineage14-data
sync
''',timeout=1200)
backup_sha=remote_hash('/data/local/tmp/t110-pre-drawer-userdata.PRIVATE.tar.gz',timeout=900)
adb('pull','/data/local/tmp/t110-pre-drawer-userdata.PRIVATE.tar.gz',plain,timeout=1200)
assert digest(plain)==backup_sha
with tarfile.open(plain,'r:') as archive:
    members=archive.getmembers()
    assert any(x.name=='t110-lineage14-data/system/users/0.xml' for x in members)
    assert all(x.name=='t110-lineage14-data' or x.name.startswith('t110-lineage14-data/') for x in members)
with plain.open('rb') as src,backup.open('wb') as dst:
    with gzip.GzipFile(fileobj=dst,mode='wb',mtime=0,compresslevel=3) as zipped:
        shutil.copyfileobj(src,zipped)
plain.unlink()
backup_sha=digest(backup)
shell('rm /data/local/tmp/t110-pre-drawer-userdata.PRIVATE.tar.gz\nsync')
free=int(adb('shell','/sbin/busybox df -Pk /data').splitlines()[-1].split()[3])*1024
assert free>files['system.raw.img.gz']['bytes']+64*1024*1024
assert free+files['system.raw.img']['bytes']>files['system.raw.img.gz']['bytes']+files['system.raw.img']['bytes']+128*1024*1024
adb('push',ART/'system.raw.img.gz','/data/local/tmp/t110-drawer-system.gz',timeout=1200)
assert remote_hash('/data/local/tmp/t110-drawer-system.gz',timeout=900)==files['system.raw.img.gz']['sha256']
say('Private data backed up and incoming image hash verified. Original rollback stays on the tablet; R2 is preserved on PC and online.')

# Space does not permit three expanded images. Remove only the unmounted R2
# duplicate, whose byte-identical PC and downloaded-online backups were checked.
shell('''[ ! -e /sys/block/loop0/loop/backing_file ]
rm /data/local/tmp/t110-lineage14-system.raw
if ! /sbin/busybox gzip -dc /data/local/tmp/t110-drawer-system.gz > /data/local/tmp/t110-lineage14-system.raw.drawer-new; then
    rm /data/local/tmp/t110-lineage14-system.raw.drawer-new
    /sbin/busybox cp /data/local/tmp/t110-lineage14-system.raw.pre-modern-ui /data/local/tmp/t110-lineage14-system.raw
    sync
    exit 1
fi
sync
''',timeout=1200)
assert remote_hash('/data/local/tmp/t110-lineage14-system.raw.drawer-new',timeout=900)==files['system.raw.img']['sha256']
shell('''[ ! -e /sys/block/loop0/loop/backing_file ]
mv /data/local/tmp/t110-lineage14-system.raw.drawer-new /data/local/tmp/t110-lineage14-system.raw
rm /data/local/tmp/t110-drawer-system.gz
sync
''')
assert remote_hash('/dev/block/mmcblk0p10')==BOOT
assert remote_hash('/dev/block/mmcblk0p9')==RECOVERY
receipt={'status':'FULL_IMAGE_INSTALLED_READBACK_VERIFIED',
    'system_sha256':files['system.raw.img']['sha256'],
    'boot_unchanged':True,'recovery_unchanged':True,'physical_system_written':False,
    'original_rollback_kept_on_tablet':True,'previous_r2_preserved_pc_online':True,
    'userdata_preserved':True,'private_userdata_backup_sha256':backup_sha,
    'exit_command':'/sbin/reboot recovery_done'}
(DEST/'install-verification.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
say('Full image installed and read back; starting the existing verified recovery exit.')
adb('shell','/sbin/reboot recovery_done')
