"""Build/install a test-only instrumentation helper without a launcher app."""
from pathlib import Path
import hashlib,json,os,subprocess,zipfile,sys
p=Path(__file__).resolve().parents[1];src=p/'scripts/interaction-audit'
b=p/'evidence/functional-followup-20261111/interaction-build';b.mkdir(parents=True,exist_ok=True)
sdk=Path(os.environ['LOCALAPPDATA'])/'Android/Sdk';bt=sdk/'build-tools/36.0.0';lib=sdk/'platforms/android-36/android.jar'
def run(args):
    r=subprocess.run(list(map(str,args)),capture_output=True,timeout=120)
    assert r.returncode==0,(r.stdout.decode(errors='replace')[-1800:],r.stderr.decode(errors='replace')[-1800:])
    return r.stdout
classes=b/'classes';classes.mkdir(exist_ok=True)
run(['javac','--release','8','-cp',lib,'-d',classes,*src.glob('*.java')])
run(['java','-cp',bt/'lib/d8.jar','com.android.tools.r8.D8','--min-api','33','--lib',lib,'--output',b,*classes.rglob('*.class')])
unsigned=b/'unsigned.apk';run([bt/'aapt2.exe','link','-o',unsigned,'-I',lib,'--manifest',src/'AndroidManifest.xml'])
with zipfile.ZipFile(unsigned,'a') as z:
    z.write(b/'classes.dex','classes.dex')
    if '--gles-layer' in sys.argv:
        layer=p/'evidence/hardware-v35/libt110_gles_audit.so'
        assert layer.is_file()
        metadata=json.loads((layer.parent/'gles-audit-build.json').read_text())
        assert metadata['source_sha256']==hashlib.sha256((src/'gles_audit.c').read_bytes()).hexdigest(), 'Build the current native trace layer first'
        assert metadata['library_sha256']==hashlib.sha256(layer.read_bytes()).hexdigest()
        z.write(layer,'lib/armeabi-v7a/libt110_gles_audit.so')
aligned=b/'aligned.apk';run([bt/'zipalign.exe','-f','4',unsigned,aligned])
key=p/'evidence/functional-audit-20261110/qa-build/qa-test-only.jks';assert key.is_file()
apk=b/'T110InteractionAudit.apk'
signer=['java','--enable-native-access=ALL-UNNAMED','-cp',bt/'lib/apksigner.jar','com.android.apksigner.ApkSignerTool']
run(signer+['sign','--ks',key,'--ks-pass','pass:android','--key-pass','pass:android','--out',apk,aligned]);run(signer+['verify',apk])
adb=[sdk/'platform-tools/adb.exe','-s','T110_ADB_SERIAL']
if '--build-only' in sys.argv:
    print('TEST_ONLY_INSTRUMENTATION_BUILT',hashlib.sha256(apk.read_bytes()).hexdigest());raise SystemExit(0)
assert run(adb+['shell','cat /sys/block/mmcblk0/device/cid']).decode().strip()=='1101003030384745T110_ADB_SERIAL'
print(run(adb+['install','-r','-t','--no-streaming',apk]).decode().strip())
print('TEST_ONLY_INSTRUMENTATION_INSTALLED',hashlib.sha256(apk.read_bytes()).hexdigest())
