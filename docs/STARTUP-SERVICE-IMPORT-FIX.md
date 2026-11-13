# Service-import startup correction - 2026-11-13

## Evidence

Saved failed-boot records: `tests/lineage14-module-abi-logs-20261113-185025`.
The corrected GPU syscall succeeded: galcore identified the GC1000 and initialized,
then real Android init entered second stage at 2.127 seconds. This is not total boot time.
At 2.609-2.616 seconds init reported missing logd, debuggerd and vold services.
No system/etc/init files were parsed. The 1200-second safeguard eventually rebooted.

Nougat normally imports /system/etc/init through init's mount_all builtin.
Our verified loop is already mounted before init and deliberately avoids mount_all.
The missing explicit import therefore omitted all of the installed service files.
Standard init_user0 synchronously runs vdc --wait cryptfs init_user0. With no vold
registered there can be no cryptd socket, so vdc's socket-connect loop never exits.
This explains why USB configuration triggers and later boot actions never ran.

## Correction and regression

Add `import /system/etc/init` in the device init.mrvl.rc. Preserve the stock
service definitions and user initialization; do not bypass user setup or invent services.
Rebuild the ramdisk normally; retain the verified system image byte-for-byte.
`verify_init_service_imports.py` inspects the actual boot archive and extracts RCs
from the actual ext4 image, resolving imports and rejecting duplicate services.
It finds 45 services including vold, logd, SurfaceFlinger and Zygote.
Removing the new import reproduces the prior missing-service graph.
All 164 existing actual-image content comparisons and clean ext4 checks passed.

Candidate boot: a27e2e1f6c5db5a4a2eac405e59acfaf0d3e9a9995efaf7db0f1715a53b2b48a
System unchanged: 60a0f45f77076d8b72a64d82cbb0159cf6f6a7bb0e4dca40ccb67e86069899bd
Installation proof and subsequent boot observations are in tests/lineage14-service-import-fix.
Never write physical SYSTEM p15. Use canonical recovery_transport.py, not shell stdin.
Normal recovery exit remains exactly `/sbin/reboot recovery_done`.

## Service-import boot outcome

Hardware serial3004523270272200 appeared on USB as0123456789ABCDEF because the
new device RC omitted iSerial. Its ro.serialno and ro.boot.serialno both matched
3004523270272200, and Android release was7.1.2. The old observer's fixed USB serial
missed it; the new observer checks the placeholder only after verifying identity.
The user correctly reported enumeration. This was not continued failure to reach init.

The service import fixed the storage wait: vold, SurfaceFlinger, Zygote and other
native services started. SurfaceFlinger then aborted repeatedly because the stock
EGL library could not load its hard-coded /system/lib/egl GLES2 path. Actual logs
also reproduced the old vsync permission failure. Both fixes were already in the
Android13 archive. See PRIOR-WORK-CARRYOVER.md for their combined Nougat adaptation.
All available live logs and the failed boot's last_kmsg were saved before returning
the tablet to TWRP through ADB. The tombstone files were empty; do not claim a
complete native backtrace. No completed Android/UI boot was observed in this test.
