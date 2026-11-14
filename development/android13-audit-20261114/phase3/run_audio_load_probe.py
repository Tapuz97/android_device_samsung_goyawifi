from pathlib import Path
import subprocess,shutil,json,os
r=Path('/root/t110-android13-audit');root=r/'loader-rootfs';ndk=Path('/root/t110-lineage14/android/prebuilts/ndk/current/platforms/android-23/arch-arm/usr/lib');base=Path('/root/t110-lineage14/android')
source=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110/android13-audit/AudioLoadProbe.c')
flags=['clang','--target=armv7a-linux-androideabi','-std=c11','-fno-builtin','-fPIE','-Wall','-Wextra','-Werror','-I'+str(r/'arm-headers')]
for p in ('bionic/libc/include','bionic/libc/arch-arm/include','bionic/libc/kernel/uapi','bionic/libc/kernel/uapi/asm-arm'):flags+=['-isystem',str(base/p)]
obj=r/'AudioLoadProbe.o';subprocess.run(flags+['-c',str(source),'-o',str(obj)],check=True)
gcc=next(Path('/root/t110-lineage14/toolchains/arm-linux-androideabi-4.6').glob('lib/gcc/arm-linux-androideabi/*/libgcc.a'))
binary=root/'data/local/tmp/audio-load-probe'
subprocess.run(['clang','--target=armv7a-linux-androideabi','-fuse-ld=lld','-pie','-nostdlib','-Wl,--no-undefined','-Wl,-dynamic-linker,/system/bin/linker',str(ndk/'crtbegin_dynamic.o'),str(obj),'-L'+str(r/'arm-checks/android13-providers'),'-lc','-lm','-ldl',str(gcc),str(ndk/'crtend_android.o'),'-o',str(binary)],check=True)
conf=root/'vendor/etc/alsa';conf.mkdir(parents=True,exist_ok=True)
stock=Path('/root/t110-lineage14/reference/stock-ani7/extracted')
shutil.copy2(stock/'etc/asound.conf',conf/'asound.conf')
text=(stock/'usr/share/alsa/alsa.conf').read_text().replace('"/etc/asound.conf"','"/vendor/etc/alsa/asound.conf"')
text+='\nctl_type.codec { lib "/vendor/lib/alsa-lib/libasound_module_ctl_codec.so" }\nctl_type.phone { lib "/vendor/lib/alsa-lib/libasound_module_ctl_phone.so" }\npcm_type.phone { lib "/vendor/lib/alsa-lib/libasound_module_pcm_phone.so" }\n'
(conf/'alsa.conf').write_text(text)
command=['unshare','--pid','--fork','--mount-proc','qemu-arm','-cpu','cortex-a9','-L',str(root),'-E','LD_LIBRARY_PATH=/vendor/lib:/system/lib','-E','ALSA_CONFIG_PATH=/vendor/etc/alsa/alsa.conf','-E','T110_PROBE_LEGACY_SDK=1',str(binary)]
p=subprocess.run(command,capture_output=True,text=True,timeout=30)
(r/'audio-load-probe.json').write_text(json.dumps(dict(command=command,exit=p.returncode,stdout=p.stdout,stderr=p.stderr,context='Offline QEMU, real Android13 Bionic/loader, explicit DT_NEEDED shims, diagnostic legacy SDK; production vendor namespace not represented',hardware_opened=False),indent=2)+'\n')
print(p.stdout+p.stderr,flush=True);raise SystemExit(p.returncode)
