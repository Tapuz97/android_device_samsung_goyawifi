"""Generate an allow-all SELinux policy ONLY for the isolated QEMU test.
It is not device policy and must never be included in a tablet ROM.
"""
from pathlib import Path
import re,subprocess
base=Path('/root/t110-build')
expanded=subprocess.check_output(['gcc','-E','-P','-x','c',str(base/'kernel-policy30/security/selinux/include/classmap.h')],text=True)
(base/'qemu-classmap-expanded.txt').write_text(expanded)
s=expanded;classes=[]
for name,body in re.findall(r'\{\s*"([a-z0-9_]+)"\s*,\s*\{([^}]+)\}',s):
 perms=re.findall(r'"([a-z0-9_]+)"',body);classes.append((name,perms))
assert len(classes)>40
sidtext=(base/'kernel-policy30/security/selinux/include/initial_sid_to_string.h').read_text();sids=re.findall(r'"([a-z0-9_]+)"',sidtext)[1:]
lines=['; TEST ONLY: allow-all QEMU policy. Never use on tablet.','(handleunknown deny)','(mls false)','(sensitivity s0)','(sensitivityorder (s0))','(level low (s0))','(type kernel_t)','(role system_r)','(role object_r)','(roletype system_r kernel_t)','(roletype object_r kernel_t)','(user system_u)','(userrole system_u system_r)','(userrole system_u object_r)','(userlevel system_u low)','(userrange system_u (low low))']
for name,perms in classes:lines.append('(class '+name+' ('+' '.join(perms)+'))')
lines.append('(classorder ('+' '.join(n for n,p in classes)+'))')
for sid in sids:lines.append('(sid '+sid+')')
lines.append('(sidorder ('+' '.join(sids)+'))')
for sid in sids:lines.append('(sidcontext '+sid+' (system_u system_r kernel_t (low low)))')
for name,perms in classes:lines.append('(allow kernel_t kernel_t ('+name+' ('+' '.join(perms)+')))')
lines.append('(allowx kernel_t kernel_t (ioctl chr_file (range 0x0000 0xffff)))')
p=base/'qemu-policy30.cil';p.write_text('\n'.join(lines)+'\n')
subprocess.run(['secilc','-M','false','-c','30','-o',str(base/'qemu-policy30.bin'),'-f',str(base/'qemu-policy30-file-contexts'),str(p)],check=True)
print('Generated QEMU policy:',len(classes),'classes,',len(sids),'initial SIDs')
