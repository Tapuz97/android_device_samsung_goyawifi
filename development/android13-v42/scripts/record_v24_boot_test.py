"""Record the single v24/v15 trial from captured evidence; no device operations."""
from pathlib import Path
import json

root=Path(__file__).resolve().parents[1]
relative='hardware-tests/20261107-001850-core'
trial=root/relative
read=lambda name:(trial/name).read_text(encoding='utf-8',errors='replace')
state=read('final-state-before-recovery.txt')
assert state.splitlines()[0]=='1' and 'State: BOOTING' in state
assert '258.73' in read('final-live-state.txt')
assert 'com.android.settings/.FallbackHome' in read('boot-completed.txt')
assert '/apex/com.android.art/lib/libart.so' in read('final-live-state.txt')
assert '/libartd.so' not in read('final-live-state.txt')
startup=read('startup-live-3.txt')
assert 'PermissionPolicyService took to complete: 2580ms' in startup
assert 'LocationManagerService$Lifecycle took to complete: 200ms' in startup
assert 'AppOpsControllerImpl.fetchCurrentActiveOps' in startup
failure=read('startup-live-4.txt')
assert 'FATAL EXCEPTION IN SYSTEM PROCESS: LockSettingsService' in failure
assert 'java.lang.AssertionError: 4' in failure and 'KeyStore.state(KeyStore.java:67)' in failure
recovery=read('recovery-state.txt')
assert '54325830bda64adfb02b3f1b204ea4de  /dev/block/mmcblk0p10' in recovery
assert 'cd9793e1ee8f284c9056b225885b5b1a  /dev/block/mmcblk0p9' in recovery
assert json.loads(read('recovery-capture-result.json'))['tablet_state']=='TWRP'
assert 'T110 GNSS probing declared services without waiting' in read('android-logs/t110-logcat.txt.1')
live='\n'.join(read(p.name) for p in trial.glob('full-logcat-*.txt'))
assert 'Failed to retrieve sender credentials' not in live

status='HARDWARE_USABLE_UI_FAILED_RECOVERY_VERIFIED'
result=dict(date='2026-11-07',status=status,artifact='artifacts/android13-full-v24',
    system_artifact='artifacts/lineage20-rom-v15/system.raw.img',
    agent_normal_boot_requests=1,agent_boot_partition_writes=1,additional_tests=0,
    framework_restart_observed=True,first_system_server_pid=360,later_system_server_pid=1424,
    boot_completed_property_observed=True,boot_completed=True,first_recorded_flag_uptime_seconds=258.73,
    usable_ui=False,full_boot_passed=False,touch_validated=False,
    user_observations=['Lineage animation','Still animation or blank screen after boot-completed flag'],
    last_android_uptime_seconds=326.44,last_android_user_state='BOOTING',
    last_resumed_activity='com.android.settings/.FallbackHome',
    improvements=dict(permission_policy_phase550_ms=2580,location_phase600_ms=200,
                      declared_nonblocking_gnss_probe_observed=True,standard_art_loaded=True,
                      lmkd_missing_sender_credentials_in_live_samples=0),
    blockers=[dict(component='SystemUI',exception='NullPointerException',
                   location='AppOpsControllerImpl.fetchCurrentActiveOps:186',
                   context='Creating KeyguardService'),
              dict(component='system_server / LockSettingsService',exception='AssertionError: 4',
                   location='android.security.KeyStore.state:67',
                   context='ensureProfileKeystoreUnlocked; framework process exited')],
    secondary_failure='media.swcodec native C2AllocatorIon crash; captured, not diagnosed',
    tablet_state='TWRP',recovery_identity_verified=True,recovery_unchanged=True,
    installed_boot_md5='54325830bda64adfb02b3f1b204ea4de',
    staged_system_md5='8ccd9a5ba9678902309e419e62d55aca',
    recovery_md5='cd9793e1ee8f284c9056b225885b5b1a',
    screenshot='screencap timed out; no pixel evidence inferred',
    stock_rollback_performed=False,active_test_runner=False,
    evidence_note='Persistent rotated logs include earlier boots. Current first system_server is PID360 at 19:46-19:47 device time; never count older PID413/1062 failures as this run.')
(trial/'result.json').write_text(json.dumps(result,indent=2)+'\n')
(root/'hardware-tests/LATEST-RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
pair_path=root/'artifacts/android13-full-v24/system-pair.json'
pair=json.loads(pair_path.read_text())
pair.update(status=status,hardware_tested=True,hardware_validated=False,
    boot_completed=True,usable_ui=False,full_boot_passed=False,hardware_boots_this_pass=1,
    flashes_this_pass=1,tablet_access_this_pass=True,hardware_result=relative+'/result.json',
    tablet_state='TWRP',active_test_runner=False)
pair_path.write_text(json.dumps(pair,indent=2)+'\n')
summary='''## v24/v15 single test FINISHED: startup improved, usable UI FAILED, TWRP verified - 2026-11-07

Exactly one agent normal-boot request and BOOT write in hardware-tests/20261107-001850-core. Runner45390 exited0 after seeing sys.boot_completed=1; that is NOT a usable-ROM pass. User saw Lineage animation, then still animation/blank instead of setup/home. First system_server360 crashed in LockSettingsService (KeyStore.state AssertionError4), naturally restarted as1424. Boot flag first saved at258.73s; at326.44s user0 remained BOOTING with no unlock, fallback home resumed. SystemUI also crashed creating KeyguardService with null list in AppOpsControllerImpl.fetchCurrentActiveOps:186. No touch confirmation; screencap timed out.

Improvements measured on first system_server360: permission-policy phase550=2580ms (previous natural-restart case39776ms), location phase600=200ms (previous13364ms), T110 declared/nonwaiting GNSS probe logged. Standard libart.so loaded; no libartd in captured maps. No missing-sender-credentials failures in current live log samples. Graphics exact-target swap and user-visible Lineage animation confirmed. These do not establish working GPS or a clean complete boot.

Guarded recovery helper invoked once after final capture; root TWRP/CID and installed BOOT MD554325830bda64adfb02b3f1b204ea4de, unchanged recovery MD5cd9793e1ee8f284c9056b225885b5b1a verified. Staged v15 MD58ccd9a5ba9678902309e419e62d55aca. Runner38284 finished recovery capture; no active runner or pending question. Leave tablet in TWRP. No second test or live configuration edits. Pair/result status HARDWARE_USABLE_UI_FAILED_RECOVERY_VERIFIED; boot_completed=true records only the observed property, full_boot_passed=false and usable_ui=false are authoritative.

Saved current live logs, ANRs/dropbox, persistent logs and tombstones. Rotated persistent files include prior boots: filter current PID360/1424 and boot segment before analyzing. Additional media.swcodec C2AllocatorIon crash saved, not diagnosed. Next offline work: keystore/user-unlock failure and SystemUI app-ops null handling, then re-evaluate startup; do not merely bypass the keystore assertion or claim success from boot_completed. Earlier sections below are historical.

'''
p=root/'CURRENT-STATUS.md'; s=p.read_text(encoding='utf-8')
p.write_text(s.replace('\n\n','\n\n'+summary,1),encoding='utf-8')
p=root/'OFFLINE-V24.md'; s=p.read_text()
s=s.replace('\n\n','\n\n**Hardware update, 2026-11-07:** The subsequent single test failed usable UI despite an observed boot-completed flag. Permission/location startup improved, but SystemUI and keystore/user-unlock errors remain. Tablet returned to verified TWRP. See [test result](hardware-tests/20261107-001850-core/result.json). The offline report below is historical.\n\n',1)
p.write_text(s)
print(status)
