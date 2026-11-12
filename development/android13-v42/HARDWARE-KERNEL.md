# T110 kernel hardware checkpoint — 2026-11-05

The patched kernel boots on the physical SM-T110 with the installed TWRP ramdisk in the BOOT partition. Root ADB works. The user confirmed the menu and touch navigation. Fifteen seccomp/Binder runtime checks passed on the tablet. This is a real hardware kernel milestone, not an Android 13 OS boot.

## Test sequence

1. The unmodified compiled kernel plus stock ramdisk reached ADB. Stock Android UI did not finish booting. Logs show the stock `galcore.ko` rejected for version-magic mismatch and SIGILL in stock `libskia.so` at instruction `ee100f10` (CPU-ID register read). Do not force-load mismatched modules or label this as successful stock Android boot. Evidence: `hardware-tests/20261105-baseline`.
2. Restored the original full BOOT partition and verified its checksum. Stock Android booted.
3. Put the already compiled patched kernel (`f4e735162c5050a7e7d2dbee1f1cff41ff26158ff5905375d140c7ce10377eb6`) with the installed recovery ramdisk in BOOT. RECOVERY was not replaced. All 16 MiB of the written partition were read back and checked.
4. Root ADB, framebuffer/menu and touch worked. Nine seccomp/no_new_privs checks and six Binder protocol/context/scatter-gather checks passed. Tests temporarily set SELinux permissive, then restored enforcing. No synthetic QEMU policy was loaded on the tablet. Existing recovery policy loaded; the kernel advertised policy version 30. This does not validate the future Android 13 policy.
5. SYSTEM direct-read scan returned all 1,594,884,096 bytes with zero final unreadable blocks, but the kernel logged one CMD18 timeout at absolute sector 3398400, recovered through single-block retry. This is not a controller-error-free pass. Three subsequent direct 64 KiB reads of the affected window returned identical data without another timeout. The same three reads under the installed recovery kernel also passed without a timeout.
6. Restored and checksum-verified the stock BOOT partition again. Original RECOVERY checksum remained unchanged. Stock Android reports boot_completed=1 and kernel 3.4.5-2751957. The complete repaired dictionary still matches stock SHA-256.

## Interpretation

The previous persistently unreadable dictionary blocks remain readable. A recovered timeout has recurred, so long-term storage health remains open; no further SYSTEM repair writes were performed. Touch I2C timeouts/reinitialization also appear in the older installed TWRP logs and therefore are not established as a regression introduced by the kernel backports. User touch confirmation is positive, but it is not a long-duration suspend/input test.

The tablet is back on stock Android with installed TWRP available. Next: build Android 13 native userspace on E:, validate bionic and real Binder libraries, then boot init and ADB before graphics. Full modern Android remains unbuilt/unbooted.

Machine-readable outcome: `hardware-tests/LATEST-RESULT.json`. Detailed evidence and flash/readback/rollback logs: `hardware-tests/20261105-modern-diagnostic`.
