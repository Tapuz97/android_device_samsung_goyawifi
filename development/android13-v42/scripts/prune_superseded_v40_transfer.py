"""Delete only the obsolete v40 transfer set after the v41 rollback is verified."""
from pathlib import Path
import json,os,re,subprocess
p=Path(__file__).resolve().parents[1];e=p/'evidence/ui-system-hang-20261112';receipt=e/'v40-transfer-pruned.json';assert not receipt.exists()
installed=json.loads((e/'v41-installation.json').read_text());assert installed['status'] in ['V41_IMAGE_VERIFIED_STARTING_ONE_FULL_BOOT','ANDROID_BOOT_COMPLETED_ART_ACCEPTANCE_AND_UI_RETEST_PENDING']
old=json.loads((p/'artifacts/lineage20-rom-v40-gapps/host-verification.json').read_text())
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(command,timeout=45,check=True):
    r=subprocess.run(adb+['shell',command],capture_output=True,timeout=timeout)
    if check:assert r.returncode==0,(r.stdout+r.stderr).decode(errors='replace')
    return r.stdout.decode(errors='replace').replace('\r','').strip()
assert sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
assert sh('sha256sum /dev/block/mmcblk0p10').split()[0]==installed['boot_sha256']
current='/stage-data/local/tmp/t110-v41-reclaim-paths-delta'
assert sh('test -d '+current+' && test ! -L '+current+' && readlink -f '+current)==current
assert sh('sha256sum '+current+'/rollback46.img').split()[0]==installed['previous_boot_sha256']
assert sh('sha256sum '+current+'/boot47.img').split()[0]==installed['boot_sha256']
stale='/stage-data/local/tmp/t110-v40-search-preopt-delta'
assert sh('test -d '+stale+' && test ! -L '+stale+' && readlink -f '+stale)==stale
names=[row[side+'_file'] for row in old['delta_ranges'] for side in ['old','new']]
assert all(re.fullmatch(r'[0-9]{4}\.(old|new)\.bin',name) for name in names)
assert set(sh('ls -1 '+stale).splitlines())==set(names)
assert not sh('find '+stale+' -type l')
before=sh('df -k /stage-data')
sh('rm '+' '.join(stale+'/'+name for name in names),90);sh('rmdir '+stale);sh('sync',90)
assert sh('test ! -e '+stale+' && echo REMOVED')=='REMOVED'
record=dict(status='OBSOLETE_V40_TRANSFER_DELETED',bytes_deleted=2*old['delta_bytes'],immediate_v40_system_and_boot_rollback_retained=current,
            both_data_profiles_untouched=True,system_image_untouched=True,before=before,after=sh('df -k /stage-data'))
receipt.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
