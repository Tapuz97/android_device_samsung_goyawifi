"""Remove owned device-side probes and save the exact safe resume state."""
from pathlib import Path
import subprocess,json,os,time,hashlib
p=Path(__file__).resolve().parents[1];e=p/'evidence/remote-fixes-20261110'
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(s,check=True):return subprocess.run(adb+['shell',s],capture_output=True,timeout=30,check=check).stdout.decode().strip()
assert sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
assert not sh('pidof strace',False)
assert not sh('pm path dev.tapuz.t110.audit',False)
owned=['/data/local/tmp/t110-ion-alloc-probe','/data/local/tmp/t110-codec-alloc.trace','/data/local/tmp/t110-import-only-candidate/libui.so','/data/local/tmp/t110-import-only-candidate/framework.png','/data/local/tmp/t110-lights-candidate/lights.mrvl.so','/data/local/tmp/t110-lights-candidate/t110_lights_probe','/data/local/tmp/t110-audit-framework.png']
for f in owned:sh('rm -f '+f)
for d in ['/data/local/tmp/t110-import-only-candidate','/data/local/tmp/t110-lights-candidate']:sh('rmdir '+d,False)
for f in owned:assert sh('test ! -e '+f+' && echo REMOVED')=='REMOVED'
state=sh('cat /proc/sys/kernel/random/boot_id; pidof system_server; sha256sum /dev/block/mmcblk0p10; settings get system screen_off_timeout; settings get global stay_on_while_plugged_in').splitlines()
assert state[0]=='a17c0d2a-5f5d-4bcd-874d-1930feebe07b' and state[1]=='303'
assert state[2].split()[0]=='83c0454a31d10aff0c80e32c94bc552a279670c4d367fe9e81ea498c6f25f29a'
assert state[3:]==['60000','0']
record={'host_epoch':time.time(),'installed_system_version':27,'installed_boot_version':29,'boot_id':state[0],'system_server':state[1],'boot_partition_sha256':state[2].split()[0],'additional_firmware_boots':0,'firmware_flashes':0,'qa_app_removed':True,'owned_phone_probes_removed':owned,'temporary_screen_preferences_restored':True,'clock_and_adbd_runtime_applied':True,'new_kernel_boot_artifact':'artifacts/android13-boot-v30/KERNEL.img','new_kernel_boot_flashed':False,'startup_sdk_status':'SOURCE_AND_EXTRACTED_JAVA_TESTS_PASS_FULL_MODULE_BLOCKED_ON_MISSING_INTERNAL_FRAMEWORK_DEPS','graphics_import_status':'COMPILED_IMPORT_HANG_RESOLVED_CAPTURE_PIXELS_STILL_CORRUPT','lights_status':'ADAPTER_SERVICE_COMPILED_REAL_PANEL_NODE_TEST_PASSES_FRAMEWORK_INSTALL_PENDING','full_system_build_status':'BLOCKED_E_VHD_ERROR_SEM_TIMEOUT_AFTER_VM_RESET','full_checklist_complete':False,'ui_phase_started':False}
(e/'FINAL-CHECKPOINT.json').write_text(json.dumps(record,indent=2)+'\n');print('REMOTE_FIXES_CHECKPOINT_SAVED_TABLET_RUNNING_V27_V29')
