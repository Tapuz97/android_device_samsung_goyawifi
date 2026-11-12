"""Record observed stable Android startup and the user's remaining display issue."""
from pathlib import Path
import json
import os
import subprocess

p = Path(__file__).resolve().parents[1]
trial = p/'hardware-tests/20261107-134233-core'
base = [str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
r = subprocess.run(base+['shell','id; test -x /sbin/recovery && echo TWRP; cat /sys/block/mmcblk0/device/cid; md5sum /dev/block/mmcblk0p10 /dev/block/mmcblk0p9'],capture_output=True,timeout=15,check=True)
text = r.stdout.decode(errors='replace')
assert 'TWRP' in text and '1101003030384745T110_ADB_SERIAL' in text
assert '942182cefec3cb7666096499220789d0' in text and 'cd9793e1ee8f284c9056b225885b5b1a' in text
(trial/'recovery-after-stable-boot.txt').write_text(text)
state = (trial/'final-before-rebuild-state.txt').read_text()
assert 'state=RUNNING_UNLOCKED' in state
assert (trial/'final-before-rebuild-crash.txt').stat().st_size==0
result = dict(status='ANDROID_STARTUP_STABLE_DISPLAY_AND_TOUCH_NOT_ACCEPTED',
    hardware_tested=True, hardware_validated=False, full_boot_passed=False,
    boot_completed=True, user_unlocked=True, user_unlock_uptime_ms=208218,
    system_server_pid=356, system_server_restart_observed=False,
    stability_seconds_after_boot_completed=361.114,
    final_observed_uptime_seconds=float(state.split()[0]),
    emulated_storage_mounted=True, kernel_ext4_acl_enabled=True,
    initial_service_anrs=['SystemUI','MediaProvider'],
    user_saw_lineage_welcome=True, user_reported_touch_response=False,
    user_photo_confirms_rotated_cropped_layout=True,
    findings=['Stock T110 requires 270 degree hardware panel orientation',
              'Current SurfaceFlinger reports unrotated 1024x600 instead of natural portrait',
              'HWC2OnFbAdapter power hook is a no-op; panel image remains visible during Android sleep',
              'Input viewport disables while asleep; injected wake re-enables DIRECT touch mode'],
    touch_events_validated=False, tablet_state='TWRP',
    controlled_return_to_recovery=True, stock_rollback_performed=False,
    system_md5='40b250a4afe35086bd6ab7610300ce24',
    boot_md5='942182cefec3cb7666096499220789d0', recovery_md5='cd9793e1ee8f284c9056b225885b5b1a')
(trial/'result.json').write_text(json.dumps(result,indent=2)+'\n')
pair_path = p/'artifacts/android13-full-v27/system-pair.json'
pair = json.loads(pair_path.read_text())
for k in ['status','hardware_tested','hardware_validated','full_boot_passed','boot_completed']:
    pair[k] = result[k]
pair['hardware_trial'] = str(trial.relative_to(p))
pair_path.write_text(json.dumps(pair,indent=2)+'\n')
entry = '''## v27 STARTUP STABLE; v19 DISPLAY CORRECTION BUILD RUNNING - 2026-11-07 14:02

v27 BOOT + v18 system booted once in hardware-tests/20261107-134233-core. Runner19507 completed0 after361 seconds beyond boot_completed, same system_server356. User0 unlocked208218ms, emulated storage mounted after initial MediaProvider ANR/restart, SystemUI also had initial ANRs. No fatal crash buffer; system remained up through roughly18 minutes. User confirmed actual Lineage welcome screen and supplied photo, but reported no touch and cropped/rotated layout. Not a usable-ROM pass. Guarded return helper intentionally brought tablet to verified TWRP; BOOT942182cefec3cb7666096499220789d0 and recoverycd9793e1ee8f284c9056b225885b5b1a confirmed. No stock rollback. See result.json and final-before-rebuild-*.

Current source corrections, evidence/offline-v29: actual STOCK stock/T110XXUANI7/system/build.prop says ro.sf.hwrotation=270 (old attempted device tree says90 and is wrong for this stock). Product now uses ro.surface_flinger.primary_display_orientation=ORIENTATION_270 and natural600x1024. SurfaceFlinger swaps exposed modes and removes physical panel orientation from InputFlinger; do NOT add a second touch rotation. Welcome view hierarchy confirms landscape layout placed content in the right column and below screen, not corrupt framebuffer size. EGL window bridge also flips final clip-space Y AFTER display rotation, fixing noncommutation at90/270. Combined patch0053 supersedes0038. Combined patch0054 supersedes0036 and wires HWC2 power to framebuffer enableScreen -> FBIOBLANK with checked errors. Previously adapter pretended power transition succeeded, leaving visible panel while Android slept and disabled touch. Injected wake changed mapperDISABLED toDIRECT. No actual corner event evidence: bounded getevent capture ended before later user reply; don't infer hardware failure from its zero bytes.

prepare_offline_v29.py completed. test_v29_offline.py PASS uses actual changed production bodies, real Android mat4, both aspect ratios/all corners/all quarter-turns, powerOFF/ON/errors/unsupported/missing-hook behavior, ASan+UBSan nonrecovering. Host compile needed normal Android utils/cutils/log headers; no production change for that. No new Android boot during fixes.

Only active system build73521, log/root/t110-build/logs/system-image-20261107T120143Z.log on T110Build. Persistent T110Build shell38923. Ubuntu kernel tree unchanged. Do not edit active build inputs. After success archive as lineage20-rom-v19, verify actual property/graphics binaries/retained fixes/ext4/hashes and policy/classpath against existing v27 BOOT. Prefer reuse identical BOOT if pairing checks pass. Stage v19 using compressed checked chunks, then full boot immediately with --reuse-boot and expected installed BOOT942182cefec3cb7666096499220789d0. Standing user instruction: NEVER stop at readiness or ask to flash. Carry through build->verification->flash->one full boot. User nearby for necessary physical actions only.

'''
status = p/'CURRENT-STATUS.md'
status.write_text(entry+status.read_text(encoding='utf-8'),encoding='utf-8')
print(result['status'])
