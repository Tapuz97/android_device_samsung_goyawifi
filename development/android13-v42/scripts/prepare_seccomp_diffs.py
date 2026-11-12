from pathlib import Path
import difflib
base=Path('/root/t110-build/kernel-modern');donor=Path('/root/t110-build/android-common-3.4');out=Path('/root/t110-build/seccomp-diffs');out.mkdir(exist_ok=True)
files=['arch/arm/include/asm/syscall.h','arch/arm/kernel/ptrace.c','arch/arm/kernel/entry-common.S','arch/arm/include/asm/thread_info.h','include/linux/sched.h','include/linux/ptrace.h','include/linux/prctl.h','include/linux/filter.h','net/core/filter.c','kernel/fork.c','kernel/sys.c','fs/exec.c','security/commoncap.c','security/selinux/hooks.c','include/linux/security.h','include/asm-generic/siginfo.h','kernel/signal.c','arch/arm/kernel/calls.S','arch/arm/include/asm/unistd.h','include/linux/syscalls.h','kernel/sys_ni.c','arch/Kconfig']
for f in files:
 a=(base/f).read_text() if (base/f).exists() else '';b=(donor/f).read_text();d=''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='a/'+f,tofile='b/'+f));(out/f.replace('/','_')).write_text(d)
print('Diffs saved',len(files))

