"""Record the observed v25 boot result; never equate boot_completed with usable UI."""
import json
from pathlib import Path

project = Path(__file__).resolve().parents[1]
trial = project / 'hardware-tests/20261107-021556-core'
recovery = (trial / 'recovery-state.txt').read_text(encoding='utf-8-sig')
assert '3f507c549441bb54e027cbb4ed20837c' in recovery
assert 'cd9793e1ee8f284c9056b225885b5b1a' in recovery
state = (trial / 'final-user-state.txt').read_text(encoding='utf-8-sig')
assert 'state=RUNNING_UNLOCKED' in state
assert state.splitlines()[1:4] == ['1', 'stopped', '355']
crashes = (trial / 'live-crash-late.txt').read_text(encoding='utf-8-sig')
assert 'C2AllocatorIon::setUsageMapper' in crashes
assert 'Failed to get EGL_DEFAULT_DISPLAY!' in crashes
capture = json.loads((trial / 'recovery-capture-result.json').read_text())
assert capture['tablet_state'] == 'TWRP'
result = {
    'status': 'ANDROID_UNLOCKED_UI_FAILED_RECOVERY_VERIFIED',
    'hardware_tested': True, 'hardware_validated': False,
    'boot_completed': True, 'full_boot_passed': False,
    'user_0_state': 'RUNNING_UNLOCKED',
    'user_unlock_uptime_ms': 212382,
    'last_live_uptime_seconds': 319.47,
    'system_server_pid': 355,
    'system_server_restart_observed': False,
    'boot_animation_final_state': 'stopped',
    'tablet_state': 'TWRP',
    'normal_rom_boots_this_pass': 1, 'boot_partition_writes_this_pass': 1,
    'stock_rollback_performed': False,
    'installed_boot_md5': '3f507c549441bb54e027cbb4ed20837c',
    'recovery_md5': 'cd9793e1ee8f284c9056b225885b5b1a',
    'staged_system_md5': '4c4c6f665218d1f471303e052d295517',
    'visual_confirmation': 'User selected Black screen or TWRP, then reported TWRP after the controlled recovery return; usable UI not confirmed',
    'screenshot': 'Timed out after12seconds; no valid image captured',
    'blockers': [
        'Repeated native SystemUI crash in C2AllocatorIon::setUsageMapper via NDK MediaCodec',
        'Launcher RenderThread abort: Failed to get EGL_DEFAULT_DISPLAY! err=EGL_SUCCESS',
    ],
    'other_observations': ['sdcard process SIGABRT after user unlock'],
    'recovery_capture': capture,
}
(trial / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
pair_file = project / 'artifacts/android13-full-v25/system-pair.json'
pair = json.loads(pair_file.read_text())
pair.update({key: result[key] for key in (
    'status', 'hardware_tested', 'hardware_validated', 'boot_completed', 'full_boot_passed')})
pair.update(hardware_boots_this_pass=1, flashes_this_pass=1, tablet_access_this_pass=True,
            user_0_state='RUNNING_UNLOCKED', hardware_result='../../hardware-tests/20261107-021556-core/result.json')
pair['limits'] = [
    'User unlocking now succeeds, but repeated native SystemUI and launcher crashes prevent usable-UI validation',
    'No screen/touch confirmation; screenshot attempt timed out',
    'GPS/audio/other unported hardware and media codec functionality remain unresolved',
]
pair_file.write_text(json.dumps(pair, indent=2) + '\n')
note = '''## v25/v16 FLASHED - USER UNLOCKED, UI FAILED - 2026-11-07

User requested "ok flash the rom". Exactly one v25 BOOT flash/readback and one full normal ROM boot were performed, trial hardware-tests/20261107-021556-core. System v16 was transferred with compressed chunks, full remote MD5 checked and staged atomically. Raw transfer first hit420s timeout; recovery discarded that partial file. Compressed final chunk needed one retry; verified assembled MD5 matches4c4c6f665218d1f471303e052d295517.

The new kernel cleared the user-unlock blocker: user0 reached RUNNING_UNLOCKED at212382ms. sys.boot_completed=1 by218.77s, main system_server remained PID355 through319.47s, bootanim stopped. Previous missing-calling_sid/KeyStore.state assertion and AppOps null-list exception were not observed in captured current-boot logs. This is NOT a usable UI pass: SystemUI repeatedly crashes natively in C2AllocatorIon::setUsageMapper (NDK MediaCodec path); launcher RenderThread aborts with Failed to get EGL_DEFAULT_DISPLAY! err=EGL_SUCCESS. sdcard also SIGABRTs after unlock. Screenshot attempt timed out; no valid PNG. User selected Black screen or TWRP, then reported TWRP after our controlled recovery return. Do not treat that later TWRP observation as spontaneous ROM fallback; no usable screen/touch confirmed.

Runner14527 exited0 on boot_completed; that does NOT mean ROM success. Final status ANDROID_UNLOCKED_UI_FAILED_RECOVERY_VERIFIED. Guarded helper returned the tablet to TWRP; capture runner69783 completed. Installed BOOT MD53f507c549441bb54e027cbb4ed20837c and unchanged recovery MD5cd9793e1ee8f284c9056b225885b5b1a verified. New system remains staged, no stock rollback, no live configuration workarounds, no second boot test. See result.json and v25-final-* snapshots, live-crash-late.txt, final-user-state.txt and recovery-state.txt. Next work is offline media allocator and app-process EGL initialization; do not treat SurfaceFlinger/bootanimation success as app rendering proof.

'''
status_file = project / 'CURRENT-STATUS.md'
status = status_file.read_text(encoding='utf-8-sig')
first, rest = status.split('\n', 1)
status_file.write_text(first + '\n\n' + note + rest.lstrip('\n'), encoding='utf-8')
print(json.dumps(result, indent=2))
