"""Apply the already-intended swap policy after recording its exact init denial."""
from pathlib import Path
import json,os,subprocess
p=Path(__file__).resolve().parents[1];e=p/'evidence/ui-system-hang-20261112';receipt=e/'v41-live-swappiness.json';assert not receipt.exists()
log=(e/'v41-reclaim-kernel-log.txt').read_text()
assert 'avc: denied { write } for comm="init" name="swappiness"' in log
assert "Command 'write /proc/sys/vm/swappiness 100'" in log
install=json.loads((e/'v41-installation.json').read_text());assert install['status']=='ANDROID_BOOT_COMPLETED_ART_ACCEPTANCE_AND_UI_RETEST_PENDING'
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(command):
    r=subprocess.run(adb+['shell',command],capture_output=True,timeout=30)
    assert r.returncode==0,(r.stdout+r.stderr).decode(errors='replace')
    return r.stdout.decode().replace('\r','').strip()
assert sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
assert sh('cat /proc/sys/kernel/random/boot_id')==install['boot_id']
assert sh('getenforce')=='Enforcing' and sh('cat /proc/sys/vm/swappiness')=='60'
record=dict(boot_id=install['boot_id'],old=60,intended=100,persistent=False,selinux_bypassed=False,reboot=False,ui_fixed=False,
            reason='Exact init write already in ROM is denied because node retains generic proc label; precise device policy prepared offline')
sh('echo 100 > /proc/sys/vm/swappiness')
assert sh('cat /proc/sys/vm/swappiness')=='100' and sh('getenforce')=='Enforcing'
record.update(status='INTENDED_POLICY_APPLIED_ON_SAME_BOOT',after=100)
receipt.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
