"""Compile and sign our resource-only overlay; leave Google's APK intact."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess

base = Path('/root/t110-lineage14-ui')
here = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--android-root', type=Path, default=Path('/root/t110-lineage14/android'))
parser.add_argument('--out-dir', type=Path, default=base/'out')
parser.add_argument('--target-apk', type=Path, default=base/'artifacts-modern-google-20261115/added-files/priv-app/SetupWizard/SetupWizard.apk')
parser.add_argument('--destination', type=Path, default=base/'setup-footer-fix-20261116')
args = parser.parse_args()
source = here if (here/'res').is_dir() else here/'google-setup-overlay'
proof = args.destination
proof.mkdir(exist_ok=True)
target = args.target_apk
target_sha = '00614d38f760a32002a387f391d8db7d8d2f8d94866ae4eb52804c177ed6687c'
assert hashlib.sha256(target.read_bytes()).hexdigest() == target_sha
out = args.out_dir
aapt = out / 'host/linux-x86/bin/aapt'
framework = out / 'target/product/goyawifi/system/framework/framework-res.apk'
unsigned = proof / 'T110SetupLayout-unsigned.apk'
subprocess.run([str(aapt), 'package', '-f', '-M', str(source/'AndroidManifest.xml'),
    '-S', str(source/'res'), '-I', str(framework), '-I', str(target), '-F', str(unsigned)], check=True)
root = args.android_root
signed = proof / 'T110SetupLayout.apk'
subprocess.run(['/usr/lib/jvm/java-8-openjdk-amd64/bin/java',
    '-Djava.library.path=' + str(out/'host/linux-x86/lib64'), '-jar',
    str(out/'host/linux-x86/framework/signapk.jar'),
    str(root/'build/target/product/security/platform.x509.pem'),
    str(root/'build/target/product/security/platform.pk8'), str(unsigned), str(signed)], check=True)
layout = subprocess.check_output([str(aapt), 'dump', 'xmltree', str(signed), 'res/layout/sim_missing_activity.xml'], text=True)
for original_id in ('0x7f0e0060', '0x7f0e00ae', '0x7f0e00af', '0x7f070192'):
    assert original_id in layout, original_id
(proof/'compiled-layout.txt').write_text(layout)
(proof/'verification.json').write_text(json.dumps({'target_apk_unchanged':True,
    'target_sha256':target_sha, 'overlay_sha256':hashlib.sha256(signed.read_bytes()).hexdigest(),
    'type':'resource-only trusted vendor overlay', 'original_ids_preserved':True,
    'skip_gravity':'bottom|right', 'runtime_verified':False}, indent=2))
print('Original Google APK untouched; footer overlay compiled and IDs checked.')
