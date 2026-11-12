from pathlib import Path
import subprocess,json,shutil
r=Path('/root/t110-build/kernel-display-i2c')
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
def git(*a):return subprocess.check_output(['git','-C',str(r),*a],text=True).strip()
assert git('rev-parse','HEAD')=='3c50b450af74d42f8c5d360c692f71002b3bb0af'
# Preserve only real modified tracked source. ZIP-exported symlink placeholders
# are not intentional changes and remain private in the exact source archive.
rows=subprocess.check_output(['git','-C',str(r),'status','--porcelain','--untracked-files=normal'],text=True).splitlines()
modified=[line[3:] for line in rows if line[:2].strip()=='M']
new=['Documentation/prctl/seccomp_filter.txt','arch/arm/include/asm/syscall.h',
     'drivers/staging/android/binder_compat34.h','drivers/staging/android/uapi',
     'include/trace/events/random.h']
config=r/'arch/arm/configs/t110_android13_v42_defconfig'
shutil.copyfile(p/'evidence/ui-system-hang-20261112/kernel-standard-reclaim.config',config)
doc=r/'Documentation/t110-android13-checkpoint.md'
doc.write_text('''# SM-T110 Android13 v42 kernel source checkpoint

WIP bring-up source, not an official LineageOS release or Nougat qualification.
Base:3c50b450af74d42f8c5d360c692f71002b3bb0af.
The installed v42/BOOT48 uses the standard-reclaim kernel with the paired native
hardware modules. Its logging/memory defaults were verified; physical display
wake, UI responsiveness and remaining hardware functions are not fully working.

This branch preserves the accumulated ARM syscall, Binder, SELinux, USB,
capabilities, network, ION, shared display/touch-I2C and logging work. The tested
full configuration is arch/arm/configs/t110_android13_v42_defconfig. Compile with
the recorded Android ARM GCC4.6 toolchain and the original image layout; this
commit alone is not a flash package. Preserve recovery and original firmware.

Device/bootstrap source and numbered patches:
https://github.com/Tapuz97/android_device_samsung_goyawifi/tree/t110/android13-v42-checkpoint

Before a full Android7.1 product build, validate legacy HWC1/EGL/gralloc ABI,
real GPU app drawing and physical panel/touch/system suspend-resume separately.
Do not import every Android13 compatibility backport as a Nougat requirement.

Generated modules/objects, scratch .orig files and ZIP-converted symlink
placeholders are excluded. Their exact private originals remain in the owner
backup. Upstream symlinks retain their original Git representation here.
''')
git('add','--',*modified,*new,str(config.relative_to(r)),str(doc.relative_to(r)))
git('config','user.name','Gal Mitrani');git('config','user.email','103029727+Tapuz97@users.noreply.github.com')
git('commit','-m','goya: preserve Android13 v42 bring-up source and tested config')
head=git('rev-parse','HEAD')
bundle=p/'backups/android13-before-lineage14-20261112/kernel-v42-checkpoint.bundle'
git('bundle','create',str(bundle),'3c50b450af74d42f8c5d360c692f71002b3bb0af..HEAD')
result={'commit':head,'branch':'t110/android13-v42-checkpoint','base':'3c50b450af74d42f8c5d360c692f71002b3bb0af',
        'tracked_source_files':len(modified),'bundle':str(bundle),'pushed':False}
(p/'community/kernel-checkpoint-commit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2),flush=True)
