"""Export/run the bounded offscreen renderer without replacing OS components."""
from pathlib import Path
import subprocess,os,json,hashlib,time,re
p=Path(__file__).resolve().parents[1];e=p/'evidence/offline-v41';e.mkdir(exist_ok=True)
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(s,timeout=30,check=True):return subprocess.run(adb+['shell',s],capture_output=True,timeout=timeout,check=check)
assert sh('cat /sys/block/mmcblk0/device/cid').stdout.decode().strip()=='1101003030384745T110_ADB_SERIAL'
before=sh('cat /proc/sys/kernel/random/boot_id; pidof system_server').stdout.decode().splitlines()
export_code="""from pathlib import Path
out=Path('/root/t110-build/out-native/soong/.intermediates/device/samsung/t110_bringup')
dest=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110/evidence/offline-v41')
for name in ['t110_gpu_readback_probe','t110_graphic_import_probe']:
    source=out/name/'android_arm_armv7-a-neon_cortex-a9'/name
    (dest/name).write_bytes(source.read_bytes())
"""
subprocess.run(['wsl.exe','-d','Ubuntu','--exec','python3','-c',export_code],check=True,timeout=60)
probe=e/'t110_gpu_readback_probe';receiver=e/'t110_graphic_import_probe'
lib=p/'evidence/remote-fixes-20261110/libui-candidate/libui.so'
remote='/data/local/tmp/t110-gpu-readback';sh('mkdir -p '+remote)
hashes={}
for file in [probe,receiver,lib]:
    data=file.read_bytes();assert data[:5]==b'\x7fELF\x01';hashes[file.name]=hashlib.sha256(data).hexdigest()
    subprocess.run(adb+['push',str(file),remote+'/'+file.name],capture_output=True,timeout=30,check=True)
    assert sh('sha256sum '+remote+'/'+file.name).stdout.decode().split()[0]==hashes[file.name]
sh('chmod 0755 '+remote+'/t110_gpu_readback_probe '+remote+'/t110_graphic_import_probe')
run=sh('LD_LIBRARY_PATH='+remote+' timeout 90 '+remote+'/t110_gpu_readback_probe',timeout=100,check=False)
(e/'gpu-readback.txt').write_bytes(run.stdout+b'\nSTDERR\n'+run.stderr)
after=sh('cat /proc/sys/kernel/random/boot_id; pidof system_server').stdout.decode().splitlines();assert before==after
source_hashes={name:hashlib.sha256((p/'work/device/samsung/t110_bringup/graphics'/name).read_bytes()).hexdigest() for name in ['gpu_readback_probe.cpp','T110EglWindow.cpp','T110EglWindow.h','T110WindowSlots.h']}
record={'returncode':run.returncode,'boot_and_server':after,'additional_boots':0,'display_services_modified':False,'hashes':hashes,'source_hashes':source_hashes,'rows':run.stdout.decode().splitlines(),'host_epoch':time.time()}
(e/'gpu-readback.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
