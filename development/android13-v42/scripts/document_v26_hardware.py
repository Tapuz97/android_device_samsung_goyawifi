"""Record the single v26 hardware result without treating boot_completed as success."""
import json
from pathlib import Path

p = Path(__file__).resolve().parents[1]
trial = p/'hardware-tests/20261107-105547-core'
read = lambda name: (trial/name).read_text(encoding='utf-8-sig', errors='replace')
state = read('final-user-state.txt')
assert state.splitlines()[1:4] == ['1', 'stopped', '355']
assert 'state=RUNNING_UNLOCKED' in state and '212188' in state
late = read('closeout-state.txt')
assert '2243' in late and late.splitlines()[2] == 'running'
crash = read('v26-closeout-graphics.txt')
assert 'FATAL EXCEPTION IN SYSTEM PROCESS: NetworkStats' in crash
assert 'bandwidthSetGlobalAlert' in crash and 'No such file or directory (code 2)' in crash
assert 'C2AllocatorIon::setUsageMapper' not in crash and 'Failed to get EGL_DEFAULT_DISPLAY!' not in crash
assert 'T110 EGL: Vivante process initialized before entrypoint lookup' in read('final-logcat.txt')
assert 'No service published for: wifi' in read('v26-user-start-framework.txt')
assert 'failed to sdcardfs_setup' in read('final-crash.txt')
recovery = read('recovery-state.txt')
assert 'f3f30815e1823ea4425847e3020a7d4b' in recovery
assert 'cd9793e1ee8f284c9056b225885b5b1a' in recovery
capture = json.loads(read('recovery-capture-result.json'))
assert capture['tablet_state'] == 'TWRP'
fb = json.loads(read('framebuffer-capture.json'))
assert fb['unchanged_pan'] and fb['before'][3] == '0,600'
result = dict(
    status='ANDROID_UNLOCKED_UI_RENDERED_STARTUP_FAILED_RECOVERY_VERIFIED',
    hardware_tested=True, hardware_validated=False, boot_completed=True,
    full_boot_passed=False, user_0_state='RUNNING_UNLOCKED',
    user_unlock_uptime_ms=212188, boot_completed_observed_by_uptime_seconds=234.16,
    system_server_restart_observed=True, original_system_server_pid=355,
    restarted_system_server_pid=2243, last_live_uptime_seconds=536.73,
    original_allocator_crash_observed=False, original_egl_default_display_abort_observed=False,
    app_vivante_initialization_observed=True,
    framebuffer_observation='Active page contains status bar clock/battery and navigation buttons over black background; actual panel/touch not confirmed by user',
    framebuffer_image='framebuffer-page-1.png',
    systemui_initial_anrs=True, systemui_later_rendered=True,
    screenshot='Android screencap timed out; read-only raw framebuffer capture succeeded',
    normal_rom_boots_this_pass=1, boot_partition_writes_this_pass=1,
    framework_restart_was_automatic=True, live_configuration_workarounds=False,
    tablet_state='TWRP', controlled_return_to_recovery=True,
    stock_rollback_performed=False,
    installed_boot_md5='f3f30815e1823ea4425847e3020a7d4b',
    recovery_md5='cd9793e1ee8f284c9056b225885b5b1a',
    staged_system_md5='89a74dd23767c22cb60a1f06ccd8cc15',
    blockers=[
        'SetupWizard repeatedly terminates after missing Wi-Fi framework service',
        'NetworkStats bandwidthSetGlobalAlert receives ENOENT and terminates system_server later in the same boot',
        'sdcard aborts with failed to sdcardfs_setup',
    ],
    other_observations=[
        'SystemUI had two startup ANRs before a later process rendered status and navigation UI',
        'Normal screenshot buffer registration failed; raw framebuffer read succeeded',
        'media.codec was absent from service check despite process presence; codec functionality unvalidated',
        'The two original native failure signatures were absent from captured crash logs; this is not a complete hardware or media pass',
    ],
    recovery_capture=capture,
)
(trial/'result.json').write_text(json.dumps(result, indent=2)+'\n')
pair_path = p/'artifacts/android13-full-v26/system-pair.json'
pair = json.loads(pair_path.read_text())
pair.update({k:result[k] for k in ('status','hardware_tested','hardware_validated','boot_completed','full_boot_passed')})
pair.update(hardware_boots_this_pass=1, flashes_this_pass=1,
            hardware_result='../../hardware-tests/20261107-105547-core/result.json',
            user_0_state='RUNNING_UNLOCKED', tablet_state='TWRP')
pair['limits'] = ['UI rendering observed in framebuffer, but setup and later framework stability still fail',
                  'Wi-Fi service, network statistics and emulated storage blockers recorded',
                  'Panel/touch, media functionality and other unported hardware remain unvalidated']
pair_path.write_text(json.dumps(pair, indent=2)+'\n')
note = '''## v26/v17 FLASHED - UI RENDERED, LATER STARTUP FAILURE - 2026-11-07

User requested both fixes offline, build, then flash. All offline checks passed before transfer. Exactly one v26 BOOT flash/readback and one normal ROM boot were performed, trial hardware-tests/20261107-105547-core. Runner16628 completed on boot_completed; that is NOT a successful usable-ROM result.

User0 unlocked at212188ms and boot_completed was observed by234.16s. App EGL logs confirm explicit Vivante initialization. Captured crash logs show neither the old C2AllocatorIon::setUsageMapper null crash nor Failed to get EGL_DEFAULT_DISPLAY abort. SystemUI initially had two ANRs, then recovered; SystemUI1704 and launcher896 were observed running and raw framebuffer active page contained status/navigation UI over black. Android screencap timed out; raw framebuffer read only succeeded after redirecting dd's statistics away from binary output. Panel/touch observation was not received.

The ROM remains unusable: SetupWizard repeatedly terminates because the Wi-Fi framework service is absent; sdcard aborts at sdcardfs_setup. During the same uninterrupted boot, NetworkStatsService bandwidthSetGlobalAlert received ENOENT, causing a fatal system_server exception. system_server restarted automatically from355 to2243; this was not a second agent-initiated boot. No live config workaround was applied.

The guarded helper intentionally ended the failed test in TWRP. Recovery capture verified installed v26 BOOT MD5f3f30815e1823ea4425847e3020a7d4b and unchanged recoverycd9793e1ee8f284c9056b225885b5b1a. Staged v17 system89a74dd23767c22cb60a1f06ccd8cc15 remains installed; no stock rollback. See result.json, final-* evidence, v26-closeout-graphics.txt and framebuffer-page-1.png. Pair manifest records full_boot_passed=false. Next offline targets are the Wi-Fi service/setup contract, NetworkStats compatibility and emulated storage; keep the current two fixes.

'''
status_path = p/'CURRENT-STATUS.md'
first, rest = status_path.read_text(encoding='utf-8-sig').split('\n',1)
status_path.write_text(first+'\n\n'+note+rest.lstrip('\n'),encoding='utf-8')
with (p/'OFFLINE-V26.md').open('a',encoding='utf-8') as out:
    out.write('\n## Single hardware boot result\n\nFlashed once after all offline checks. Android unlocked and status/navigation UI rendered into the framebuffer. The two original native crash signatures were absent, but missing Wi-Fi service repeatedly killed setup, sdcard aborted, and a later NetworkStats exception restarted system_server. Full usable boot failed. The tablet was returned to verified TWRP, with v26/v17 still installed. See `hardware-tests/20261107-105547-core/result.json`. No extra boot or live configuration workaround was used.\n')
print(json.dumps(result,indent=2))
