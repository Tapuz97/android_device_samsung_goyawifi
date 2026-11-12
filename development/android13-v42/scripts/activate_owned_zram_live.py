"""Qualify the existing uninitialized RAM-only zram0 on this boot, with no reboot.

Use Android's existing swap_block_device label and the byte-identical standard
toybox. Its private copy avoids the init->toolbox domain transition for swapon;
normal boot will instead use init with the specifically corrected permission.
No persistent permissive switch and no disk-backed swap.
"""
from pathlib import Path
import json,os,subprocess
p=Path(__file__).resolve().parents[1];e=p/'evidence/offline-v41/gapps-v29-test'
a=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(s):return subprocess.check_output(a+['shell',s],timeout=45).decode().strip()
before=sh('cat /proc/sys/kernel/random/boot_id; pidof system_server').splitlines()
assert before==['dd03b95b-3f7e-4a1e-8c27-84cd94056813','314']
assert sh('cat /sys/block/zram0/disksize')=='536870912' and sh('cat /sys/block/zram0/initstate') in ['0','1']
assert len(sh('cat /proc/swaps').splitlines())==1
assert sh('readlink -f /sys/dev/block/253:0').endswith('/virtual/block/zram0')
directory='/data/local/tmp/t110-zram-check'
path=directory+'/toybox'
assert sh('test ! -e '+directory+' && test ! -L '+directory+' && echo ABSENT')=='ABSENT'
assert sh('test ! -e '+path+' && test ! -L '+path+' && echo ABSENT')=='ABSENT'
sha=sh('sha256sum /system/bin/toybox').split()[0]
try:
    sh('mkdir '+directory+' && chcon u:object_r:shell_data_file:s0 '+directory+' && cp /system/bin/toybox '+path+' && chmod 0755 '+path+' && chcon u:object_r:shell_data_file:s0 '+path)
    assert sh('sha256sum '+path).split()[0]==sha
    sh('chcon u:object_r:swap_block_device:s0 /dev/block/zram0')
    formatted=sh('/system/bin/mkswap /dev/block/zram0')
    # Keep the exact toybox basename so its multicall dispatcher accepts swapon.
    activated=sh(path+' swapon /dev/block/zram0')
    swaps=sh('cat /proc/swaps');assert '/dev/block/zram0' in swaps
    assert sh('getenforce')=='Enforcing'
    assert sh('cat /proc/sys/kernel/random/boot_id; pidof system_server').splitlines()==before
    record={'status':'RAM_SWAP_ACTIVE_THIS_BOOT','boot_and_server':before,'logical_bytes':536870912,'swap_device':'/dev/block/zram0','mkswap':formatted,'swapon':activated,'swaps':swaps,'selinux_global_enforcing':True,'persistent_fix_still_required':True,'additional_boots':0,'disk_swap_used':False}
    (e/'zram-live-activation.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
finally:
    if sh('test -f '+path+' && echo EXISTS')=='EXISTS':
        assert sh('sha256sum '+path).split()[0]==sha
        sh('rm '+path)
    sh('rmdir '+directory)
