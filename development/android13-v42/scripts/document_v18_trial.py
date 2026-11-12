"""Record the captured v18 failure and the ongoing kernel correction."""
from pathlib import Path
import json

p = Path(__file__).resolve().parents[1]
trial = p/'hardware-tests/20261107-132951-core'
result = dict(status='USER_STORAGE_ACL_FAILURE_RECOVERY_VERIFIED', hardware_tested=True,
              hardware_validated=False, full_boot_passed=False, boot_completed=True,
              boot_completed_is_success=False, user_unlock_completed=False,
              first_system_server_pid=363, replacement_system_server_pid=1738,
              wifi_framework_service_started=True, wifi_radio_validated=False,
              root_cause='vold SetDefaultAcl: ext4 POSIX ACL disabled in kernel; user 0 preparation fails',
              fatal_exception='UserDataPreparer: error rebooting into recovery',
              tablet_state='TWRP', normal_boots_started_by_agent=1,
              controlled_return_to_recovery=True, stock_rollback_performed=False,
              system_md5='40b250a4afe35086bd6ab7610300ce24',
              boot_md5='f3f30815e1823ea4425847e3020a7d4b',
              recovery_md5='cd9793e1ee8f284c9056b225885b5b1a',
              user_visual_or_touch_confirmation=False)
(trial/'result.json').write_text(json.dumps(result, indent=2)+'\n')
pair_path = p/'artifacts/lineage20-rom-v18/rom-pair.json'
pair = json.loads(pair_path.read_text())
pair.update({k:result[k] for k in ('status','hardware_tested','hardware_validated','boot_completed','full_boot_passed')})
pair.update(hardware_trial=str(trial.relative_to(p)), hardware_boots_this_pass=1,
            tablet_access_this_pass=True, limits=['User storage preparation fails: kernel lacks ext4 ACL',
            'Wi-Fi feature publication does not establish working radio/HAL', 'Usable UI and touch unverified'])
pair_path.write_text(json.dumps(pair, indent=2)+'\n')
entry = '''## v18 FULL BOOT FAILED - KERNEL ACL CORRECTION BUILDING - 2026-11-07

Runner88799 completed and returned to verified TWRP. Trial hardware-tests/20261107-132951-core shows Wi-Fi framework service now starts, but vold cannot set the default ACL on /data/media/0 (EOPNOTSUPP). This aborts user storage preparation, triggers recovery failure and kills system_server363; replacement1738 detected. The observed boot_completed=1 is NOT a pass. Recovery and BOOT hashes unchanged. No user UI/touch confirmation. No stock rollback.

Exact cause confirmed in archived kernel.config: CONFIG_EXT4_FS_POSIX_ACL is disabled. New Ubuntu kernel build53847 enables only that option in a separate out-storage-acl, using unchanged kernel-binder-secctx sources; all prior artifacts preserved. Kernel sources/toolchain are in Ubuntu, NOT T110Build. T110Build contains Android source on E:. Persistent T110Build shell12296 is idle. After kernel build, run archive_storage_acl_kernel.py in Ubuntu, package_v27_boot.py and verify_v27_boot.py on Windows. Correct pair will be android13-full-v27/system-pair.json with unchanged v18 system already staged. Flash new BOOT and start a full boot immediately after offline checks; standing user authorization explicitly requires this. Do not use --reuse-boot for the NEW kernel; expected installed BOOT remainsf3f30815e1823ea4425847e3020a7d4b.

'''
status = p/'CURRENT-STATUS.md'
status.write_text(entry + status.read_text(encoding='utf-8'), encoding='utf-8')
print(result['status'])
