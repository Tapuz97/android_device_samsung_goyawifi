"""Archive the built kernel and module, preserving all prior artifacts."""
from pathlib import Path
import hashlib,json,shutil,subprocess
b=Path('/root/t110-build'); p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
src=b/'kernel-binder-secctx'; out=b/'out-binder-secctx'; dest=p/'artifacts/kernel-binder-secctx'
patch=p/'patches/0044-kernel-binder-security-context.patch'
subprocess.run(['patch','--dry-run','-R','-p1','-i',str(patch)],cwd=src,check=True)
assert (out/'.config').read_bytes()==(b/'out-alarm/.config').read_bytes(),'configuration drift'
assert json.loads((p/'evidence/offline-v25/regressions.json').read_text())['status']=='PASS'
modules=list(out.rglob('galcore.ko')); assert len(modules)==1
assert (out/'drivers/staging/android/binder.o').exists()
assert 'error:' not in (b/'logs/binder-secctx-build.log').read_text()
dest.mkdir(exist_ok=False)
sha=lambda data:hashlib.sha256(data).hexdigest()
files={}
for name,path in {'zImage':out/'arch/arm/boot/zImage','galcore.ko':modules[0],
                  'kernel.config':out/'.config','build.log':b/'logs/binder-secctx-build.log',
                  'binder.o':out/'drivers/staging/android/binder.o'}.items():
    shutil.copyfile(path,dest/name); data=path.read_bytes();files[name]=dict(bytes=len(data),sha256=sha(data))
provenance=dict(status='COMPILED_OFFLINE_CONTRACTS_PASSED_NOT_BOOT_TESTED',files=files,
    parent_kernel='artifacts/kernel-alarm/provenance.json',patch=str(patch.relative_to(p)),
    patch_sha256=sha(patch.read_bytes()),source_files={},hardware_validated=False,kernel_boots=0)
for name in ['drivers/staging/android/binder.c','drivers/staging/android/uapi/binder.h']:
    provenance['source_files'][name]=dict(before=sha((b/'kernel-alarm'/name).read_bytes()),after=sha((src/name).read_bytes()))
(dest/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
print(json.dumps(files,indent=2))
