"""Build/install/run a temporary QA instrumentation package, collect its report."""
from pathlib import Path
import hashlib,json,os,subprocess,zipfile,shlex,sys
p=Path(__file__).resolve().parents[1]
audit=p/'evidence/functional-audit-20261110';b=audit/'qa-build';b.mkdir(parents=True,exist_ok=True)
label=sys.argv[sys.argv.index('--evidence')+1] if '--evidence' in sys.argv else 'functional-audit-20261110'
assert all(part.replace('-','').isalnum() for part in Path(label).parts)
e=p/'evidence'/label;e.mkdir(exist_ok=True)
src=p/'scripts/functional-audit';sdk=Path(os.environ['LOCALAPPDATA'])/'Android/Sdk';bt=sdk/'build-tools/36.0.0';lib=sdk/'platforms/android-36/android.jar'
adb=[str(sdk/'platform-tools/adb.exe'),'-s','T110_ADB_SERIAL'];pkg='dev.tapuz.t110.audit'
build_only='--build-only' in sys.argv
def call(args,timeout=90,check=True):
    r=subprocess.run(list(map(str,args)),capture_output=True,timeout=timeout)
    if check:assert r.returncode==0,(args,r.stdout[-3000:],r.stderr[-3000:])
    return r
if not build_only:
    assert call(adb+['shell','cat /sys/block/mmcblk0/device/cid']).stdout.decode().strip()=='1101003030384745T110_ADB_SERIAL'
    before=call(adb+['shell','cat /proc/sys/kernel/random/boot_id; pidof system_server']).stdout.decode().splitlines()
apk=b/'T110FunctionalAudit.apk'
installed='' if build_only else call(adb+['shell','pm path '+pkg],check=False).stdout.decode().strip()
if installed and '--fresh' in sys.argv:
    assert installed.startswith('package:/data/app/') and '\n' not in installed
    assert call(adb+['shell','sha256sum '+installed.removeprefix('package:')]).stdout.decode().split()[0]==hashlib.sha256(apk.read_bytes()).hexdigest()
    if (e/'app-api-report.json').exists():(e/'app-api-before-fresh.json').write_bytes((e/'app-api-report.json').read_bytes())
    call(adb+['shell','cmd appwidget revokebind --package '+pkg+' --user 0'],check=False)
    assert b'Success' in call(adb+['uninstall',pkg]).stdout
    installed=''
if installed and '--rebuild' not in sys.argv:
    assert installed.startswith('package:/data/app/') and '\n' not in installed
    assert call(adb+['shell','sha256sum '+installed.removeprefix('package:')]).stdout.decode().split()[0]==hashlib.sha256(apk.read_bytes()).hexdigest()
else:
    classes=b/'classes';classes.mkdir(exist_ok=True)
    call(['javac','--release','8','-cp',lib,'-d',classes,*src.glob('*.java')])
    call(['java','-cp',bt/'lib/d8.jar','com.android.tools.r8.D8','--min-api','33','--lib',lib,'--output',b,*classes.rglob('*.class')])
    assets=b/'assets';assets.mkdir(exist_ok=True)
    call(['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y','-f','lavfi','-i','testsrc2=size=256x144:rate=10','-t','1','-an','-c:v','libx264','-profile:v','baseline','-pix_fmt','yuv420p','-movflags','+faststart',assets/'audit-video.mp4'])
    call(['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y','-f','lavfi','-i','sine=frequency=440:sample_rate=48000','-t','1','-c:a','aac','-b:a','64k',assets/'audit-audio.m4a'])
    unsigned=b/'audit-unsigned.apk';call([bt/'aapt2.exe','link','-o',unsigned,'-I',lib,'-A',assets,'--manifest',src/'AndroidManifest.xml'])
    with zipfile.ZipFile(unsigned,'a') as z:z.write(b/'classes.dex','classes.dex')
    aligned=b/'audit-aligned.apk';call([bt/'zipalign.exe','-f','4',unsigned,aligned])
    key=b/'qa-test-only.jks'
    if not key.exists():call(['keytool','-genkeypair','-keystore',key,'-storepass','android','-keypass','android','-alias','audit','-keyalg','RSA','-keysize','2048','-validity','3650','-dname','CN=T110 Temporary QA Test Key'])
    signer=['java','--enable-native-access=ALL-UNNAMED','-cp',bt/'lib/apksigner.jar','com.android.apksigner.ApkSignerTool']
    call(signer+['sign','--ks',key,'--ks-pass','pass:android','--key-pass','pass:android','--out',apk,aligned])
    call(signer+['verify',apk])
    if build_only:
        print('QA_APK_BUILT_NO_DEVICE_ACTIONS',hashlib.sha256(apk.read_bytes()).hexdigest(),flush=True)
        sys.exit(0)
    print(call(adb+['install','-r','-t','--no-streaming',apk],180).stdout.decode(),flush=True)
