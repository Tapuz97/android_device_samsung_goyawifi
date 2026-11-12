from pathlib import Path
import json,os,subprocess
p=Path(__file__).resolve().parents[1];e=p/'evidence/ui-system-hang-20261112';e.mkdir(exist_ok=True);adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(cmd,timeout=15):
 r=subprocess.run(adb+['shell',cmd],capture_output=True,timeout=timeout);return r.stdout.decode(errors='replace').strip(),r.returncode
assert sh('cat /sys/block/mmcblk0/device/cid')[0]=='1101003030384745T110_ADB_SERIAL'
pid=sh('pidof system_server')[0];assert pid.isdigit();result={'server':pid,'sigquit_exit':sh('kill -3 '+pid)[1]}
result['disable']=sh('cmd bluetooth_manager disable',30)
for name,cmd in {'runtime-hashes':'sha256sum /apex/com.android.btservices/lib/libbluetooth_jni.so /system/apex/com.android.btservices/lib/libbluetooth_jni.so /vendor/bin/t110_bt_init',
 'runtime-versions':'getprop ro.apex.updatable; getprop init.svc.vendor.bluetooth-1-1; getprop init.svc.t110-bluetooth-init'}.items():
 out,code=sh(cmd);(e/(name+'.txt')).write_text(out+'\n',encoding='utf-8');result[name+'_exit']=code
(e/'quiesce.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
