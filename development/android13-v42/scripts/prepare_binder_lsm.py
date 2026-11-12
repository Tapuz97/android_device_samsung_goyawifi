from pathlib import Path
import difflib,subprocess
base=Path('/root/t110-build');root=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
rel=Path('drivers/staging/android/binder.c')
a=(base/'kernel-policy30'/rel).read_text();donor=(base/'android-common-3.4'/rel).read_text()
lines=list(difflib.unified_diff(a.splitlines(True),donor.splitlines(True),fromfile='a/'+str(rel),tofile='b/'+str(rel)))
head=lines[:2];hunks=[];cur=[]
for line in lines[2:]:
 if line.startswith('@@'):
  if cur:hunks.append(cur)
  cur=[]
 cur.append(line)
if cur:hunks.append(cur)
chosen=[h for h in hunks if any('security_binder_' in line or '+#include <linux/security.h>' in line for line in h)]
assert len(chosen)==6,len(chosen)
patch=''.join(head+sum(chosen,[]));p=root/'patches/0007-binder-lsm-hooks.patch';p.write_text(patch)
b=base/'kernel-binder'
if not b.exists():
 subprocess.run(['git','-C',str(base/'kernel'),'worktree','add','-b','codex/t110-binder-lsm',str(b),'3c50b450af74d42f8c5d360c692f71002b3bb0af'],check=True)
 for name in ['0004-seccomp-arm-tsync-backport.patch','0005-qemu-debug-header-guard.patch','0006-selinux-policy30-backport.patch','0007-binder-lsm-hooks.patch']:
  subprocess.run(['git','-C',str(b),'apply',str(root/'patches'/name)],check=True)
print('Prepared Binder LSM candidate; no ABI modernization claimed')