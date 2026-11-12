from pathlib import Path
import json, hashlib, shutil, subprocess
root=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');base=Path('/root/t110-build')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,obj):p.write_text(json.dumps(obj,indent=2)+'\n')
base_rev='3c50b450af74d42f8c5d360c692f71002b3bb0af';donor_rev='40bb591cb6abaf540bf9a988e3fac0ca86368865';tool_rev='b4ecd7806d8f46cddeacaf9f8de92c191fb266e4'
for name,out,log,patches in [('kernel-seccomp','out-modern','modern-build-final.log',['0004-seccomp-arm-tsync-backport.patch','0005-qemu-debug-header-guard.patch']),('kernel-policy30','out-policy30','policy30-build-retry.log',['0004-seccomp-arm-tsync-backport.patch','0005-qemu-debug-header-guard.patch','0006-selinux-policy30-backport.patch'])]:
 dest=root/'artifacts'/name;dest.mkdir(exist_ok=True)
 for src,filename in [(base/out/'arch/arm/boot/zImage','zImage'),(base/out/'.config','kernel.config'),(base/'logs'/log,'build.log')]:shutil.copy2(src,dest/filename)
 dump(dest/'build-provenance.json',{'status':'COMPILED FOR T110; NOT TABLET BOOT TESTED; NOT A COMPLETE ANDROID ROM','kernel_revision':base_rev,'donor':{'url':'https://android.googlesource.com/kernel/common','branch':'deprecated/android-3.4','commit':donor_rev},'toolchain_revision':tool_rev,'patches':[{'file':'patches/'+p,'sha256':sha(root/'patches'/p)} for p in patches],'config_sha256':sha(dest/'kernel.config'),'sha256':sha(dest/'zImage'),'bytes':(dest/'zImage').stat().st_size,'runtime_validation':'Related vexpress Cortex-A9 build from same patched source, NOT Marvell device emulation','remaining':['Hardware boot checkpoint','Binder ABI and feature integration','Android init, policy, HALs and userspace','Persistent stock SYSTEM read failure']})
dest=root/'artifacts/qemu-policy30';dest.mkdir(exist_ok=True)
for src,filename in [(base/'out-qemu-policy30/arch/arm/boot/zImage','zImage'),(base/'out-qemu-policy30/.config','kernel.config'),(base/'logs/qemu-policy30-test.log','test.log'),(base/'qemu-policy30-initramfs.cpio.gz','initramfs.cpio.gz'),(base/'qemu-policy30.cil','TEST-ONLY-policy.cil'),(base/'qemu-policy30.bin','TEST-ONLY-policy.bin')]:shutil.copy2(src,dest/filename)
log=(dest/'test.log').read_text(errors='replace');passes=[l.strip() for l in log.splitlines() if l.startswith('PASS ')]
assert len(passes)==10 and 'RESULT failures=0' in log and '\nFAIL ' not in log
meta={'status':'PASS','tests':passes,'machine':'QEMU vexpress-a9, Cortex-A9, 2 CPUs, 256 MiB','selinux':'permissive; synthetic allow-all policy version 30 with ioctl xperms; parser validation only','not_validated':['T110 board drivers/hardware boot','Android policy compilation/loading','SELinux enforcement completeness','Complete Android 13 userspace'],'files':{p.name:sha(p) for p in dest.iterdir() if p.is_file() and p.name != "validation.json"}}
dump(dest/'validation.json',meta)
lock=json.loads((root/'sources.lock.json').read_text())
for entry in [{'directory':'WSL:/root/t110-build/kernel','url':'https://github.com/visyone/android_kernel_samsung_goya.git','commit':base_rev},{'directory':'WSL:/root/t110-build/android-common-3.4','url':'https://android.googlesource.com/kernel/common','branch':'deprecated/android-3.4','commit':donor_rev},{'directory':'WSL:/root/t110-build/toolchain','url':'https://android.googlesource.com/platform/prebuilts/gcc/linux-x86/arm/arm-eabi-4.6','commit':tool_rev}]:
 if not any(x['directory']==entry['directory'] for x in lock):lock.append(entry)
dump(root/'sources.lock.json',lock)
print(json.dumps({'artifacts_saved':True,'policy30_zimage_sha256':sha(root/'artifacts/kernel-policy30/zImage'),'qemu_passes':len(passes)},indent=2))