"""Verify restored Android13 lessons against the actual Nougat artifacts."""
from pathlib import Path
import gzip, hashlib, json, re, runpy, shutil, subprocess, tempfile

BASE = Path('/root/t110-lineage14')
ART = BASE / 'artifacts/lineage14-first-build'
scope = runpy.run_path(str(Path(__file__).with_name('verify_init_service_imports.py')))
boot_files = scope['files']
rc = boot_files['/init.mrvl.rc']
for command in (b'iSerial ${ro.serialno}', b'    start adbd\n',
                b'symlink /dev/graphics/galcore /dev/galcore',
                b'chown system graphics /sys/devices/platform/pxa168-fb.0/vsync',
                b'chmod 0660 /sys/devices/platform/pxa168-fb.0/vsync'):
    assert command in rc, command
assert rc.index(b'    start adbd\n') < rc.index(b'on post-fs-data\n')
assert b'0666 system graphics' in boot_files['/ueventd.mrvl.rc']
assert b'/dev/graphics/galcore 0666 system graphics' in boot_files['/ueventd.mrvl.rc']

checks = []
with tempfile.TemporaryDirectory(prefix='t110-prior-graphics-') as tmp:
    def extract(name):
        target = Path(tmp) / name.replace('/', '_')
        subprocess.run(['debugfs', '-R', 'dump /'+name+' '+str(target),
                        str(ART/'system.raw.img')], capture_output=True, check=True)
        assert target.is_file() and target.stat().st_size
        return target
    egl = extract('vendor/lib/egl/libEGL_MRVL.so').read_bytes()
    # The old fix found four strings; GLES3 is an optional unsupported stock path.
    paths = re.findall(rb'/system/lib/egl/[A-Za-z0-9_.]+\.so', egl)
    assert len(paths) == 4, paths
    names = {Path(p.decode()).name for p in paths}
    assert names == {'libEGL_MRVL.so', 'libGLESv1_CM_MRVL.so', 'libGLESv2_MRVL.so', 'libGLESv3_MRVL.so'}
    for name in sorted(names - {'libGLESv3_MRVL.so'}):
        link = subprocess.check_output(['debugfs', '-R', 'stat /lib/egl/'+name,
                                        str(ART/'system.raw.img')], stderr=subprocess.DEVNULL, text=True)
        assert 'Type: symlink' in link and '"../../vendor/lib/egl/'+name+'"' in link, link
        target = extract('vendor/lib/egl/'+name)
        checks.append({'absolute_driver_path': '/system/lib/egl/'+name,
                       'canonical_target': '/system/vendor/lib/egl/'+name,
                       'sha256': hashlib.sha256(target.read_bytes()).hexdigest()})
    gal = extract('vendor/lib/libGAL.so')
    compiler = extract('vendor/lib/libGLESv2SC.so')
    assert hashlib.sha256(compiler.read_bytes()).hexdigest() == 'ad6e492a98834b34079eb32024fc70e77b8df543b5118e762a4fe8d96c64706f'
    dynamic = subprocess.check_output(['readelf', '-d', str(gal)], text=True)
    assert '(INIT)' not in dynamic and '(INIT_ARRAY)' not in dynamic
    symbols = subprocess.check_output(['readelf', '-Ws', str(gal)], text=True)
    assert ' gcoOS_ModuleConstructor' in symbols
    for name in ('lib/libEGL.so', 'lib/libui.so'):
        data = extract(name).read_bytes()
        assert b'gcoOS_ModuleConstructor\0' in data
        assert b'process initialization failed' in data
    props = extract('build.prop').read_text()
    assert 'ro.zygote.disable_gl_preload=true' in props
    assert 'persist.sys.sdcardfs=force_off' in props
    assert 'ro.sf.hwrotation=270' in props and 'ro.sf.lcd_density=200' in props
    assert 'ro.opengles.version=131072' in props  # Advertise GLES2, never fake GLES3.

record = {'status': 'PASS', 'scope': 'Actual boot and system images; not hardware graphics certification',
          'boot_sha256': hashlib.sha256((ART/'boot.img').read_bytes()).hexdigest(),
          'restored': ['absolute EGL driver paths', 'stock dynamic shader compiler',
                       'actual Nougat GPU node permissions and alias', 'EGL and gralloc process initialization',
                       'vsync permissions', 'early authenticated ADB', 'original USB serial'],
          'driver_paths': checks}
(ART/'prior-graphics-verification.json').write_text(json.dumps(record, indent=2)+'\n')
print('PASS: actual-image checks for prior EGL, gralloc, display and USB fixes.')
