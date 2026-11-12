"""Finish the checksum-verified transfer interrupted by the host ADB service."""
from pathlib import Path
import json,os,subprocess
p=Path(__file__).resolve().parents[1];pair=json.loads((p/'artifacts/lineage20-rom-v22/rom-pair.json').read_text())
assert pair['status']=='OFFLINE_VERIFIED_NOT_BOOT_TESTED'
assert pair['system_md5']=='36cd03dbb9196b868cd96107ad1a157b'
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
command='''set -e
[ "$(id -u)" = 0 ]
[ -x /sbin/recovery ]
[ "$(cat /sys/block/mmcblk0/device/cid)" = 1101003030384745T110_ADB_SERIAL ]
[ "$(md5sum /dev/block/mmcblk0p10 | cut -d' ' -f1)" = 942182cefec3cb7666096499220789d0 ]
[ "$(md5sum /dev/block/mmcblk0p9 | cut -d' ' -f1)" = cd9793e1ee8f284c9056b225885b5b1a ]
[ -z "$(losetup -a)" ]
[ ! -L /data/local/tmp/t110-rom-system.raw ]
[ ! -L /data/local/tmp/t110-rom-system-v22.incoming ]
[ ! -e /data/local/tmp/t110-rom-v22-tail.chunk ]
[ "$(md5sum /data/local/tmp/t110-rom-system-v22.incoming | cut -d' ' -f1)" = 36cd03dbb9196b868cd96107ad1a157b ]
mv /data/local/tmp/t110-rom-system-v22.incoming /data/local/tmp/t110-rom-system.raw
sync
echo STAGED_AND_SYNCED
'''
r=subprocess.run(adb+['shell',command],capture_output=True,timeout=180);assert r.returncode==0,(r.stdout,r.stderr)
assert b'STAGED_AND_SYNCED' in r.stdout
receipt=dict(status='STAGED_VERIFIED_NO_BOOT',system_md5=pair['system_md5'],system_sha256=pair['system_sha256'],compressed_chunk_transfer=True,
    installed_boot_md5=pair['boot_md5'],tablet_state='TWRP',hardware_boots_this_pass=0,
    host_adb_service_restarted=True,complete_incoming_image_reverified_before_atomic_activation=True)
(p/'evidence/v22-tablet-stage.json').write_text(json.dumps(receipt,indent=2)+'\n');print('STAGED_VERIFIED_NO_BOOT',flush=True)
