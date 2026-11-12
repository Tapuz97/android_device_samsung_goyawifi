"""Verify and install the native SystemUI notification fix without rebooting Android."""
from pathlib import Path
import hashlib,json,os,re,subprocess,time,zipfile
p=Path(__file__).resolve().parents[1];e=p/'evidence/offline-v40/systemui-candidate'
sdk=Path(os.environ['LOCALAPPDATA'])/'Android/Sdk';bt=sdk/'build-tools/36.0.0'
adb=[str(sdk/'platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def call(a,timeout=60):
    r=subprocess.run(a,capture_output=True,timeout=timeout)
    assert r.returncode==0,(a,r.stdout[-4000:],r.stderr[-4000:])
    return r.stdout
def sh(c,timeout=60):return call(adb+['shell',c],timeout).decode().strip()
before=sh('cat /proc/sys/kernel/random/boot_id; pidof system_server').splitlines()
assert before==['9f48e9ba-49c8-4cf8-a1f2-0fca599e83c1','311'],before
assert sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
original='/system/system_ext/priv-app/SystemUI/SystemUI.apk'
assert sh('pm path com.android.systemui')=='package:'+original
assert sh('sha256sum '+original).split()[0]=='abf394f4e01154fff834c8b7dc903b0e4af7251243255e5d408d857f77676742'
assert sh('sha256sum /system/framework/services.jar').split()[0]=='e430a91a56d6362610c8da45b44ba3d00fd9df9cc9b09c78a2e77a46bc2296db'
apk=e/'SystemUI.apk';old=e/'SystemUI-v26-original.apk'
call(adb+['pull',original,str(old)],120)
signer=['java','--enable-native-access=ALL-UNNAMED','-cp',str(bt/'lib/apksigner.jar'),'com.android.apksigner.ApkSignerTool','verify','--print-certs']
sig=call(signer+[str(apk)]).decode();old_sig=call(signer+[str(old)]).decode()
cert=lambda s:re.search(r'certificate SHA-256 digest: ([0-9a-f]{64})',s)[1]
assert cert(sig)==cert(old_sig)
manifest=call([str(bt/'aapt2.exe'),'dump','xmltree','--file','AndroidManifest.xml',str(apk)]).decode()
assert 'package="com.android.systemui"' in manifest
assert 'FINITE_NOTIFICATION_CLIP_PASS' in (e.parent/'clip-probe/last-result.txt').read_text()
assert 'build completed successfully' in (e/'build.log').read_text()
descriptor="Class descriptor  : 'Lcom/android/systemui/statusbar/notification/row/ExpandableView;'"
section=None;dex_path=e/'SystemUI-clip-verification.dex'
try:
    with zipfile.ZipFile(apk) as z:
        for n in z.namelist():
            if not n.endswith('.dex'):continue
            data=z.read(n)
            if b'Lcom/android/systemui/statusbar/notification/row/ExpandableView;' not in data:continue
            dex_path.write_bytes(data)
            dump=call([str(bt/'dexdump.exe'),'-d',str(dex_path)],180).decode(errors='replace')
            if descriptor in dump:
                section=dump[dump.index(descriptor):];end=section.find('\nClass #')
                if end>=0:section=section[:end]
                break
finally:
    if dex_path.exists():dex_path.unlink()
assert section is not None,'ExpandableView definition missing from candidate dex'
method=section[section.index("name          : 'updateClipping'"):]
method=method[:method.find('\n    #',1)]
assert all(s in method for s in ['t110_bringup','widthPixels','heightPixels','getWidth','ceil']),method
(e/'compiled-updateClipping.txt').write_text(method)
digest=hashlib.sha256(apk.read_bytes()).hexdigest()
assert digest!=hashlib.sha256(old.read_bytes()).hexdigest()
(e/'signature.txt').write_text(sig);(e/'manifest.txt').write_text(manifest)
report=dict(status='OFFLINE_VERIFIED',sha256=digest,certificate_sha256=cert(sig),original_sha256=hashlib.sha256(old.read_bytes()).hexdigest(),boot_and_server=before,additional_boots=0)
(e/'installation.json').write_text(json.dumps(report,indent=2)+'\n')
print('NATIVE_SYSTEMUI_CLIP_FIX_SIGNATURE_AND_BYTECODE_VERIFIED',flush=True)
result=subprocess.run(adb+['install','-r','-t','--no-streaming',str(apk)],capture_output=True,timeout=240)
if result.returncode!=0:
    report.update(status='APP_UPDATE_REJECTED_NO_CHANGE',failure=(result.stdout+result.stderr).decode(errors='replace'))
    (e/'installation.json').write_text(json.dumps(report,indent=2)+'\n')
    raise RuntimeError('App update rejected; build and install a verified system image instead')
assert b'Success' in result.stdout,result.stdout
path=sh('pm path com.android.systemui').removeprefix('package:')
assert path.startswith('/data/app/') and '\n' not in path
assert sh('sha256sum '+path).split()[0]==digest
report.update(status='INSTALLED_RUNTIME_PENDING',installed_path=path)
(e/'installation.json').write_text(json.dumps(report,indent=2)+'\n')
print('SYSTEMUI_CLIP_FIX_INSTALLED',flush=True)
assert 'Success' in sh('cmd package compile -m speed -f com.android.systemui',300)
assert sh('cat /proc/sys/kernel/random/boot_id; pidof system_server').splitlines()==before
report.update(compilation='speed',systemui_pid=sh('pidof com.android.systemui'))
(e/'installation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2),flush=True)
