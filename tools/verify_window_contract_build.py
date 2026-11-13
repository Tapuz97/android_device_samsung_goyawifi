"""Inspect compiled candidate components; this is not hardware qualification."""
from pathlib import Path
import hashlib, json, subprocess, tempfile, shutil

base = Path('/root/t110-lineage14')
tree = base/'android'
out = tree/'out/target/product/goyawifi'
objdump = tree/'prebuilts/gcc/linux-x86/arm/arm-linux-androideabi-4.9/bin/arm-linux-androideabi-objdump'
objects = list((out/'obj/STATIC_LIBRARIES/libhwui_static_intermediates').rglob('EglManager.o'))
assert len(objects) == 1, objects
dump = subprocess.check_output([str(objdump), '-drC', str(objects[0])], text=True)
start = dump.index('<android::uirenderer::renderthread::EglManager::swapBuffers(')
section = dump[start:]
# Relocation-aware output ties glReadPixels to the actual swap function.
import re
next_function = re.search(r'\n[0-9a-f]+ <', section[1:])
if next_function:
    section = section[:next_function.start()+1]
assert 'glReadPixels' in section and 'eglSwapBuffersWithDamageKHR' in section
assert section.index('glReadPixels') < section.index('eglSwapBuffersWithDamageKHR')

surface = list((out/'obj/SHARED_LIBRARIES/libgui_intermediates').rglob('Surface.o'))
assert len(surface) == 1, surface
surface_dump = subprocess.check_output([str(objdump), '-drC', str(surface[0])], text=True)
start = surface_dump.index('<android::Surface::hook_dequeueBuffer_DEPRECATED(')
queue = surface_dump[start:]
next_function = re.search(r'\n[0-9a-f]+ <', queue[1:])
if next_function:
    queue = queue[:next_function.start()+1]
assert 'systemTime' in queue and 'pthread_cond_timedwait_relative_np' in queue

oat = out/'system/framework/arm/boot-framework.oat'
assert b'ro.t110.legacy_gpu' in oat.read_bytes(), 'New Java guard absent from compiled framework'
assert 'ro.t110.legacy_gpu=true' in (out/'system/build.prop').read_text()
files = ['system/lib/libhwui.so', 'system/lib/libgui.so',
         'system/framework/arm/boot-framework.oat',
         'system/framework/arm/boot-framework.art', 'system/build.prop', 'system.img']
checks = []
for name in files:
    file = out/name
    with file.open('rb') as stream:
        h = hashlib.sha256()
        for chunk in iter(lambda: stream.read(4*1024*1024), b''):
            h.update(chunk)
    checks.append(dict(path=name, bytes=file.stat().st_size, sha256=h.hexdigest()))
with tempfile.TemporaryDirectory(prefix='t110-window-image-', dir=str(base/'records')) as tmp:
    tmp = Path(tmp)
    raw = tmp/'system.raw.img'
    image = out/'system.img'
    with image.open('rb') as stream:
        sparse = stream.read(4) == b'\x3a\xff\x26\xed'
    if sparse:
        subprocess.run([str(tree/'out/host/linux-x86/bin/simg2img'), str(image), str(raw)], check=True)
    else:
        shutil.copyfile(image, raw)
    assert raw.stat().st_size <= 1594884096
    fsck = subprocess.run(['e2fsck', '-fn', str(raw)], capture_output=True, text=True)
    filesystem_log = fsck.stdout + fsck.stderr
    normalized_padding = False
    if fsck.returncode:
        # Same narrowly identified make_ext4fs defect handled by our existing
        # packager. Normalize only this disposable generated copy, not input.
        questions = [line for line in filesystem_log.splitlines() if 'Fix?' in line]
        assert fsck.returncode == 4 and questions == [
            'Padding at end of inode bitmap is not set. Fix? no'], filesystem_log
        repair = subprocess.run(['e2fsck', '-fy', str(raw)], capture_output=True, text=True)
        assert repair.returncode in (0, 1), repair.stdout + repair.stderr
        filesystem_log += '\nTemporary-copy padding normalization:\n' + repair.stdout + repair.stderr
        normalized_padding = True
        fsck = subprocess.run(['e2fsck', '-fn', str(raw)], capture_output=True, text=True)
        filesystem_log += '\nFinal read-only check:\n' + fsck.stdout + fsck.stderr
    assert fsck.returncode == 0, fsck.stdout + fsck.stderr
    for item in checks:
        if not item['path'].startswith('system/'):
            continue
        extracted = tmp/'extracted'
        extracted.unlink(missing_ok=True)
        command = 'dump /' + item['path'][len('system/'):] + ' ' + str(extracted)
        subprocess.run(['debugfs', '-R', command, str(raw)], capture_output=True, check=True)
        assert hashlib.sha256(extracted.read_bytes()).hexdigest() == item['sha256'], item['path']
        item['actual_system_image_match'] = True
record = dict(status='OFFLINE_COMPONENT_CHECKS_PASSED', installed=False,
              hardware_graphics_pass=False, files=checks,
              temporary_copy_padding_normalized=normalized_padding,
              checks=['compiled HWUI resolve before swap',
                      'compiled legacy queue deadline and condition wait',
                      'T110 Java warmup guard in compiled framework',
                      'T110 product opt-in in built system',
                      'actual system image component hashes and read-only filesystem check'])
dest = base/'records/window-contract';dest.mkdir(exist_ok=True)
(dest/'filesystem-check.txt').write_text(filesystem_log)
(dest/'hwui-swap.disassembly.txt').write_text(section)
(dest/'legacy-dequeue.disassembly.txt').write_text(queue)
(dest/'verification.json').write_text(json.dumps(record, indent=2)+'\n')
print(json.dumps(record, indent=2))
