from pathlib import Path
import json,hashlib,shutil
root=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');base=Path('/root/t110-build')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,o):p.write_text(json.dumps(o,indent=2)+'\n')
dest=root/'artifacts/kernel-binder';dest.mkdir(exist_ok=True)
for src,name in [(base/'out-binder/arch/arm/boot/zImage','zImage'),(base/'out-binder/.config','kernel.config'),(base/'logs/binder-t110-build.log','build.log')]:shutil.copy2(src,dest/name)
meta=json.loads((root/'artifacts/kernel-policy30/build-provenance.json').read_text());meta['patches'].append({'file':'patches/0007-binder-lsm-hooks.patch','sha256':sha(root/'patches/0007-binder-lsm-hooks.patch')});meta['sha256']=sha(dest/'zImage');meta['bytes']=(dest/'zImage').stat().st_size;meta['config_sha256']=sha(dest/'kernel.config');meta['runtime_validation']='12 checks pass under QEMU Cortex-A9, including cross-process Binder and SELinux-enforced Binder denial; not hardware validation';meta['remaining'][1]='Modern Binder features: hwbinder/multiple contexts, scatter-gather and PTR/FDA objects; transaction security contexts'
dump(dest/'build-provenance.json',meta)
dest=root/'artifacts/qemu-binder';dest.mkdir(exist_ok=True)
for src,name in [(base/'out-qemu-binder/arch/arm/boot/zImage','zImage'),(base/'out-qemu-binder/.config','kernel.config'),(base/'logs/qemu-binder-test.log','test.log'),(base/'qemu-binder-initramfs.cpio.gz','initramfs.cpio.gz'),(base/'qemu-policy30.cil','TEST-ONLY-policy.cil'),(base/'qemu-policy30-deny-binder.cil','TEST-ONLY-deny-binder.cil'),(root/'scripts/seccomp_arm_test.c','seccomp_arm_test.c'),(root/'scripts/binder_arm_test.h','binder_arm_test.h')]:shutil.copy2(src,dest/name)
log=(dest/'test.log').read_text(errors='replace');passes=[l.strip() for l in log.splitlines() if l.startswith('PASS ')]
assert len(passes)==12 and 'RESULT failures=0' in log and '\nFAIL ' not in log and 'tclass=binder permissive=0' in log
dump(dest/'validation.json',{'status':'PASS','tests':passes,'machine':'QEMU vexpress-a9 Cortex-A9, 2 CPUs, 256 MiB','scope':'Policy30 parser + seccomp semantics + Binder protocol7 roundtrip + enforcing denial of Binder call','limitations':['Synthetic policies only, never use on tablet','Binder transfer-binder and transfer-file hooks not separately exercised','Not a modern Android libbinder/libhwbinder runtime test','No T110 board/hardware test'],'files':{p.name:sha(p) for p in dest.iterdir() if p.is_file() and p.name != "validation.json"}})
print('Archived final kernel SHA256',meta['sha256']);print('Archived',len(passes),'passing QEMU checks')