# Bluetooth and microSD integration

This is an engineering SM-T110 port, not a public release qualification.
The receipts in `evidence/hardware-bt-sd` distinguish controller tests,
compiled-source checks, installation and native Android tests.

Current gate: v38/BOOT45 is installed, but native Bluetooth enable/discovery
has not passed. The permanent identity-mode and late-watchdog fixes compiled;
E disappeared before export, so v39 is not yet a verified image or installed.
See CURRENT-STATUS.md and combined-build-export-blocked.json before resuming.

## Bluetooth transport

The SD8777 presents SDIO vendor/device 02df:9132. Wi-Fi uses function 1;
Bluetooth uses function 2 and the existing `mbt8xxx` character driver.
Its transport is `/dev/mbtchar0` carrying H4 packets, not a guessed UART.

The module is built with the qualified kernel's configuration and symbols.
Patch 0100 restricts character nodes to 0660 and adds `require_fw_ready`.
The production loader uses `fw=1 drv_mode=1 debug_intf=0 require_fw_ready=1
req_fw_nowait=0`. `fw=0` does not register the character device. A running
Wi-Fi combo firmware is reused; no firmware download or shared power cycle
is allowed on this path. Firmware absence fails explicitly.

The default H4 implementation writes packet type and data with `writev`.
This old character driver's VFS fallback invokes its packet-oriented write
separately for each iovec. Patch 0101 selects a contiguous single write for
the matching character-device descriptor, while keeping UART behavior.
A short write fails rather than submitting a packet tail as a new packet.
The driver's partial-read path was also checked: it removes only the consumed
bytes, requeues the remainder at the head, and suppresses duplicate H4 type
insertion with `read_continue_flag`. Native H4 header/payload reads are supported.

The vendor adapter uses the standard Android Bluetooth HAL and native stack.
The board loader reads the controller's own BD_ADDR and saves it in a
restricted vendor-data file. It does not program a generated identity.
The node has a dedicated vendor SELinux type; private platform types are
not referenced from vendor policy. The system remains enforcing.

The radio-completion trigger belongs in the platform boot script: Android13
rejects `init.svc.*` triggers in vendor scripts. The final vendor init file
only defines the loader and its data-directory preparation. BOOT45 starts it
after Wi-Fi's loader completes. The HCI service uses its original native init
definition. Patch0104 embeds the installed implementation directory as an ELF
RUNPATH, separately for lib/lib64. An LD_LIBRARY_PATH service override failed
under secure launch and was removed; the intermediate BOOT44 is not the final
configuration.

Controller reset, version, feature and identity commands passed. The
controller reports manufacturer 72 and HCI version 6; the actual feature
bit 38 confirms LE controller capability. These checks alone do not prove
native discovery, pairing, HID, BLE applications or Bluetooth audio.

## Regression harness correction

The upstream H4 receive test registered callbacks after sending its bytes.
On this device the SCO/event callback could arrive first, leaving an
unbounded condition-variable wait. Saved callback output and a stack trace
establish the test-harness race. Patch 0103 registers expectations first
and uses predicate waits with a two-second bound. Payload assertions remain.
All four tests pass on ARM: two existing UART tests and two packet-write
regressions. No test is skipped and no controller commands are sent by them.

## microSD

The external slot is mmc1 at
`/devices/platform/sdhci-pxav3.0/mmc_host/mmc1/*`.
The normal vold fstab declaration is `voldmanaged=sdcard1:auto`.
Five actual POSIX pattern checks cover the slot and exclude internal eMMC,
the radio's SDIO host, and mmc10. The known kernel supports VFAT/FUSE;
exFAT is not qualified. No card is formatted or adopted automatically.

The app probe writes only its own unique 64 KiB temporary file on an
already-mounted removable volume, syncs, reads, compares and removes it.
No card means the physical mounting/read-write check remains pending.

## Build and installation

`scripts/build_bt_sd_rom.sh` builds the image and production H4 tests.
`build_bt_h4_tests.sh` can rebuild the corrected test harness independently.
`export_bt_sd_v37.py` verifies native/Google payload preservation, file
metadata, SELinux attributes, filesystem consistency and Bluetooth AOT code.
The initial BOOT43 integration retains BOOT42's kernel and updates policy,
fstab and node ownership. The corrected v38/BOOT45 pair also includes the
platform startup trigger and the service RUNPATH. BOOT45 retains that same
kernel and returns to the normal native HAL service definition.

Installation uses a verified forward/reverse block delta in the unmounted
userdata system image because there is insufficient space for another full
image. Both Android data profiles and TWRP are retained. The physical
SYSTEM partition is never a write target. Boot and system form a paired
update, and both are rolled back if their post-write hashes disagree.

`prepare_bt_v38.py` performs its two-file correction on a verified local clone
and checks ELF RUNPATH, metadata, init syntax and filesystem consistency.
Its final delta is32768 bytes; the initial v37 integration delta was8982528.
No package or directory is removed by either image update.

`qualify_bt_sd_v37.py` (now pinned to the v38 installation receipt) checks automatic loader startup, native adapter
enable/disable, app discovery and BLE scan requests, existing Wi-Fi DNS/TLS,
storage and process stability. Accessory pairing/audio and physical card
checks are separate gates. Audio remains limited by the unfinished native
audio port; unsupported SCO/offload requests are not reported as successes.
