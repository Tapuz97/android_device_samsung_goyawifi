from pathlib import Path
import subprocess
root=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');base=Path('/root/t110-build');target=base/'kernel-binder-modern';donor=root/'evidence/binder-donor-3.18-n'
if not target.exists():
 subprocess.run(['git','-C',str(base/'kernel'),'worktree','add','-b','codex/t110-binder-modern',str(target),'3c50b450af74d42f8c5d360c692f71002b3bb0af'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 for p in ['0004-seccomp-arm-tsync-backport.patch','0005-qemu-debug-header-guard.patch','0006-selinux-policy30-backport.patch','0007-binder-lsm-hooks.patch']:
  subprocess.run(['git','-C',str(target),'apply',str(root/'patches'/p)],check=True)
rel=Path('drivers/staging/android')
for f in ['binder.c','binder.h','binder_trace.h','uapi/binder.h']:
 p=target/rel/f;p.parent.mkdir(exist_ok=True);p.write_bytes((donor/f).read_bytes())
a=(target/rel/'Kconfig').read_text();dk=(donor/'Kconfig').read_text();start=dk.index('config ANDROID_BINDER_IPC\n');end=dk.index('config ASHMEM\n')
a=a[:a.index('config ANDROID_BINDER_IPC\n')]+dk[start:end]+a[a.index('config ASHMEM\n'):]
a=a.replace('depends on MMU','depends on MMU && !USER_NS',1);(target/rel/'Kconfig').write_text(a)
# Local 3.4 UID API: user namespaces are deliberately excluded in Kconfig.
p=target/rel/'binder.c';s=p.read_text();s=s.replace('kuid_t','uid_t').replace('INVALID_UID','((uid_t)-1)')
s=s.replace('from_kuid(current_user_ns(), t->sender_euid)','t->sender_euid').replace('from_kuid(&init_user_ns, curr_euid)','curr_euid').replace('from_kuid(&init_user_ns,\n\t\t\t\t\t context->binder_context_mgr_uid)','context->binder_context_mgr_uid')
s=s.replace('uid_valid(context->binder_context_mgr_uid)','(context->binder_context_mgr_uid != (uid_t)-1)').replace('uid_eq(context->binder_context_mgr_uid, curr_euid)','(context->binder_context_mgr_uid == curr_euid)')
# Retain the donor's files_lock lifetime protection around the original 3.4 fd-table operations.
old=(base/'kernel-binder'/rel/'binder.c').read_text();helpers='static '+old[old.index('int task_get_unused_fd_flags('):old.index('static inline void binder_lock(')]
for original,new in [('task_get_unused_fd_flags','binder34_alloc_fd'),('task_fd_install','binder34_install_fd'),('task_close_fd','binder34_close_fd')]:helpers=helpers.replace(original,new)
wrappers='''
/* Linux 3.4 file-table API, serialized with the donor's files lifetime lock. */
static int task_get_unused_fd_flags(struct binder_proc *proc, int flags)
{
 int ret;
 mutex_lock(&proc->files_lock);
 ret = binder34_alloc_fd(proc, flags);
 mutex_unlock(&proc->files_lock);
 return ret;
}
static void task_fd_install(struct binder_proc *proc, unsigned int fd, struct file *file)
{
 mutex_lock(&proc->files_lock);
 binder34_install_fd(proc, fd, file);
 mutex_unlock(&proc->files_lock);
}
static long task_close_fd(struct binder_proc *proc, unsigned int fd)
{
 long ret;
 mutex_lock(&proc->files_lock);
 ret = binder34_close_fd(proc, fd);
 mutex_unlock(&proc->files_lock);
 return ret;
}
'''
s=s[:s.index('static int task_get_unused_fd_flags(')]+helpers+wrappers+s[s.index('static inline void binder_lock('):]
compat = r"""/* Local Linux 3.4 compatibility for the Android 3.18 Binder donor. */
#ifndef _BINDER_COMPAT34_H
#define _BINDER_COMPAT34_H
static inline int binder34_map_vm_area(struct vm_struct *area, pgprot_t prot,
                                      struct page **pages)
{
 return map_vm_area(area, prot, &pages);
}
#define BINDER_MAX_NICE 19
#define BINDER_SIZE_MAX ((size_t)-1)
#define binder34_page_aligned(addr) IS_ALIGNED((unsigned long)(addr), PAGE_SIZE)
static inline long binder34_rlimit_to_nice(unsigned long rlim)
{
 return BINDER_MAX_NICE - (long)rlim + 1;
}
/* Matches Android common 3.4 exclusive freezer-aware waiting. */
#define binder34_wait_event_freezable_exclusive(wq, condition) \
 ({ int _ret; freezer_do_not_count(); \
    _ret = wait_event_interruptible_exclusive(wq, condition); \
    freezer_count(); _ret; })

#define binder_hlist_entry_safe(ptr, type, member) \
 ({ typeof(ptr) _p = (ptr); _p ? hlist_entry(_p, type, member) : NULL; })
#define binder_hlist_for_each_entry(pos, head, member) \
 for (pos = binder_hlist_entry_safe((head)->first, typeof(*(pos)), member); \
      pos; \
      pos = binder_hlist_entry_safe((pos)->member.next, typeof(*(pos)), member))
#define binder_hlist_for_each_entry_safe(pos, n, head, member) \
 for (pos = binder_hlist_entry_safe((head)->first, typeof(*(pos)), member); \
      pos && ({ n = (pos)->member.next; 1; }); \
      pos = binder_hlist_entry_safe(n, typeof(*(pos)), member))
#endif
"""
(target/rel/'binder_compat34.h').write_text(compat)
s=s.replace('#include "binder.h"', '#include "binder.h"\n#include "binder_compat34.h"')
s=s.replace('MAX_NICE','BINDER_MAX_NICE').replace('SIZE_MAX','BINDER_SIZE_MAX')
s=s.replace('hlist_for_each_entry_safe(', 'binder_hlist_for_each_entry_safe(').replace('hlist_for_each_entry(', 'binder_hlist_for_each_entry(')
s=s.replace('rlimit_to_nice(', 'binder34_rlimit_to_nice(').replace('PAGE_ALIGNED(', 'binder34_page_aligned(').replace('wait_event_freezable_exclusive(', 'binder34_wait_event_freezable_exclusive(')
s=s.replace('map_vm_area(&tmp_area, PAGE_KERNEL, page)', 'binder34_map_vm_area(&tmp_area, PAGE_KERNEL, page)')
old_context_claim='\t\tret = binder_ioctl_set_ctx_mgr(filp);\n\t\tif (ret)\n\t\t\tgoto err;\n\t\tret = security_binder_set_context_mgr(proc->tsk);\n\t\tif (ret < 0)\n\t\t\tgoto err;'
new_context_claim='\t\t/* Authorize before claiming the context or recording its owner UID. */\n\t\tret = security_binder_set_context_mgr(proc->tsk);\n\t\tif (ret < 0)\n\t\t\tgoto err;\n\t\tret = binder_ioctl_set_ctx_mgr(filp);\n\t\tif (ret)\n\t\t\tgoto err;'
assert s.count(old_context_claim)==1
s=s.replace(old_context_claim,new_context_claim)
p.write_text(s)
makefile=target/rel/'Makefile'
original=(base/'kernel-binder'/rel/'Makefile').read_text()
makefile.write_text(original+'\n# Keep Binder API mismatches visible while porting from newer kernels.\nCFLAGS_REMOVE_binder.o = -w\nCFLAGS_binder.o += -Werror\n')
print('Prepared modern Binder candidate')