from pathlib import Path
import difflib,re,subprocess
base=Path('/root/t110-build/kernel-modern');donor=Path('/root/t110-build/android-common-3.4');patch=''
for f,pat in [('include/linux/audit.h','audit_seccomp'),('kernel/auditsc.c','.')]:
 lines=list(difflib.unified_diff((base/f).read_text().splitlines(True),(donor/f).read_text().splitlines(True),fromfile='a/'+f,tofile='b/'+f));h=[]
 for l in lines[2:]:
  if l.startswith('@@'):h.append([])
  h[-1].append(l)
 patch+=''.join(lines[:2])+''.join(''.join(x) for x in h if re.search(pat,''.join(x)))
p=Path('/root/t110-build/seccomp-audit.patch');p.write_text(patch);subprocess.run(['git','-C',str(base),'apply',str(p)],check=True)
