"""Use native ART speed compilation for the interpreted apps observed in the ANRs."""
from pathlib import Path
import datetime,json,os,re,subprocess,time
p=Path(__file__).resolve().parents[1];e=p/'evidence/ui-system-hang-20261112';receipt=e/'google-aot.json';assert not receipt.exists()
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(cmd,timeout=45):
 r=subprocess.run(adb+['shell',cmd],capture_output=True,timeout=timeout);return r.returncode,(r.stdout+r.stderr).decode(errors='replace').strip()
assert sh('cat /sys/block/mmcblk0/device/cid')[1]=='1101003030384745T110_ADB_SERIAL'
assert sh('getprop dalvik.vm.usejit')[1]=='false'
boot=sh('cat /proc/sys/kernel/random/boot_id')[1];server=sh('pidof system_server')[1];assert server.isdigit()
state=dict(started=datetime.datetime.now().astimezone().isoformat(),boot_id=boot,system_server=server,packages=[],features_removed=False,settings_changed=False,ui_fixed=False)
def save():receipt.write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8')
save()
for pkg in ['com.google.android.googlequicksearchbox','com.google.android.gms']:
 df=sh('df -k /data')[1];free=int(df.splitlines()[-1].split()[-3]);assert free>700*1024,free
 before=sh('dumpsys package dexopt')[1];(e/(pkg+'-dexopt-before.txt')).write_text(before,encoding='utf-8')
 status=re.search(r'\['+re.escape(pkg)+r'\](.*?)(?=\n\s*\[[\w.]|\Z)',before,re.S);assert status,pkg
 if '[status=speed]' in status[1]:state['packages'].append(dict(package=pkg,status='ALREADY_SPEED'));save();continue
 started=time.monotonic();print('OPTIMIZING',pkg,flush=True)
 code,text=sh('cmd package compile -m speed '+pkg,900)
 (e/(pkg+'-compile.txt')).write_text(text+'\n',encoding='utf-8')
 item=dict(package=pkg,exit_code=code,output=text[-1500:],seconds=round(time.monotonic()-started,2));state['packages'].append(item);save()
 assert code==0 and 'Success' in text,item
 assert sh('cat /proc/sys/kernel/random/boot_id')[1]==boot and sh('pidof system_server')[1]==server
 print('OPTIMIZED',pkg,item['seconds'],flush=True)
after=sh('dumpsys package dexopt')[1];(e/'google-dexopt-after.txt').write_text(after,encoding='utf-8')
state['status']='OPTIMIZATION_COMPLETED_UI_RETEST_PENDING';state['same_boot_and_server']=sh('cat /proc/sys/kernel/random/boot_id')[1]==boot and sh('pidof system_server')[1]==server;save();print(state['status'],flush=True)
