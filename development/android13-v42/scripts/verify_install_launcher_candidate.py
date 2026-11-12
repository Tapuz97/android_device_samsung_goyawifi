"""Verify the signed launcher update, then exercise it on the current v23 boot."""
from pathlib import Path
import hashlib,json,os,re,subprocess,time,zipfile
p=Path(__file__).resolve().parents[1];e=p/'evidence/offline-v34/launcher-candidate'
apk=e/'TrebuchetQuickStep.apk'
sdk=Path(os.environ['LOCALAPPDATA'])/'Android/Sdk';bt=sdk/'build-tools/36.0.0'
adb=[str(sdk/'platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def call(args,timeout=30):
    r=subprocess.run(args,capture_output=True,timeout=timeout)
    assert r.returncode==0,(args,r.stdout.decode(errors='replace'),r.stderr.decode(errors='replace'))
    return r.stdout
signer=['java','--enable-native-access=ALL-UNNAMED','-cp',str(bt/'lib/apksigner.jar'),'com.android.apksigner.ApkSignerTool','verify','--print-certs']
sig=call(signer+[str(apk)]).decode();original=call(signer+[str(e.parent/'launcher-original.apk')]).decode()
cert=lambda s:re.search(r'certificate SHA-256 digest: ([0-9a-f]{64})',s).group(1)
assert cert(sig)==cert(original)
manifest=call([str(bt/'aapt2.exe'),'dump','xmltree','--file','AndroidManifest.xml',str(apk)]).decode()
assert 'package="com.android.launcher3"' in manifest
with zipfile.ZipFile(apk) as z:
    dex=b''.join(z.read(n) for n in z.namelist() if n.endswith('.dex'))
assert b'Cannot read hardware bitmap for software UI' in dex and b't110_bringup' in dex
assert apk.read_bytes()!=(e.parent/'launcher-original.apk').read_bytes()
(e/'manifest.txt').write_text(manifest,encoding='utf-8');(e/'signature.txt').write_text(sig,encoding='utf-8')
digest=hashlib.sha256(apk.read_bytes()).hexdigest()
report=dict(status='APK_SIGNATURE_AND_DEVICE_BITMAP_POLICY_VERIFIED',sha256=digest,certificate_sha256=cert(sig))
(e/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
assert call(adb+['shell','test -f /init.t110-core.rc && cat /sys/block/mmcblk0/device/cid']).decode().strip()=='1101003030384745T110_ADB_SERIAL'
assert call(adb+['shell','getprop ro.product.device']).decode().strip()=='t110_bringup'
assert call(adb+['shell','sha256sum /system/framework/framework.jar']).decode().split()[0]=='7d39885ee9afc59ebc6eebd176a6d7e1a93ce3d3a5d1a0f06249bf2ae5a50e18'
before=call(adb+['shell','cat /proc/sys/kernel/random/boot_id; pidof system_server']).decode()
r=call(adb+['install','-r','-t','--no-streaming',str(apk)],timeout=180).decode();assert 'Success' in r,r
path=call(adb+['shell','pm path com.android.launcher3']).decode().strip().removeprefix('package:')
assert path.startswith('/data/app/') and path.endswith('.apk') and '\n' not in path
assert call(adb+['shell','sha256sum '+path]).decode().split()[0]==digest
print('LAUNCHER_UPDATE_INSTALLED_AND_HASH_VERIFIED',flush=True)
call(adb+['shell','input keyevent 224; cmd statusbar collapse; wm dismiss-keyguard; am start -W -a android.intent.action.MAIN -c android.intent.category.HOME'],timeout=50)
time.sleep(10)
trial=p/'hardware-tests/20261107-170914-core'
for script,args in [('capture_live_graphics.py',[str(trial),'launcher-software-candidate']),('capture_v26_framebuffer.py',[str(trial),'--label','launcher-software-candidate'])]:
    subprocess.run(['python',str(p/'scripts'/script),*args],check=True,timeout=120)
after=call(adb+['shell','cat /proc/sys/kernel/random/boot_id; pidof system_server']).decode();assert before==after,(before,after)
report.update(installed_app_update=True,additional_boots=0,framework_restarted=False,installed_path=path,
    boot_and_server=after.strip().splitlines(),visual_result='PENDING_REVIEW')
(e/'installation.json').write_text(json.dumps(report,indent=2)+'\n')
print('LAUNCHER_CANDIDATE_INSTALLED_SAME_BOOT',flush=True)
