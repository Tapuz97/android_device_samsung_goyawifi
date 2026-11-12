"""Record the completed v5 hardware trial from saved logs and artifact hashes."""
import hashlib
import json
from pathlib import Path
root = Path(__file__).resolve().parents[1]
trial = root / 'hardware-tests/20261105-modern-init-v5'
artifact = root / 'artifacts/android13-ramdisk-v5'
provenance = json.loads((artifact / 'provenance.json').read_text())
runtime = (trial / 'runtime-tests.txt').read_text()
assert all(x in runtime for x in ['PATH_EXIT=0', 'CGROUP_EXIT=0', 'BIONIC_EXIT=0', 'Enforcing'])
assert 'BINDER_EXIT=0' in (trial / 'binder-test.txt').read_text()
assert 'RECONNECTED' in (trial / 'reconnect-test.txt').read_text()
assert 'STOCK_BOOT_AND_RECOVERY_VERIFIED' in (trial / 'rollback-log.txt').read_text()
original = (trial / 'usb-transfer.bin').read_bytes()
returned = (trial / 'usb-transfer-return.bin').read_bytes()
assert original == returned and len(original) == 2097189
assert hashlib.sha256((artifact / 'KERNEL.img').read_bytes()).hexdigest() == provenance['full_boot_sha256']
result = {
    'date': '2026-11-05',
    'status': 'ANDROID13_MINIMAL_INIT_ADB_HARDWARE_BOOT_PASSED',
    'artifact': 'artifacts/android13-ramdisk-v5',
    'kernel_sha256': provenance['kernel_sha256'],
    'full_boot_sha256': provenance['full_boot_sha256'],
    'evidence': str(trial.relative_to(root)),
    'android13_minimal_userspace_booted': True,
    'full_os_or_graphical_ui_booted': False,
    'root_adb': True,
    'selinux': {'global_enforcing': True, 'policy': 'Android 13 eng recovery',
                'qualification': 'Engineering recovery and su domains are permissive; not a production policy validation'},
    'mmap_randomization_bits': 16,
    'tests': {'opath_and_realpath': 'PASS', 'processgroup_create_inherit_kill_cleanup': 'PASS',
              'static_bionic_subset': 'PASS', 'android13_libbinder_parcel_roundtrip': 'PASS',
              'usb_transfer_bidirectional': 'PASS', 'adb_host_reconnect': 'PASS'},
    'usb_transfer': {'bytes': len(original), 'sha256': hashlib.sha256(original).hexdigest()},
    'stock_return': {'boot_completed': True, 'android_version': '4.2.2', 'kernel': '3.4.5-2751957',
                     'boot_full_readback_verified': True, 'separate_recovery_unchanged': True},
    'current_state': 'Stock Android restored and boot_completed=1 verified',
    'remaining': ['Full Lineage system build and product integration', 'Graphics and hardware HAL compatibility',
                  'Modern normal-boot init/APEX/services and production policy', 'libhwbinder runtime',
                  'Previously recovered MMC timeout requires ongoing monitoring'],
    'prior_trials': {'v3': 'Modern init reached; FunctionFS string-table use-after-free crashed kernel',
                     'v4': 'Modern init and probes passed, USB enumerated but AIO transport offline; watchdog returned to TWRP'},
}
(trial / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
(root / 'hardware-tests/LATEST-RESULT.json').write_text(json.dumps(result, indent=2) + '\n')
provenance['status'] = result['status']
provenance['hardware_result'] = str((trial / 'result.json').relative_to(root))
(artifact / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
host = root / 'BUILD-WORKSPACE.json'
data = json.loads(host.read_text())
data['state'] = 'Full source sync complete; build-only lineage_t110_system-eng systemimage started'
data['full_source_manifest'] = 'evidence/lineage20-full-manifest-pinned.xml'
data['system_output'] = 'T110Build:/root/t110-build/out-system'
host.write_text(json.dumps(data, indent=2) + '\n')
print(result['status'])
