"""Backport the pinned Android common 3.4 ARM mmap entropy control."""
import difflib
import json
import subprocess
from pathlib import Path

base = Path('/root/t110-build')
source = base / 'kernel-binder-modern'
donor = base / 'android-common-3.4'
project = Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
revision = '40bb591cb6abaf540bf9a988e3fac0ca86368865'
def upstream(name):
    return subprocess.check_output(['git', '-C', str(donor), 'show', revision + ':' + name], text=True)
def section(text, start, end):
    return text[text.index(start):text.index(end, text.index(start))]
files = ['arch/Kconfig', 'arch/arm/Kconfig', 'include/linux/mm.h', 'mm/mmap.c', 'kernel/sysctl.c', 'arch/arm/mm/mmap.c']
old = {name: (source / name).read_text() for name in files}
new = old.copy()
assert 'config HAVE_ARCH_MMAP_RND_BITS' not in old['arch/Kconfig']
new['arch/Kconfig'] += '\n' + section(upstream('arch/Kconfig'), 'config HAVE_ARCH_MMAP_RND_BITS\n', 'config HAVE_ARCH_MMAP_RND_COMPAT_BITS\n')
new['arch/arm/Kconfig'] = new['arch/arm/Kconfig'].replace('config ARM\n', 'config ARM\n\tselect HAVE_ARCH_MMAP_RND_BITS if MMU\n', 1)
new['arch/arm/Kconfig'] += '\n' + section(upstream('arch/arm/Kconfig'), 'config ARCH_MMAP_RND_BITS_MIN\n', '#\n# The "ARM system type"')
control = '#ifdef CONFIG_HAVE_ARCH_MMAP_RND_BITS\n'
for name, marker in [('include/linux/mm.h', '#include <asm/page.h>'), ('mm/mmap.c', 'static void unmap_region(')]:
    block = section(upstream(name), control, '#ifdef CONFIG_HAVE_ARCH_MMAP_RND_COMPAT_BITS\n')
    assert new[name].count(marker) >= 1
    new[name] = new[name].replace(marker, block + '\n' + marker, 1)
block = section(upstream('kernel/sysctl.c'), control, '#ifdef CONFIG_HAVE_ARCH_MMAP_RND_COMPAT_BITS\n')
marker = '#ifdef HAVE_ARCH_PICK_MMAP_LAYOUT\n\t{'
assert new['kernel/sysctl.c'].count(marker) == 1
new['kernel/sysctl.c'] = new['kernel/sysctl.c'].replace(marker, block + marker)
before = '(get_random_int() % (1 << 8)) << PAGE_SHIFT'
after = '(get_random_int() & ((1UL << mmap_rnd_bits) - 1)) << PAGE_SHIFT'
assert new['arch/arm/mm/mmap.c'].count(before) == 1
new['arch/arm/mm/mmap.c'] = new['arch/arm/mm/mmap.c'].replace(before, after)
patch = ''.join(''.join(difflib.unified_diff(old[name].splitlines(True), new[name].splitlines(True),
                                          fromfile='a/' + name, tofile='b/' + name)) for name in files)
path = project / 'patches/0011-arm-mmap-entropy-control.patch'
path.write_text(patch)
subprocess.run(['git', '-C', str(source), 'apply', '--check', str(path)], check=True)
subprocess.run(['git', '-C', str(source), 'apply', str(path)], check=True)
(project / 'evidence/mmap-entropy-backport.json').write_text(json.dumps({
    'donor': revision, 'files': files, 'status': 'APPLIED_NOT_COMPILED',
    'scope': 'Native 32-bit ARM entropy tunable, bounds 8..16 for 3GB split; no compat architecture support',
    'adaptation': 'Uses existing get_random_int(): ARM unsigned int and unsigned long are both 32-bit',
    'reason': 'Android 13 init aborts without writable vm.mmap_rnd_bits supporting 16 bits',
}, indent=2) + '\n')
print(path)
