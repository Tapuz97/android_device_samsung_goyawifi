"""Port reviewed seccomp/no_new_privs hunks from pinned Android common 3.4.
Run only on clean kernel-modern worktree. Preserves Marvell board/driver code.
"""
from pathlib import Path
import re,difflib,subprocess,shutil
base=Path('/root/t110-build/kernel-modern');donor=Path('/root/t110-build/android-common-3.4')
assert subprocess.check_output(['git','-C',str(donor),'rev-parse','HEAD'],text=True).strip()=='40bb591cb6abaf540bf9a988e3fac0ca86368865'
assert not subprocess.check_output(['git','-C',str(base),'status','--porcelain'],text=True).strip()
selection={
 'kernel/fork.c':'.',
 'arch/arm/kernel/traps.c':'Emulate/fallthrough',
 'include/linux/audit.h':'audit_seccomp',
 'kernel/auditsc.c':'.',
 'include/linux/sched.h':'thread_head|thread_node|atomic_flags|struct seccomp|PFA_NO_NEW_PRIVS|for_each_thread',
 'include/linux/init_task.h':'thread_head|thread_node',
 'kernel/exit.c':'thread_node',
 'include/linux/ptrace.h':'.',
 'include/linux/filter.h':'.',
 'net/core/filter.c':'.',
 'include/linux/security.h':'LSM_UNSAFE_NO_NEW_PRIVS',
 'security/commoncap.c':'.',
 'security/selinux/hooks.c':'LSM_UNSAFE_NO_NEW_PRIVS',
 'fs/exec.c':'no_new_privs|seccomp thread-sync',
 'include/asm-generic/siginfo.h':'.',
 'kernel/signal.c':'SIGSYS|__SI_SYS',
 'arch/arm/kernel/calls.S':'.',
 'arch/arm/include/asm/unistd.h':'.',
 'include/linux/syscalls.h':'sys_seccomp',
 'kernel/sys_ni.c':'sys_seccomp',
 'arch/arm/kernel/ptrace.c':'tracehook.h|current_thread_info|ptrace_report_syscall',
}
patch=''
for file,pattern in selection.items():
 a=(base/file).read_text();b=(donor/file).read_text();lines=list(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='a/'+file,tofile='b/'+file));hunks=[]
 for line in lines[2:]:
  if line.startswith('@@'):hunks.append([])
  hunks[-1].append(line)
 picked=[''.join(h) for h in hunks if re.search(pattern,''.join(h))]
 assert picked,file
 patch+=''.join(lines[:2])+''.join(picked)
p=Path('/root/t110-build/seccomp-selected.patch');p.write_text(patch)
subprocess.run(['git','-C',str(base),'apply','--check',str(p)],check=True)
subprocess.run(['git','-C',str(base),'apply',str(p)],check=True)
for file in ['kernel/seccomp.c','include/linux/seccomp.h','arch/arm/include/asm/syscall.h','Documentation/prctl/seccomp_filter.txt']:
 (base/file).parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(donor/file,base/file)
def replace(file,old,new):
 p=base/file;s=p.read_text();assert s.count(old)==1,(file,old);p.write_text(s.replace(old,new))
replace('arch/arm/Kconfig','\tselect HAVE_ARCH_KGDB','\tselect HAVE_ARCH_SECCOMP_FILTER\n\tselect HAVE_ARCH_KGDB')
s=(donor/'arch/Kconfig').read_text();block=s[s.index('config HAVE_ARCH_SECCOMP_FILTER'):s.index('config HAVE_ARCH_MMAP_RND_BITS')]
replace('arch/Kconfig','source "kernel/gcov/Kconfig"',block+'source "kernel/gcov/Kconfig"')
s=(donor/'include/linux/prctl.h').read_text();block=s[s.index('/*\n * If no_new_privs'):s.index('#endif /* _LINUX_PRCTL_H */')]
replace('include/linux/prctl.h','#endif /* _LINUX_PRCTL_H */',block+'#endif /* _LINUX_PRCTL_H */')
replace('kernel/sys.c','prctl_set_seccomp(arg2);','prctl_set_seccomp(arg2, (char __user *)arg3);')
s=(donor/'kernel/sys.c').read_text();start=s.index('\t\tcase PR_SET_NO_NEW_PRIVS:');end=s.index('\t\tdefault:',start);block=s[start:end]
replace('kernel/sys.c','\t\tdefault:\n\t\t\terror = -EINVAL;\n\t\t\tbreak;\n\t}\n\treturn error;',''+block+'\t\tdefault:\n\t\t\terror = -EINVAL;\n\t\t\tbreak;\n\t}\n\treturn error;')
p=base/'arch/arm/kernel/entry-common.S';s=p.read_text();start=s.index('#ifdef CONFIG_SECCOMP\n\ttst\tr10, #_TIF_SECCOMP');end=s.index('#endif',start)+len('#endif');s=s[:start]+'#ifdef CONFIG_SECCOMP\n\ttst\tr10, #_TIF_SECCOMP\n\tbne\t__sys_trace\n#endif'+s[end:];s=s.replace('\tldmccia\tr1, {r0 - r3}\t\t\t@ have to reload r0 - r3','\tldmccia\tr1, {r0 - r6}\t\t\t@ have to reload r0 - r6\n\tstmccia\tsp, {r4, r5}\t\t\t@ and update the stack args');p.write_text(s)
print('Applied selected seccomp and no_new_privs integration')
