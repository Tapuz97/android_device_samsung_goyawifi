"""Reproduce codec linker isolation in a private native process; do not replace services."""
from pathlib import Path
import hashlib,json,os,subprocess
p=Path(__file__).resolve().parents[1];e=p/'evidence/offline-v41/boot32-test'
a=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(s):return subprocess.check_output(a+['shell',s],timeout=40)
before=sh('cat /proc/sys/kernel/random/boot_id; pidof system_server').decode().splitlines()
assert before==['046c74cc-c706-4b07-8105-bd06c5818ffe','304']
config=sh('cat /linkerconfig/com.android.media.swcodec/ld.config.txt').decode();(e/'codec-linker-config.txt').write_text(config)
libs=[]
for line in config.splitlines():
    if line.startswith('namespace.default.link.system.shared_libs '):
        for name in line.split('=',1)[1].strip().split(':'):
            if name not in libs:libs.append(name)
assert 'libvndksupport.so' in libs and 'libhardware.so' not in libs
(e/'codec-shared-libraries.txt').write_text(':'.join(libs))
source='/root/t110-build/out-native/soong/.intermediates/device/samsung/t110_bringup/t110_codec_loader_probe/android_arm_armv7-a-neon_cortex-a9/t110_codec_loader_probe'
destination='/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110/evidence/offline-v41/boot32-test/t110_codec_loader_probe'
export='from pathlib import Path; Path('+repr(destination)+').write_bytes(Path('+repr(source)+').read_bytes())'
subprocess.run(['wsl','-d','Ubuntu','--exec','python3','-c',export],check=True,timeout=45)
remote='/data/local/tmp/t110-codec-loader-probe';sh('test ! -L '+remote+' && mkdir -p '+remote)
try:
    for name in ['codec-shared-libraries.txt','t110_codec_loader_probe']:
        subprocess.run(a+['push',str(e/name),remote+'/'+name],capture_output=True,check=True,timeout=30)
        assert sh('sha256sum '+remote+'/'+name).decode().split()[0]==hashlib.sha256((e/name).read_bytes()).hexdigest()
    sh('chmod 700 '+remote+'/t110_codec_loader_probe')
    r=subprocess.run(a+['shell',remote+'/t110_codec_loader_probe '+remote+'/codec-shared-libraries.txt'],capture_output=True,timeout=45)
    (e/'codec-loader-probe.txt').write_bytes(r.stdout+b'\nSTDERR\n'+r.stderr)
    after=sh('cat /proc/sys/kernel/random/boot_id; pidof system_server').decode().splitlines();assert after==before
    (e/'codec-loader-probe.json').write_text(json.dumps({'exit':r.returncode,'boot_and_server':after,'isolated_namespace_matches_codec_paths_and_exports':True,'shared_libraries':libs,'probe_sha256':hashlib.sha256((e/'t110_codec_loader_probe').read_bytes()).hexdigest(),'rom_changed':False,'service_restarted':False},indent=2)+'\n')
    print('probe_exit',r.returncode);print(r.stdout.decode(errors='replace'));print(r.stderr.decode(errors='replace'))
finally:
    sh('rm -f '+remote+'/t110_codec_loader_probe '+remote+'/codec-shared-libraries.txt')
    subprocess.run(a+['shell','rmdir '+remote],capture_output=True,timeout=15)