codecs_only='--only-codecs' in sys.argv
for permission in ([] if codecs_only else ['POST_NOTIFICATIONS','READ_CONTACTS','WRITE_CONTACTS','READ_CALENDAR','WRITE_CALENDAR']):
    call(adb+['shell','pm grant '+pkg+' android.permission.'+permission])
call(adb+['shell','input keyevent WAKEUP; wm dismiss-keyguard'])
zygote=call(adb+['shell','pidof zygote']).stdout.decode().split()[0]
raw=call(adb+['exec-out','cat /proc/'+zygote+'/environ']).stdout.decode()
runtime_env={}
for item in raw.split('\0'):
    if '=' in item:
        key,value=item.split('=',1)
        if key in ['BOOTCLASSPATH','DEX2OATBOOTCLASSPATH','ANDROID_ART_ROOT','ANDROID_I18N_ROOT','ANDROID_TZDATA_ROOT']:runtime_env[key]=value
assert runtime_env.get('BOOTCLASSPATH')
prefix=' '.join(k+'='+shlex.quote(v) for k,v in runtime_env.items())
if not codecs_only:
    widget_permission=call(adb+['shell',prefix+' appwidget grantbind --package '+pkg+' --user 0'],check=False)
    (e/'widget-qa-bind-permission.txt').write_bytes(widget_permission.stdout+widget_permission.stderr)
try:
    mode=' -e codecsOnly true' if codecs_only else ''
    run=call(adb+['shell',prefix+' am instrument -w'+mode+' '+pkg+'/.AuditInstrumentation'],240,False)
    (e/'app-instrumentation.txt').write_bytes(run.stdout+b'\nSTDERR:\n'+run.stderr)
    print(run.stdout.decode(errors='replace')[-3000:],flush=True)
except subprocess.TimeoutExpired as x:
    (e/'app-instrumentation.txt').write_bytes((x.stdout or b'')+b'\nINSTRUMENTATION_HOST_TIMEOUT\n'+(x.stderr or b''))
    call(adb+['shell','am force-stop '+pkg],check=False)
if (e/'app-api-report.json').exists() and not (e/'app-api-initial.json').exists():(e/'app-api-initial.json').write_bytes((e/'app-api-report.json').read_bytes())
report=call(adb+['exec-out','cat /data/user/0/'+pkg+'/files/report.json']).stdout
(e/'app-api-report.json').write_bytes(report);data=json.loads(report)
after=call(adb+['shell','cat /proc/sys/kernel/random/boot_id; pidof system_server']).stdout.decode().splitlines();assert after==before
(e/'app-probe-context.json').write_text(json.dumps({'apk_sha256':hashlib.sha256(apk.read_bytes()).hexdigest(),'boot_and_server':before,'additional_boots':0,'package':pkg,'temporary_qa_only':True,'rom_modifications':False},indent=2)+'\n')
print('APP_API_AUDIT_REPORT_SAVED',data.get('completed',False),flush=True)
