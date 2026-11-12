"""Backport seeded getrandom from upstream onto the pinned Android 3.4 RNG."""
from pathlib import Path
import shutil
import difflib
import subprocess

base = Path('/root/t110-build')
project = Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
source = base / 'kernel-random'
baseline = base / 'kernel-platform'
donor = base / 'android-common-3.4'
assert subprocess.check_output(['git', '-C', str(donor), 'rev-parse', 'HEAD'], text=True).strip() == '40bb591cb6abaf540bf9a988e3fac0ca86368865'
assert not source.exists()
shutil.copytree(baseline, source, ignore=shutil.ignore_patterns('.git', '*.rej'))
files = ['drivers/char/random.c', 'include/linux/random.h', 'include/trace/events/random.h']
for name in files:
    shutil.copyfile(donor / name, source / name)

def edit(name, before, after):
    p = source / name
    text = p.read_text()
    assert text.count(before) == 1, (name, before, text.count(before))
    p.write_text(text.replace(before, after))
    if name not in files:
        files.append(name)

rng = 'drivers/char/random.c'
edit(rng, '#include <linux/kmemcheck.h>', '#include <linux/kmemcheck.h>\n#include <linux/syscalls.h>')
edit(rng, 'static DECLARE_WAIT_QUEUE_HEAD(random_write_wait);', 'static DECLARE_WAIT_QUEUE_HEAD(random_write_wait);\nstatic DECLARE_WAIT_QUEUE_HEAD(urandom_init_wait);')
edit(rng, '\t\tif (r->entropy_total > 128)\n\t\t\tr->initialized = 1;', '\t\tif (r->entropy_total > 128) {\n\t\t\tr->initialized = 1;\n\t\t\tif (r == &nonblocking_pool) {\n\t\t\t\twake_up_interruptible(&urandom_init_wait);\n\t\t\t\tpr_notice("random: nonblocking pool initialized\\n");\n\t\t\t}\n\t\t}')
edit(rng, '\t__u8 tmp[EXTRACT_SIZE];\n\n\ttrace_extract_entropy_user', '\t__u8 tmp[EXTRACT_SIZE];\n\tint large_request = (nbytes > 256);\n\n\ttrace_extract_entropy_user')
edit(rng, '\t\tif (need_resched()) {', '\t\tif (large_request && need_resched()) {')
edit(rng, '\nrandom_read(struct file *file, char __user *buf, size_t nbytes, loff_t *ppos)', '\n_random_read(int nonblock, char __user *buf, size_t nbytes)')
edit(rng, 'if (file->f_flags & O_NONBLOCK)', 'if (nonblock)')
edit(rng, 'static ssize_t\nurandom_read(', 'static ssize_t\nrandom_read(struct file *file, char __user *buf, size_t nbytes, loff_t *ppos)\n{\n\treturn _random_read(file->f_flags & O_NONBLOCK, buf, nbytes);\n}\n\nstatic ssize_t\nurandom_read(')
patch = (project / 'sources/getrandom-upstream.patch').read_text()
block = patch[patch.index('+SYSCALL_DEFINE3(getrandom'):]
block = block[:block.index('\n /***************************************************************')]
block = '\n'.join(line[1:] for line in block.splitlines() if line.startswith('+'))
edit(rng, '/***************************************************************\n * Random UUID interface', block + '\n/***************************************************************\n * Random UUID interface')
edit('include/linux/random.h', 'struct rand_pool_info {', '#define GRND_NONBLOCK 0x0001\n#define GRND_RANDOM 0x0002\n\nstruct rand_pool_info {')
edit('include/linux/syscalls.h', 'asmlinkage long sys_seccomp(', 'asmlinkage long sys_getrandom(char __user *buf, size_t count, unsigned int flags);\n\nasmlinkage long sys_seccomp(')
edit('arch/arm/kernel/calls.S', '\t\tCALL(sys_seccomp)\n', '\t\tCALL(sys_seccomp)\n\t\tCALL(sys_getrandom)\n')
edit('arch/arm/include/asm/unistd.h', '#define __NR_seccomp', '#define __NR_getrandom (__NR_SYSCALL_BASE+384)\n#define __NR_seccomp')
edit('kernel/irq/handle.c', '\tif (random & IRQF_SAMPLE_RANDOM)\n\t\tadd_interrupt_randomness(irq);', '\tadd_interrupt_randomness(irq, random);')
p = source / 'kernel/irq/manage.c'
s = p.read_text()
start = s.index('\t/*\n\t * Some drivers like serial.c use request_irq() heavily,')
end = s.index('\n\t/*\n\t * Check whether the interrupt nests', start)
edit('kernel/irq/manage.c', s[start:end], '')
# Keep the existing Marvell-only card-presence workaround out of vexpress builds.
edit('drivers/mmc/core/core.c', '\tif (host->index == SEC_SDCARD_INDEX) {', '#ifndef CONFIG_ARCH_VEXPRESS\n\tif (host->index == SEC_SDCARD_INDEX) {')
edit('drivers/mmc/core/core.c', '\tif (host->ops->get_cd && host->ops->get_cd(host) == 0) {', '#endif\n\tif (host->ops->get_cd && host->ops->get_cd(host) == 0) {')
diff = []
for name in files:
    old = (baseline / name).read_text() if (baseline / name).exists() else ''
    diff.extend(difflib.unified_diff(old.splitlines(True), (source / name).read_text().splitlines(True), fromfile='a/' + name, tofile='b/' + name))
(project / 'patches/0020-kernel-seeded-getrandom.patch').write_text(''.join(diff))
print('Prepared pinned RNG, IRQ integration, ARM syscall 384 and patch 0020')
