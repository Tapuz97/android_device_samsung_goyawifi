"""Install the checked UI system container, preserving old boot, recovery and data."""
from pathlib import Path
import hashlib,json,subprocess,sys,tarfile,time
sys.path.insert(0,str(Path(__file__).parent.parent/'scripts'))
from recovery_transport import adb,shell,remote_hash,digest
WORK=Path(r'\\wsl.localhost\Ubuntu\root\t110-lineage14-ui')
ART=WORK/'artifacts';DEST=WORK/'hardware-test';DEST.mkdir(exist_ok=True)
report=json.loads((ART/'ui-image-verification.json').read_text(encoding='utf-8'))
assert report['status']=='OFFLINE_COMPLETE_IMAGE_CHECKS_PASSED_NOT_HARDWARE_QUALIFIED'
entries={entry['name']:entry for entry in report['files']}
for name in ('system.raw.img','system.raw.img.gz','boot.img'):
    assert digest(ART/name)==entries[name]['sha256'],name
assert entries['boot.img']['sha256']=='93aa73c2cd75efee0441513967a878eb9b92161109d326febc26a61a48b2b0f2'
online=json.loads((ART/'online-backup-verification.json').read_text(encoding='utf-8'))
assert online['status']=='PASS_ONLINE_DOWNLOAD_HASH_READBACK'
assert online['system_gzip_sha256']==entries['system.raw.img.gz']['sha256']
def say(text):
    print(text,flush=True)
    with (DEST/'install.log').open('a',encoding='utf-8') as out:out.write(text+'\n')
assert adb('shell','cat /sys/block/mmcblk0/device/cid').strip()=='11010030303847453004523270272200'
state=adb('get-state').strip()
if state=='device':
    assert adb('shell','getprop ro.build.version.release').strip()=='7.1.2'
    say('Requesting recovery from the preserved working14.1 boot.')
    adb('reboot','recovery')
    for _ in range(60):
        time.sleep(2)
        try:
            if adb('get-state',timeout=10).strip()=='recovery':break
        except Exception:pass
assert adb('get-state').strip()=='recovery','Recovery has not connected; no installation performed.'
assert remote_hash('/dev/block/mmcblk0p10')==entries['boot.img']['sha256']
recovery='f7f0bcf8a0cee4ecf265a2e1d75de028e97e9401c640e8cbc29d4b256d39452e'
assert remote_hash('/dev/block/mmcblk0p9')==recovery
normalized=False
rollback='/data/local/tmp/t110-lineage14-system.raw.pre-modern-ui'
if '__ROLLBACK_PRESENT__' in adb('shell','[ -f '+rollback+' ] && echo __ROLLBACK_PRESENT__'):
    # R1 is itself backed up online. Reclaim only its verified device copy;
    # keep the original working image throughout the replacement transaction.
    previous=WORK/'artifacts-r1'
    previous_report=json.loads((previous/'ui-image-verification.json').read_text(encoding='utf-8'))
    previous_files={entry['name']:entry for entry in previous_report['files']}
    previous_receipt=json.loads((previous/'online-backup-verification.json').read_text(encoding='utf-8'))
    assert previous_receipt['status']=='PASS_ONLINE_DOWNLOAD_HASH_READBACK'
    assert previous_receipt['system_gzip_sha256']==previous_files['system.raw.img.gz']['sha256']
    assert digest(previous/'system.raw.img')==previous_files['system.raw.img']['sha256']
    shell('''grep -q '^/dev/block/mmcblk0p16 /data ext4 ' /proc/mounts
[ ! -e /sys/block/loop0/loop/backing_file ]
[ ! -L /data/local/tmp/t110-lineage14-system.raw ]
[ ! -L /data/local/tmp/t110-lineage14-system.raw.pre-modern-ui ]
''')
    assert remote_hash('/data/local/tmp/t110-lineage14-system.raw',timeout=900)==previous_files['system.raw.img']['sha256']
    assert remote_hash(rollback,timeout=900)=='01165196d103ecb5939bea6ec367497d956b606ac789178413169fc5f6cb95ea'
    say('R1 and original rollback readbacks match their intact online/PC backups. Reclaiming only the redundant R1 device image.')
    shell('''[ ! -e /sys/block/loop0/loop/backing_file ]
rm /data/local/tmp/t110-lineage14-system.raw
mv /data/local/tmp/t110-lineage14-system.raw.pre-modern-ui /data/local/tmp/t110-lineage14-system.raw
sync
''')
    normalized=True
