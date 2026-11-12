"""Reproduce and fix the A9 Thumb-2 single-register STM fault with actual Bionic asm."""
from pathlib import Path
import difflib
import os
import shutil
import subprocess
import tempfile

base = Path('/root/t110-build')
project = Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
bionic = base / 'lineage20/bionic'
source = bionic / 'libc/arch-arm/cortex-a9/bionic'
clang = base / 'lineage20/prebuilts/clang/host/linux-x86/clang-r450784d/bin/clang'
patch = []

def trial(patched):
    label = 'fixed' if patched else 'before-fix'
    root = Path(tempfile.mkdtemp(prefix='a9-strings-', dir=base))
    root.chmod(0o755)
    (root / 'dev').mkdir()
    asm = root / 'asm'
    shutil.copytree(source, asm)
    if patched:
        for name in ['string_copy.S', 'strcat.S']:
            p = asm / name
            before = p.read_text()
            old = '    stmia   r0, {r2}'
            assert before.count(old) == 1
            after = before.replace(old, '    str     r2, [r0]  // One-register Thumb-2 STM is unpredictable.')
            p.write_text(after)
            rel = 'libc/arch-arm/cortex-a9/bionic/' + name
            patch.extend(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile='a/'+rel, tofile='b/'+rel))
    objects = []
    for name in ['strcpy', 'stpcpy', 'strcat']:
        obj = root / (name + '.o')
        subprocess.run([str(clang), '--target=arm-linux-gnueabi', '--sysroot=/usr/arm-linux-gnueabi', '-march=armv7-a', '-mthumb', '-I'+str(bionic/'libc'), '-c', str(asm/(name+'.S')), '-o', str(obj)], check=True)
        objects.append(str(obj))
    subprocess.run(['arm-linux-gnueabi-gcc', '-static', '-O2', '-march=armv7-a', '-mthumb', '-Wall', '-Wextra', '-Werror', str(project/'work/core-boot/a9_string_test.c'), *objects, '-o', str(root/'init')], check=True)
    archive = subprocess.run(['bash', '-c', 'find dev init -print0 | cpio --quiet -o -0 -H newc | gzip -n'], cwd=root, capture_output=True, check=True).stdout
    (root/'ramdisk.gz').write_bytes(archive)
    log = project / ('evidence/qemu-a9-strings-'+label+'.log')
    with log.open('wb') as out:
        result = subprocess.run(['timeout','30','qemu-system-arm','-M','vexpress-a9','-cpu','cortex-a9','-smp','2','-m','256M','-display','none','-monitor','none','-serial','stdio','-net','none','-no-reboot','-kernel',str(base/'out-qemu-random/arch/arm/boot/zImage'),'-initrd',str(root/'ramdisk.gz'),'-append','console=ttyAMA0 rdinit=/init panic=1'], stdout=out, stderr=subprocess.STDOUT, env={**os.environ, 'QEMU_AUDIO_DRV':'none'})
    content = log.read_text(errors='replace')
    passed = 'T110_A9_STRING_REGRESSION_PASS' in content
    if patched:
        assert passed and result.returncode == 0, content[-3000:]
    else:
        assert not passed and ('Illegal instruction' in content or 'exitcode=0x00000004' in content), content[-3000:]
    print(label, 'validated', flush=True)

trial(False)
trial(True)
(project/'patches/0028-bionic-a9-single-register-thumb-store.patch').write_text(''.join(patch))
