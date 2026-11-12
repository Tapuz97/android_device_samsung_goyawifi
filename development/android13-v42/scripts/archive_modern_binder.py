from pathlib import Path
import json,hashlib,shutil,shlex
root=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');base=Path('/root/t110-build')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,obj):p.write_text(json.dumps(obj,indent=2)+'\n')
# Require successful final builds and exact source reproduction before archiving.
for mode in ['qemu','t110']:
 log=base/(f'logs/binder-modern-{mode}-final.log' if mode=='qemu' else 'logs/binder-modern-t110-build.log')
 assert 'Kernel: arch/arm/boot/zImage is ready' in log.read_text(),f'Incomplete build: {mode}'
for output in ['out-binder-modern','out-qemu-binder-modern']:
 config=(base/output/'.config').read_text()
 for required in ['CONFIG_ANDROID_BINDER_IPC=y','CONFIG_ANDROID_BINDER_IPC_32BIT=y','CONFIG_ANDROID_BINDER_DEVICES="binder,hwbinder,vndbinder"','# CONFIG_USER_NS is not set']:
  assert required in config, (output,required)
verification=json.loads((root/'evidence/binder-modern-source-verification.json').read_text())
for f,digest in verification['files'].items():assert sha(base/'kernel-binder-modern'/f)==digest,f
patch=root/'patches/0008-binder-contexts-scatter-gather-backport.patch'
assert sha(patch)==verification['patch_sha256']
qlog=base/'logs/qemu-binder-modern-test.log';log=qlog.read_text(errors='replace');passes=[l.strip() for l in log.splitlines() if l.startswith('PASS ')]
assert len(passes)==18 and 'RESULT failures=0' in log and '\nFAIL ' not in log
assert 'tclass=binder permissive=0' in log and 'PASS Binder denied manager leaves context unclaimed' in log
for marker in ['Kernel panic','BUG:','Unable to handle kernel']:assert marker not in log
meta=json.loads((root/'artifacts/kernel-binder/build-provenance.json').read_text())
meta['patches'].append({'file':'patches/'+patch.name,'sha256':sha(patch)})
meta['binder_donor']={'url':'https://android.googlesource.com/kernel/common','branch':'deprecated/android-3.18-n-release','commit':'71c88531171e6a1eb49da78e8260475310dc1e81','snapshot':'evidence/binder-donor-3.18-n/source-lock.json'}
meta['changes']=['Independent binder/hwbinder/vndbinder contexts','Scatter-gather transactions, nested PTR and FDA object transport','Local 3.4 UID/fd-table/list/freezer/vmalloc API adaptation; USER_NS excluded','Binder compiled with -w removed and -Werror enabled','LSM authorization before context-manager state mutation']
meta['remaining']=['Tablet hardware boot validation and persistent SYSTEM read fault','Actual Android 13 libbinder/libhwbinder runtime validation','Transaction security contexts and other newer optional driver features','Android init, policy, HAL and product integration']
meta['runtime_validation']='18 focused checks pass on vexpress Cortex-A9; not Marvell hardware emulation or a full Android runtime'
dest=root/'artifacts/kernel-binder-modern';dest.mkdir(exist_ok=True)
for src,name in [(base/'out-binder-modern/arch/arm/boot/zImage','zImage'),(base/'out-binder-modern/.config','kernel.config'),(base/'logs/binder-modern-t110-build.log','build.log'),(root/'evidence/binder-modern-source-verification.json','source-verification.json')]:shutil.copy2(src,dest/name)
meta['sha256']=sha(dest/'zImage');meta['bytes']=(dest/'zImage').stat().st_size;meta['config_sha256']=sha(dest/'kernel.config')
flags={}
for mode,out in [('t110','out-binder-modern'),('qemu','out-qemu-binder-modern')]:
 line=(base/out/'drivers/staging/android/.binder.o.cmd').read_text().splitlines()[0].split(' := ',1)[1];args=shlex.split(line)
 flags[mode]={'warnings_enabled':'-w' not in args,'warnings_as_errors':'-Werror' in args}
 assert all(flags[mode].values())
meta['binder_compiler_checks']=flags;dump(dest/'build-provenance.json',meta)
dest=root/'artifacts/qemu-binder-modern';dest.mkdir(exist_ok=True)
files=[(base/'out-qemu-binder-modern/arch/arm/boot/zImage','zImage'),(base/'out-qemu-binder-modern/.config','kernel.config'),(qlog,'test.log'),(base/'logs/qemu-binder-modern-manager-denial-reproduced.log','regression-before-fix.log'),(base/'qemu-binder-modern-initramfs.cpio.gz','initramfs.cpio.gz'),(base/'qemu-policy30.cil','TEST-ONLY-policy.cil'),(base/'qemu-policy30-deny-binder.cil','TEST-ONLY-deny-call.cil'),(base/'qemu-policy30-deny-manager.cil','TEST-ONLY-deny-manager.cil'),(root/'scripts/seccomp_binder_modern_test.c','seccomp_binder_modern_test.c'),(root/'scripts/binder_modern_arm_test.h','binder_modern_arm_test.h'),(root/'scripts/run_binder_modern_qemu.sh','run_binder_modern_qemu.sh')]
for src,name in files:shutil.copy2(src,dest/name)
dump(dest/'validation.json',{'status':'PASS','tests':passes,'machine':'QEMU vexpress-a9 Cortex-A9, SMP2, 256 MiB','scope':'Seccomp/SELinux regression suite, Binder context isolation, SG request/reply, FD array transfer/automatic cleanup, invalid-input rejection with continued operation, enforcing call/manager denial','limitations':['Synthetic SELinux policies: TEST ONLY','Not actual Android libbinder/libhwbinder userspace','No tablet boot/hardware validation','Not exhaustive Binder fuzzing, concurrency or security review'],'files':{p.name:sha(p) for p in dest.iterdir() if p.is_file() and p.name!='validation.json'}})
lock=json.loads((root/'sources.lock.json').read_text());entry={'directory':'evidence/binder-donor-3.18-n','url':'https://android.googlesource.com/kernel/common','branch':'deprecated/android-3.18-n-release','commit':'71c88531171e6a1eb49da78e8260475310dc1e81','scope':'Binder source snapshot only'}
if not any(x['directory']==entry['directory'] for x in lock):lock.append(entry)
dump(root/'sources.lock.json',lock)
print(json.dumps({'kernel_sha256':meta['sha256'],'bytes':meta['bytes'],'qemu_passes':len(passes),'binder_compiler_checks':flags},indent=2))
(root/'artifacts/kernel-binder-modern/STATUS.txt').write_text('COMPILED FOR T110; NOT HARDWARE BOOT TESTED. Binder enabled, USER_NS disabled, strict Binder compiler checks passed. 18 focused ARM QEMU tests pass. Not an Android 13 ROM. See build-provenance.json and ../qemu-binder-modern/validation.json.\n')
