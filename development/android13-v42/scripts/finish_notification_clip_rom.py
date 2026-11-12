"""Export, verify and install the integrated notification ROM with one full boot."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys
parser=argparse.ArgumentParser();parser.add_argument('--build-log',required=True);args=parser.parse_args()
p=Path(__file__).resolve().parents[1]
linux='/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110/scripts/'
a=p/'artifacts/lineage20-rom-v27';e=p/'evidence/offline-v40'
subprocess.run(['wsl','-d','T110Build','--','bash',linux+'export_native_wallpaper_system.sh','27',args.build_log],check=True)
subprocess.run([sys.executable,str(p/'scripts/verify_exported_system.py'),str(a),'--build-log',args.build_log],check=True)
contents=json.loads((e/'contents.json').read_text());host=json.loads((a/'host-verification.json').read_text())
assert contents['status']=='PASS' and host['status']=='VERIFIED'
assert host['sha256']==contents['system_sha256']
pair=dict(status='OFFLINE_VERIFIED_NOT_BOOT_TESTED',system_artifact='system.raw.img',system_sha256=host['sha256'],system_md5=host['md5'],system_bytes=host['bytes'],boot_artifact='../android13-boot-v29/KERNEL.img',boot_sha256=contents['boot_sha256'],boot_md5=contents['boot_md5'],existing_boot_reused=True,data_preserved=True,fixes=['0076 finite notification row clips on T110 raster Canvas; native rounded shade retained'],hardware_validated=False,limitations=['Camera unported','Software UI remains slow'])
(a/'rom-pair.json').write_text(json.dumps(pair,indent=2)+'\n')
(a/'README.md').write_text('''# SM-T110 LineageOS20 system v27

Integrates patch0076, finite notification clip bounds for the T110 raster Canvas.
Native rounded shade, notifications, gestures, wallpaper settings, hardware/onscreen
navigation switch and other v26 features retained. Matched BOOTv29 unchanged.

Filesystem, fit, native/Windows hashes, unchanged components, APK certificate and
compiled clipping method verified. Installation and actual boot/visual result are
recorded in ../../evidence/offline-v40/installation.json and runtime.json.
Camera and general graphics performance remain unresolved. No blanket hardware pass.

Use the verified recovery image-on-userdata staging method. Do not flash the raw
system file directly to the old faulty SYSTEM partition. See CURRENT-STATUS.md.
''')
print('INTEGRATED_NOTIFICATION_ROM_EXPORTED_AND_VERIFIED',flush=True)
subprocess.run(['wsl','--terminate','T110Build'],check=True)
subprocess.run([sys.executable,str(p/'scripts/install_native_wallpaper_system.py'),'--system-version','27','--previous-version','26','--evidence','offline-v40','--expected-boot','9f48e9ba-49c8-4cf8-a1f2-0fca599e83c1'],check=True)
