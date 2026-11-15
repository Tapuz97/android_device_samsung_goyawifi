"""Create a self-contained launcher update from this same platform-signed build.

The ROM APK is dex-preoptimized: its code is stored separately in the image.
A normal application update needs the matching DEX embedded in the APK.
This prepares an update only; it never contacts a device.
"""
from pathlib import Path
import hashlib
import json
import subprocess
import zipfile

WORK = Path('/root/t110-lineage14-ui')
SOURCE = Path('/root/t110-lineage14/android')
OUT = WORK/'out'
DEST = WORK/'launcher-swipe-update'
DEST.mkdir(exist_ok=True)
JAVA = Path('/usr/lib/jvm/java-8-openjdk-amd64/bin')
HOST = OUT/'host/linux-x86'
BASELINE_SHA = '2778300b359e54c35966390e47c779c14cd11da1f5fb4ae0af3bddad1f49b400'
image = WORK/'artifacts/system.raw.img'
def sha(p):
    digest = hashlib.sha256()
    with p.open('rb') as stream:
        for chunk in iter(lambda: stream.read(8*1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()
assert sha(image) == BASELINE_SHA, 'Installed R2 backup changed'

def run(*args, **kwargs):
    return subprocess.run([str(x) for x in args], check=True, **kwargs)

local = Path(__file__).resolve().parent
checks = WORK/'swipe-checks'
checks.mkdir(exist_ok=True)
detector = SOURCE/'packages/apps/Trebuchet/src/com/android/launcher3/util/HomeSwipeDetector.java'
assert detector.read_bytes() == (local/'swipe-up/HomeSwipeDetector.java').read_bytes()
run(JAVA/'javac', '-source', '7', '-target', '7', '-d', checks,
    detector, local/'swipe-up/HomeSwipeDetectorTest.java', capture_output=True)
tests = run(JAVA/'java', '-cp', checks,
    'com.android.launcher3.util.HomeSwipeDetectorTest', capture_output=True, text=True).stdout
assert tests.strip() == 'PASS: 21 gesture behavior checks', tests
(DEST/'gesture-checks.txt').write_text(tests)
build_log = (WORK/'logs/launcher-swipe-build.log').read_text()
assert 'make completed successfully' in build_log
(DEST/'launcher-build.log').write_text(build_log)

rom_apk = DEST/'r2-original-system-Trebuchet.apk'
run('debugfs', '-R',
    'dump -p /priv-app/Trebuchet/Trebuchet.apk '+str(rom_apk), image,
    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
assert rom_apk.is_file(), 'Could not extract original launcher'
built = OUT/'target/product/goyawifi/obj/APPS/Trebuchet_intermediates/package.apk'
dex = sorted((OUT/'target/common/obj/APPS/Trebuchet_intermediates').glob('classes*.dex'))
assert dex and dex[0].name == 'classes.dex'
for p in dex:
    assert p.read_bytes().startswith(b'dex\n'), p
assert b'Lcom/android/launcher3/util/HomeSwipeDetector;' in dex[0].read_bytes()
unsigned = DEST/'Trebuchet-swipe-up-unsigned.apk'
with zipfile.ZipFile(built) as src, zipfile.ZipFile(unsigned, 'w') as dst:
    assert src.testzip() is None
    for item in src.infolist():
        if item.filename.startswith('META-INF/') or item.filename.endswith('.dex'):
            continue
        dst.writestr(item, src.read(item.filename))
    for p in dex:
        dst.write(p, p.name, compress_type=zipfile.ZIP_DEFLATED)
aligned = DEST/'Trebuchet-swipe-up-aligned.apk'
apk = DEST/'Trebuchet-T110-swipe-up-20261115.apk'
signer = Path('/mnt/c/Users/Gal/AppData/Local/Android/Sdk/build-tools/36.0.0/lib/apksigner.jar')
run(HOST/'bin/zipalign', '-f', '4', unsigned, aligned)
run(JAVA/'java', '-jar', signer, 'sign',
    '--key', SOURCE/'build/target/product/security/platform.pk8',
    '--cert', SOURCE/'build/target/product/security/platform.x509.pem',
    '--min-sdk-version', '22', '--v1-signing-enabled', 'true',
    '--v2-signing-enabled', 'true', '--v3-signing-enabled', 'false',
    '--v4-signing-enabled', 'false', '--out', apk, aligned)
alignment = run(HOST/'bin/zipalign', '-c', '4', apk, capture_output=True).returncode == 0
signature = run(JAVA/'java', '-jar', signer, 'verify', '--verbose', '--print-certs',
                apk, capture_output=True, text=True)
assert 'Verified using v1 scheme (JAR signing): true' in signature.stdout
assert 'Verified using v2 scheme (APK Signature Scheme v2): true' in signature.stdout
(DEST/'signature-verification.txt').write_text(signature.stdout+signature.stderr)

def certificate(apk_path):
    with zipfile.ZipFile(apk_path) as z:
        certs = [n for n in z.namelist() if n.startswith('META-INF/') and n.endswith('.RSA')]
        assert len(certs) == 1
        cert = run('openssl', 'pkcs7', '-inform', 'DER', '-print_certs',
                   input=z.read(certs[0]), capture_output=True).stdout
    der = run('openssl', 'x509', '-outform', 'DER', input=cert, capture_output=True).stdout
    return hashlib.sha256(der).hexdigest()

cert = certificate(apk)
assert cert == certificate(rom_apk), 'Update signing identity differs from installed R2'
with zipfile.ZipFile(apk) as z:
    assert z.testzip() is None
    for p in dex:
        assert hashlib.sha256(z.read(p.name)).hexdigest() == sha(p), p.name
badging = run(HOST/'bin/aapt', 'dump', 'badging', apk, capture_output=True, text=True).stdout
resources = run(HOST/'bin/aapt', 'dump', 'resources', apk, capture_output=True, text=True).stdout
assert 'id/t110_action_open_all_apps' in resources
assert "package: name='com.cyanogenmod.trebuchet'" in badging
assert "targetSdkVersion:'23'" in badging
assert "sdkVersion:'22'" in badging
(DEST/'apk-badging.txt').write_text(badging)
report = {
    'status': 'PASS_OFFLINE_ONLY',
    'apk': apk.name, 'apk_sha256': sha(apk), 'bytes': apk.stat().st_size,
    'package': 'com.cyanogenmod.trebuchet', 'min_sdk': 22, 'target_sdk': 23,
    'build_platform_api': 25,
    'signing_certificate_sha256': cert,
    'installed_r2_certificate_matches': True,
    'embedded_matching_dex': {p.name: sha(p) for p in dex},
    'zipalign': alignment, 'apk_v1_and_v2_signatures_verified': True, 'zip_crc_verified': True,
    'gesture_classifier_checks': tests.strip(), 'launcher_build': 'PASS',
    'r2_system_backup_sha256': BASELINE_SHA,
    'device_installation': 'NOT_ATTEMPTED_USER_REQUESTED_OFFLINE',
    'device_gesture_acceptance': 'PENDING',
}
(DEST/'verification.json').write_text(json.dumps(report, indent=2)+'\n')
(DEST/'SHA256SUMS.txt').write_text(sha(apk)+'  '+apk.name+'\n')
# Only final APK, original rollback reference and verification records are retained.
unsigned.unlink()
aligned.unlink()
print(json.dumps(report, indent=2))
