"""Install the signed Settings repair on the verified current boot."""
from pathlib import Path
import argparse, hashlib, json, os, re, subprocess, zipfile

parser = argparse.ArgumentParser()
parser.add_argument('--expected-boot', default='e7d5592a-6995-482f-a2e3-25e2741ebf95')
parser.add_argument('--expected-server', default='378')
args = parser.parse_args()

p = Path(__file__).resolve().parents[1]
e = p / 'evidence/offline-v36/settings-candidate'
e.mkdir(parents=True, exist_ok=True)
sdk = Path(os.environ['LOCALAPPDATA']) / 'Android/Sdk'
bt = sdk / 'build-tools/36.0.0'
adb = [str(sdk / 'platform-tools/adb.exe'), '-s', 'T110_ADB_SERIAL']
def call(args, timeout=45):
    r = subprocess.run(args, capture_output=True, timeout=timeout)
    assert r.returncode == 0, (args, r.stdout.decode(errors='replace'), r.stderr.decode(errors='replace'))
    return r.stdout
def sh(cmd, timeout=45): return call(adb + ['shell', cmd], timeout).decode().strip()
before = sh('cat /proc/sys/kernel/random/boot_id; pidof system_server').splitlines()
assert before == [args.expected_boot, args.expected_server], before
assert sh('cat /sys/block/mmcblk0/device/cid') == '1101003030384745T110_ADB_SERIAL'
assert sh('sha256sum /dev/block/mmcblk0p10').split()[0] == 'f3b0cba693c938a60d58cf5ef569a36ee82d2874e858e4a3a6999f8d2385d35d'
assert sh('sha256sum /system/framework/services.jar').split()[0] == '427754c42b4cd44803bf3ab90aeaac5c98756a20b637c2685d449a9bcef0abc3'
apk = e / 'Settings.apk'
original = e / 'Settings-original.apk'
current_path = sh('pm path com.android.settings').removeprefix('package:')
if current_path != '/system/system_ext/priv-app/Settings/Settings.apk':
    previous = json.loads((e/'installation.json').read_text())
    assert current_path == previous['installed_path']
    assert sh('sha256sum ' + current_path).split()[0] == previous['sha256']
    rollback = e/'Settings-previous-installed.apk'
    call(adb+['pull',current_path,str(rollback)],90)
    assert hashlib.sha256(rollback.read_bytes()).hexdigest() == previous['sha256']
call(adb + ['pull', '/system/system_ext/priv-app/Settings/Settings.apk', str(original)], 90)
signer = ['java', '--enable-native-access=ALL-UNNAMED', '-cp', str(bt / 'lib/apksigner.jar'),
          'com.android.apksigner.ApkSignerTool', 'verify', '--print-certs']
sig = call(signer + [str(apk)]).decode()
old = call(signer + [str(original)]).decode()
cert = lambda s: re.search(r'certificate SHA-256 digest: ([0-9a-f]{64})', s)[1]
assert cert(sig) == cert(old)
manifest = call([str(bt/'aapt2.exe'), 'dump', 'xmltree', '--file', 'AndroidManifest.xml', str(apk)]).decode()
assert 'package="com.android.settings"' in manifest
with zipfile.ZipFile(apk) as z:
    dex = b''.join(z.read(n) for n in z.namelist() if n.endswith('.dex'))
assert b't110_bringup' in dex and b'getEthernetManager' in dex and b'isServiceAvailable' in dex
digest = hashlib.sha256(apk.read_bytes()).hexdigest()
assert digest != hashlib.sha256(original.read_bytes()).hexdigest()
(e/'signature.txt').write_text(sig, encoding='utf-8')
(e/'manifest.txt').write_text(manifest, encoding='utf-8')
result = call(adb + ['install', '-r', '-t', '--no-streaming', str(apk)], 180).decode()
assert 'Success' in result, result
path = sh('pm path com.android.settings').removeprefix('package:')
assert path.startswith('/data/app/') and '\n' not in path
assert sh('sha256sum ' + path).split()[0] == digest
report = dict(status='INSTALLED_RUNTIME_PENDING', sha256=digest, certificate_sha256=cert(sig),
              installed_path=path, original_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),
              boot_and_server=before, additional_boots=0)
(e/'installation.json').write_text(json.dumps(report, indent=2)+'\n')
print('SETTINGS_INSTALLED_AND_HASH_VERIFIED', flush=True)
assert 'Success' in sh('cmd package compile -m speed -f com.android.settings', 300)
sh('am force-stop com.android.settings')
assert sh('cat /proc/sys/kernel/random/boot_id; pidof system_server').splitlines() == before
report['compilation'] = 'speed'
(e/'installation.json').write_text(json.dumps(report, indent=2)+'\n')
print('SETTINGS_COMPILED_SAME_BOOT', flush=True)
