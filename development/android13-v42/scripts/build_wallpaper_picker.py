"""Build the small wallpaper picker with the installed SDK; retain source for ROM builds."""
from pathlib import Path
import os,subprocess,zipfile,json,hashlib
p=Path(__file__).resolve().parents[1]
src=p/'work/device/samsung/t110_bringup/wallpapers'
out=p/'evidence/offline-v37/wallpapers';out.mkdir(parents=True,exist_ok=True)
sdk=Path(os.environ['LOCALAPPDATA'])/'Android/Sdk';bt=sdk/'build-tools/36.0.0'
android=sdk/'platforms/android-36/android.jar'
assert len(list((src/'assets').glob('*.jpg')))==7
def run(args):subprocess.run([str(x) for x in args],check=True)
run([bt/'aapt2.exe','compile','--dir',src/'res','-o',out/'resources.zip'])
gen=out/'gen';gen.mkdir(exist_ok=True)
run([bt/'aapt2.exe','link','-I',android,'--manifest',src/'AndroidManifest.xml','--java',gen,'-o',out/'unsigned.apk',out/'resources.zip'])
classes=out/'classes';classes.mkdir(exist_ok=True)
run(['javac','--release','8','-Xlint:-options','-cp',android,'-d',classes]+list((src/'src').rglob('*.java'))+list(gen.rglob('*.java')))
run(['java','-cp',bt/'lib/d8.jar','com.android.tools.r8.D8','--min-api','26','--lib',android,'--output',out]+list(classes.rglob('*.class')))
with zipfile.ZipFile(out/'unsigned.apk','a',compression=zipfile.ZIP_DEFLATED) as z:
    z.write(out/'classes.dex','classes.dex')
    for f in (src/'assets').glob('*.jpg'):z.write(f,'assets/'+f.name)
run([bt/'zipalign.exe','-f','4',out/'unsigned.apk',out/'aligned.apk'])
key=p/'tools/aosp-testkey'
signer=['java','--enable-native-access=ALL-UNNAMED','-cp',bt/'lib/apksigner.jar','com.android.apksigner.ApkSignerTool']
apk=out/'T110Wallpapers.apk'
run(signer+['sign','--key',key/'platform.pk8','--cert',key/'platform.x509.pem','--out',apk,out/'aligned.apk'])
run(signer+['verify','--print-certs',apk])
(out/'build.json').write_text(json.dumps(dict(sha256=hashlib.sha256(apk.read_bytes()).hexdigest(),bytes=apk.stat().st_size,wallpapers=len(list((src/'assets').glob('*.jpg')))),indent=2))
print('WALLPAPER_PICKER_BUILT',apk)
