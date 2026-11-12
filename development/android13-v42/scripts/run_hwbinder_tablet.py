"""Run a bounded test on the v5 diagnostic and restore verified stock BOOT."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

project = Path(__file__).resolve().parents[1]
previous = project / 'hardware-tests/20261105-modern-init-v5'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--staged-system', action='store_true')
parser.add_argument('--headless', action='store_true')
parser.add_argument('--gpu', action='store_true', help='Try the matched galcore module after the staged image check')
parser.add_argument('--display-only', action='store_true', help='Show a pattern in the staged-system diagnostic without repeating the image mount')
args = parser.parse_args()
if args.display_only and (not args.staged_system or args.headless or args.gpu):
    parser.error('--display-only requires --staged-system and a visual run')
trial = project / 'hardware-tests' / (time.strftime('%Y%m%d-%H%M%S') + ('-system' if args.staged_system else '-hwbinder'))
trial.mkdir()
adb = Path(r'C:\Users\Gal\AppData\Local\Android\Sdk\platform-tools\adb.exe')
serial = 'T110_ADB_SERIAL'
stock_md5 = '7847f1b7e68e49e9ca590e052f0f76c4'
diagnostic = project / 'artifacts/android13-ramdisk-v5/KERNEL.img'
stock = project / 'backups/20261104T201457Z/KERNEL.img'
bundle = project / 'artifacts/android13-hwbinder/t110-hwbinder.tar'

def digest(path, name):
    return hashlib.new(name, path.read_bytes()).hexdigest()

assert digest(diagnostic, 'sha256') == '6ced895a4cb8a2357035ae877b1f95992ac5becb8b2cc6e89faf48c352acda39'
assert digest(stock, 'md5') == stock_md5
bundle_sha = digest(bundle, 'sha256')
assert bundle_sha == '81b3f332b4235fb851a78eece1620084954e32592f43169e99c90329704b8151'
graphics = project / 'artifacts/framebuffer-probe'
if args.staged_system:
    stage = json.loads((project / 'artifacts/system-stage-20261105/provenance.json').read_text(encoding='utf-8-sig'))
    fit = json.loads((project / stage['fit_report']).read_text())
    assert fit['status'] == 'FIT_AND_EXT4_VERIFIED'
    assert stage['bytes'] == fit['expanded_bytes'] and stage['sparse_sha256'] == fit['sha256']
    assert len(stage['raw_sha256']) == 64 and all(c in '0123456789abcdef' for c in stage['raw_sha256'])
    graphics_pins = json.loads((graphics/'provenance.json').read_text(encoding='utf-8-sig'))
    for name, sha256 in graphics_pins['artifacts'].items():
        assert digest(graphics/name, 'sha256') == sha256

def run(*args, timeout=30, check=True):
    result = subprocess.run([str(adb), '-s', serial, *map(str, args)],
                            capture_output=True, text=True, errors='replace', timeout=timeout)
    output = result.stdout + result.stderr
    with (trial / 'adb.log').open('a', encoding='utf-8') as log:
        log.write(f'{args!r} => {result.returncode}\n{output}\n')
    if check and result.returncode:
        raise RuntimeError(output)
    return output

def wait_for(command, marker, seconds):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            output = run('shell', command, timeout=6, check=False)
            if marker in output:
                return output
        except subprocess.TimeoutExpired:
            pass
        time.sleep(2)
    raise TimeoutError(f'ADB did not report {marker}')

def recovery():
    return wait_for('[ "$(id -u)" = 0 ] && [ -x /sbin/reboot ] && [ -x /sbin/recovery ] && echo T110_TWRP_READY',
                    'T110_TWRP_READY', 150)

def push_script(name, contents):
    path = trial / (name + '.sh')
    path.write_bytes(contents.encode())
    run('push', path, '/tmp/'+path.name)
    return '/tmp/'+path.name

def stage_test():
    for name in ('t110_framebuffer_probe', 't110_galcore_query', 't110_return_to_recovery'):
        run('push', graphics/name, '/tmp/'+name)
    run('shell', 'chmod 0755 /tmp/t110_framebuffer_probe /tmp/t110_galcore_query /tmp/t110_return_to_recovery')
    run('shell', 'touch /dev/t110-keepalive')
    stage_pass = args.display_only
    if not args.display_only:
        script = push_script('probe-staged-system', (project/'scripts/probe_staged_system_ro.sh').read_text())
        print('Running staged image hash, mount and linker checks.', flush=True)
        output = run('shell', f'sh {script} {stage["raw_sha256"]} {stage["bytes"]}', timeout=200, check=False)
        (trial/'system-probe.txt').write_text(output)
        (trial/'kernel-after-system.txt').write_text(run('shell', 'dmesg', check=False))
        print(output, flush=True)
        stage_pass = 'T110_SYSTEM_IMAGE_LINKER_AND_TOYBOX_PASS' in output
    geometry = run('shell', '/tmp/t110_framebuffer_probe', check=False)
    (trial/'framebuffer-geometry.txt').write_text(geometry)
    print(geometry, flush=True)
    if args.headless:
        if args.gpu:
            test_gpu()
        return stage_pass
    print('GRAPHICS_READY '+str(trial), flush=True)
    deadline = time.monotonic() + 120
    while not (trial/'run-pattern').exists() and time.monotonic() < deadline:
        time.sleep(1)
    if not (trial/'run-pattern').exists():
        return stage_pass and not args.display_only
    pattern_output = run('shell', '/tmp/t110_framebuffer_probe --pattern', timeout=20, check=False)
    (trial/'framebuffer-pattern.txt').write_text(pattern_output)
    print(pattern_output, flush=True)
    if args.display_only:
        # Leave time for the observer to report the result before restoring BOOT.
        time.sleep(15)
    else:
        test_gpu()
    return stage_pass and 'Presenting red, green, blue and white bars' in pattern_output

def test_gpu():
    module = project/'artifacts/kernel-native-init-ffs/modules/galcore.ko'
    metadata = json.loads((module.parent/'provenance.json').read_text())
    assert digest(module, 'sha256') == metadata['sha256']
    assert metadata['paired_kernel_sha256'] == graphics_pins['matching_kernel_sha256']
    run('push', module, '/tmp/t110-galcore.ko')
    run('push', graphics/'t110_load_galcore', '/tmp/t110_load_galcore')
    run('shell', 'chmod 0755 /tmp/t110_load_galcore')
    output = run('shell', f'[ "$(sha256sum /tmp/t110-galcore.ko | cut -d\' \' -f1)" = {metadata["sha256"]} ] '
                 '&& /tmp/t110_load_galcore && /tmp/t110_galcore_query', timeout=35, check=False)
    (trial/'galcore-query.txt').write_text(output)
    print(output, flush=True)
    kernel = run('shell', 'dmesg', check=False)
    (trial/'kernel-after-graphics.txt').write_text(kernel)

wait_for('[ "$(getprop sys.boot_completed)" = 1 ] && [ "$(getprop ro.product.device)" = goyawifi ] && echo T110_STOCK_READY',
         'T110_STOCK_READY', 15)
if args.staged_system:
    # Stock toolbox has ls rather than stat. The diagnostic performs the hash.
    staged = run('shell', 'ls -l /data/local/tmp/t110-stage-system.raw')
    assert str(stage['bytes']) in staged, staged
run('reboot', 'recovery')
recovery()
flash = (previous / 'flash-command.txt').read_text()
assert flash.count('032b0fc951db00f1125fe90e496ff3f8') == 1
flash = flash.replace('032b0fc951db00f1125fe90e496ff3f8', stock_md5)
run('push', diagnostic, '/tmp/t110-android13-v5.img')
run('push', stock, '/tmp/t110-stock-boot.img')
flash_path = push_script('flash', flash)
try:
    flash_output = run('shell', '/sbin/sh '+flash_path, timeout=60)
    assert 'FLASH_AND_RECOVERY_VERIFIED' in flash_output, flash_output
    print('Verified diagnostic BOOT and separate recovery readbacks.', flush=True)
    run('shell', '/sbin/reboot recovery_done', check=False)
    wait_for('[ -f /t110-native-diagnostic ] && [ "$(id -u)" = 0 ] && echo T110_DIAGNOSTIC_READY',
             'T110_DIAGNOSTIC_READY', 100)
    if args.staged_system:
        assert stage_test(), 'Staged system probe did not complete'
    else:
        run('push', bundle, '/tmp/t110-hwbinder.tar')
        output = run('shell', f'set -e; [ "$(sha256sum /tmp/t110-hwbinder.tar | cut -d\' \' -f1)" = {bundle_sha} ]; '
                     'tar -xf /tmp/t110-hwbinder.tar -C /tmp; '
                     'LD_LIBRARY_PATH=/tmp/t110-hwbinder/lib /tmp/t110-hwbinder/bin/linker /tmp/t110-hwbinder/bin/t110_hwbinder_probe; '
                     'echo T110_HWBINDER_EXIT_0', timeout=35, check=False)
        (trial / 'probe.txt').write_text(output)
        print(output, flush=True)
        assert 'T110_HWBINDER_EXIT_0' in output and 'PASS Android 13 HIDL Binder cross-process 4099-byte SG roundtrip' in output
finally:
    # If v5 ran, its watchdog also returns to recovery if this request is lost.
    try:
        run('shell', '[ ! -f /t110-native-diagnostic ] || { if [ -x /tmp/t110_return_to_recovery ]; then /tmp/t110_return_to_recovery || setprop sys.powerctl reboot; else setprop sys.powerctl reboot,recovery; fi; }', timeout=8, check=False)
    except subprocess.TimeoutExpired:
        pass
    recovery()
    state = run('shell', 'md5sum /dev/block/mmcblk0p10')
    if stock_md5 not in state:
        run('push', stock, '/tmp/t110-stock-boot.img')
        rollback_path = push_script('rollback', (previous / 'rollback-command.txt').read_text())
        restored = run('shell', '/sbin/sh '+rollback_path, timeout=60)
        assert 'STOCK_BOOT_AND_RECOVERY_VERIFIED' in restored, restored
    run('shell', '/sbin/reboot recovery_done', check=False)
    returned = wait_for('[ "$(getprop sys.boot_completed)" = 1 ] && [ "$(getprop ro.build.version.release)" = 4.2.2 ] && echo T110_STOCK_RETURN_VERIFIED',
                        'T110_STOCK_RETURN_VERIFIED', 180)
    (trial / 'stock-return.txt').write_text(returned)
    print('Stock boot verified. Evidence: '+str(trial), flush=True)