shell('''[ "$(cat /sys/class/block/mmcblk0p16/size)" = 10760192 ]
grep -q '^/dev/block/mmcblk0p16 /data ext4 ' /proc/mounts
[ ! -e /sys/block/loop0/loop/backing_file ]
[ -d /data/local/tmp/t110-lineage14-data ]
[ -f /data/local/tmp/t110-lineage14-system.raw ]
[ ! -L /data/local/tmp/t110-lineage14-system.raw ]
[ ! -e /data/local/tmp/t110-lineage14-system.raw.modern-ui-new ]
[ ! -e /data/local/tmp/t110-lineage14-system.raw.pre-modern-ui ]
''')
if not normalized:
    assert remote_hash('/data/local/tmp/t110-lineage14-system.raw',timeout=900)=='01165196d103ecb5939bea6ec367497d956b606ac789178413169fc5f6cb95ea'
say('Working boot/recovery/system readbacks match. Backing up the retained14.1 data privately.')
backup=DEST/'pre-ui-userdata-PRIVATE.tar.gz'
remote_backup='/data/local/tmp/t110-pre-ui-userdata.PRIVATE.tar.gz'
# This old recovery adbd does not implement exec-out. Use its verified shell
# transport to create a file, then the binary-safe ADB sync/pull protocol.
shell('''[ ! -e /data/local/tmp/t110-pre-ui-userdata.PRIVATE.tar.gz ]
/sbin/busybox tar -C /data/local/tmp -czf /data/local/tmp/t110-pre-ui-userdata.PRIVATE.tar.gz t110-lineage14-data
sync
''',timeout=1200)
backup_sha=remote_hash(remote_backup,timeout=900)
adb('pull',remote_backup,backup,timeout=1200)
assert digest(backup)==backup_sha
with tarfile.open(backup,'r:gz') as archive:
    members=archive.getmembers()
    assert any(member.name=='t110-lineage14-data/system/users/0.xml' for member in members)
    assert all(member.name=='t110-lineage14-data' or member.name.startswith('t110-lineage14-data/') for member in members)
shell('rm /data/local/tmp/t110-pre-ui-userdata.PRIVATE.tar.gz\nsync')
free=int(adb('shell','/sbin/busybox df -Pk /data').splitlines()[-1].split()[3])*1024
assert free>entries['system.raw.img']['bytes']+entries['system.raw.img.gz']['bytes']+128*1024*1024,free
incoming='/data/local/tmp/t110-modern-ui-system.gz'
adb('push',ART/'system.raw.img.gz',incoming,timeout=1200)
assert remote_hash(incoming,timeout=900)==entries['system.raw.img.gz']['sha256']
shell('''[ ! -e /sys/block/loop0/loop/backing_file ]
/sbin/busybox gzip -dc /data/local/tmp/t110-modern-ui-system.gz > /data/local/tmp/t110-lineage14-system.raw.modern-ui-new
sync
''',timeout=1200)
assert remote_hash('/data/local/tmp/t110-lineage14-system.raw.modern-ui-new',timeout=900)==entries['system.raw.img']['sha256']
say('The complete new image transfer and expanded readback match. Keeping the old image on the tablet for rollback.')
shell('''[ ! -e /sys/block/loop0/loop/backing_file ]
rm /data/local/tmp/t110-modern-ui-system.gz
mv /data/local/tmp/t110-lineage14-system.raw /data/local/tmp/t110-lineage14-system.raw.pre-modern-ui
if ! mv /data/local/tmp/t110-lineage14-system.raw.modern-ui-new /data/local/tmp/t110-lineage14-system.raw; then
    mv /data/local/tmp/t110-lineage14-system.raw.pre-modern-ui /data/local/tmp/t110-lineage14-system.raw
    exit 1
fi
sync
''')
assert remote_hash('/dev/block/mmcblk0p10')==entries['boot.img']['sha256']
assert remote_hash('/dev/block/mmcblk0p9')==recovery
record={'status':'SYSTEM_CONTAINER_INSTALLED_READBACK_VERIFIED_NOT_BOOTED',
        'boot_unchanged':True,'recovery_unchanged':True,'physical_system_written':False,
        'system_sha256':entries['system.raw.img']['sha256'],'old_system_kept_on_tablet':True,
        'userdata_private_backup_sha256':digest(backup),'original_data_preserved':True,
        'exit_command':'/sbin/reboot recovery_done'}
(DEST/'install-verification.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')
say('Full UI image installed. Kernel, recovery and both data profiles remain unchanged. Starting the full boot.')
adb('shell','/sbin/reboot recovery_done')
