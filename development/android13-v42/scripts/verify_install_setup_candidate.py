from pathlib import Path
import hashlib,json,os,re,subprocess,time
p=Path(__file__).resolve().parents[1];e=p/'evidence/offline-v32/setup-candidate';apk=e/'LineageSetupWizard.apk'
sdk=Path(os.environ['LOCALAPPDATA'])/'Android/Sdk';bt=sdk/'build-tools/36.0.0'
adb=[str(sdk/'platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def call(args,timeout=30):
    r=subprocess.run(args,capture_output=True,timeout=timeout)
    assert r.returncode==0,(args,r.stdout.decode(errors='replace'),r.stderr.decode(errors='replace'))
    return r.stdout
signer=['java','--enable-native-access=ALL-UNNAMED','-cp',str(bt/'lib/apksigner.jar'),'com.android.apksigner.ApkSignerTool','verify','--print-certs']
sig=call(signer+[str(apk)]).decode();original=call(signer+[str(e.parent/'setup-original.apk')]).decode()
cert=lambda s:re.search(r'certificate SHA-256 digest: ([0-9a-f]{64})',s).group(1)
assert cert(sig)==cert(original)=='c8a2e9bccf597c2fb6dc66bee293fc13f2fc47ec77bc6b2b0d52c11f51192ab8'
manifest=call([str(bt/'aapt2.exe'),'dump','xmltree','--file','AndroidManifest.xml',str(apk)]).decode()
resources=call([str(bt/'aapt2.exe'),'dump','resources',str(apk)]).decode()
(e/'manifest.txt').write_text(manifest,encoding='utf-8');(e/'resources.txt').write_text(resources,encoding='utf-8');(e/'signature.txt').write_text(sig,encoding='utf-8')
assert 'package="org.lineageos.setupwizard"' in manifest
hardware=re.findall(r'android:hardwareAccelerated\(0x010102d3\)=@(0x[0-9a-f]+)',manifest)
assert len(hardware)==1,hardware
resource=re.search(r'resource '+hardware[0]+r' bool/config_setupHardwareAccelerated[^\n]*\n([^\n]+)',resources)
assert resource and 'false' in resource.group(1),resource.group(0) if resource else 'missing resource'
digest=hashlib.sha256(apk.read_bytes()).hexdigest()
report=dict(status='APK_SIGNATURE_AND_COMPILED_DEVICE_OVERLAY_VERIFIED',sha256=digest,certificate_sha256=cert(sig),hardware_acceleration=False)
(e/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
assert call(adb+['shell','test -f /init.t110-core.rc && cat /sys/block/mmcblk0/device/cid']).decode().strip()=='1101003030384745T110_ADB_SERIAL'
before=call(adb+['shell','cat /proc/sys/kernel/random/boot_id; pidof system_server']).decode()
r=call(adb+['install','-r','-t','--no-streaming',str(apk)],timeout=180).decode();assert 'Success' in r,r
print(r,flush=True)
call(adb+['shell',"setprop debug.hwui.use_partial_updates ''; input keyevent 224; am start -n org.lineageos.setupwizard/.SetupWizardActivity -a android.intent.action.MAIN -c android.intent.category.HOME"],timeout=30)
time.sleep(8)
trial=p/'hardware-tests/20261107-151636-core'
for script,args in [('capture_live_graphics.py',[str(trial),'setup-software-candidate']),('capture_v26_framebuffer.py',[str(trial),'--label','setup-software-candidate'])]:
    subprocess.run(['python',str(p/'scripts'/script),*args],check=True,timeout=120)
for name,command in [('window','dumpsys window windows'),('activity','dumpsys activity top'),('package','dumpsys package org.lineageos.setupwizard')]:
    (trial/('setup-software-candidate-'+name+'.txt')).write_bytes(call(adb+['shell',command],timeout=30))
after=call(adb+['shell','cat /proc/sys/kernel/random/boot_id; pidof system_server']).decode();assert before==after,(before,after)
report.update(installed_app_update=True,additional_boots=0,framework_restarted=False,boot_and_server=after.strip().splitlines(),visual_result='PENDING_REVIEW')
(e/'installation.json').write_text(json.dumps(report,indent=2)+'\n');print('SETUP_CANDIDATE_INSTALLED_SAME_BOOT',flush=True)
