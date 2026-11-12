from pathlib import Path
import json,os,subprocess
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-bt-sd';out=e/'identity-mode-live-fix.json';assert not out.exists()
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(command):
 r=subprocess.run(adb+['shell',command],capture_output=True,timeout=30,check=True);return r.stdout.decode(errors='replace').strip()
install=json.loads((e/'v38-installation.json').read_text());assert sh('cat /proc/sys/kernel/random/boot_id')==install['boot_id']
assert sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
f='/data/vendor/t110-bluetooth/controller_address';assert sh('test -f '+f+' && test ! -L '+f+' && readlink -f '+f)==f
assert sh("stat -c '%a %u %g %s' "+f)=='600 0 1002 18'
before=sh('sha256sum '+f).split()[0];sh('chmod 0640 '+f);assert sh('sha256sum '+f).split()[0]==before
assert sh("stat -c '%a %u %g %s' "+f)=='640 0 1002 18'
out.write_text(json.dumps(dict(boot_id=install['boot_id'],before_mode='0600',after_mode='0640',uid=0,gid=1002,content_unchanged=True,
 controller_identity_exported=False,rom_rebuilt=False,permanent_loader_fix_pending_build=True),indent=2)+'\n');print('EXACT_IDENTITY_FILE_MODE_FIXED_CONTENT_UNCHANGED')
