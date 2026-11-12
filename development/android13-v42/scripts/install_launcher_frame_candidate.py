"""Verify the software-frame launcher update and install on the current v25 boot."""
from pathlib import Path
import hashlib,json,os,re,subprocess,zipfile,time
p=Path(__file__).resolve().parents[1];e=p/'evidence/offline-v36'
apk=e/'launcher-candidate/TrebuchetQuickStep.apk';original=e/'launcher-original.apk'
sdk=Path(os.environ['LOCALAPPDATA'])/'Android/Sdk';bt=sdk/'build-tools/36.0.0'
adb=[str(sdk/'platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def call(args,timeout=35):
    r=subprocess.run(args,capture_output=True,timeout=timeout)
    assert r.returncode==0,(args,r.stdout.decode(errors='replace'),r.stderr.decode(errors='replace'))
    return r.stdout
assert 'SOFTWARE_FRAME_LIFECYCLE_PASS' in (e/'frame-lifecycle/result.txt').read_text()
assert 'SOFTWARE_SURFACE_ORDERING_PASS' in (e/'surface-transactions/result.txt').read_text()
signer=['java','--enable-native-access=ALL-UNNAMED','-cp',str(bt/'lib/apksigner.jar'),'com.android.apksigner.ApkSignerTool','verify','--print-certs']
sig=call(signer+[str(apk)]).decode();old=call(signer+[str(original)]).decode()
cert=lambda s:re.search(r'certificate SHA-256 digest: ([0-9a-f]{64})',s)[1]
assert cert(sig)==cert(old)
assert hashlib.sha256(original.read_bytes()).hexdigest()=='adc6b36596865afde2920b42a9bd38e8f712aa04dce493612bc2cc8932629bb8'
manifest=call([str(bt/'aapt2.exe'),'dump','xmltree','--file','AndroidManifest.xml',str(apk)]).decode()
assert 'package="com.android.launcher3"' in manifest
with zipfile.ZipFile(apk) as z:dex=b''.join(z.read(n) for n in z.namelist() if n.endswith('.dex'))
assert b'Using software draw completion for launcher transition' in dex
assert b'Applying launcher surface transaction without RenderThread' in dex
assert b'Cannot read hardware bitmap for software UI' in dex and b't110_bringup' in dex
digest=hashlib.sha256(apk.read_bytes()).hexdigest();assert digest!=hashlib.sha256(original.read_bytes()).hexdigest()
(e/'launcher-candidate/signature.txt').write_text(sig,encoding='utf-8')
(e/'launcher-candidate/manifest.txt').write_text(manifest,encoding='utf-8')
assert call(adb+['shell','test -f /init.t110-core.rc && cat /sys/block/mmcblk0/device/cid']).decode().strip()=='1101003030384745T110_ADB_SERIAL'
assert call(adb+['shell','sha256sum /system/framework/services.jar']).decode().split()[0]=='427754c42b4cd44803bf3ab90aeaac5c98756a20b637c2685d449a9bcef0abc3'
before=call(adb+['shell','cat /proc/sys/kernel/random/boot_id; pidof system_server']).decode().strip().splitlines()
assert before==['e7d5592a-6995-482f-a2e3-25e2741ebf95','378'],before
result=call(adb+['install','-r','-t','--no-streaming',str(apk)],180).decode();assert 'Success' in result,result
path=call(adb+['shell','pm path com.android.launcher3']).decode().strip().removeprefix('package:')
assert path.startswith('/data/app/') and path.endswith('.apk') and '\n' not in path
assert call(adb+['shell','sha256sum '+path]).decode().split()[0]==digest
report=dict(status='INSTALLED_SIGNATURE_HASH_VERIFIED_RUNTIME_PENDING',sha256=digest,certificate_sha256=cert(sig),installed_path=path,additional_boots=0,boot_and_server=before)
(e/'launcher-candidate/installation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('LAUNCHER_UPDATE_INSTALLED_AND_HASH_VERIFIED',flush=True)
compiled=call(adb+['shell','cmd package compile -m speed -f com.android.launcher3'],240).decode();assert 'Success' in compiled,compiled
call(adb+['shell','am force-stop com.android.launcher3; input keyevent WAKEUP; wm dismiss-keyguard; am start -W -a android.intent.action.MAIN -c android.intent.category.HOME'],60)
after=call(adb+['shell','cat /proc/sys/kernel/random/boot_id; pidof system_server']).decode().strip().splitlines();assert before==after
report['on_device_compilation']='speed';(e/'launcher-candidate/installation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('LAUNCHER_PRECOMPILED_SAME_BOOT_RUNTIME_PENDING',flush=True)
