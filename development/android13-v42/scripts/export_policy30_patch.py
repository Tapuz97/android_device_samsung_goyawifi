from pathlib import Path
import difflib
root=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
a=Path('/root/t110-build/kernel-modern'); b=Path('/root/t110-build/kernel-policy30')
paths=[Path(x) for x in ['include/linux/security.h','include/linux/lsm_audit.h','security/security.c','security/capability.c','security/lsm_audit.c']]
paths+= [p.relative_to(b) for p in sorted((b/'security/selinux').rglob('*')) if p.is_file()]
patch=[]
for rel in paths:
    before=(a/rel).read_text() if (a/rel).exists() else "";after=(b/rel).read_text()
    if before!=after:
        patch.extend(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/'+str(rel) if (a/rel).exists() else '/dev/null',tofile='b/'+str(rel)))
(root/'patches/0006-selinux-policy30-backport.patch').write_text(''.join(patch))
print('Exported SELinux delta, lines:',len(patch))