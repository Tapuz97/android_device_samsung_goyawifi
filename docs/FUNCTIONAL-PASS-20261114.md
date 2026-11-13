# Lineage14 functional checks — 2026-11-13

Boot899925b4-0de0-4dc0-93a2-c1a820079278, system611bc2d2..., density200 override.
Evidence: tests/lineage14-functional-20261113. Initial pass completed before fixes.
Do not inherit Android13 PASS labels as Nougat results.

| Function | Initial result | Evidence / remaining check |
|---|---|---|
| Settings main/display/apps navigation | Incomplete | Launches accepted, but an existing crash dialog obstructed navigation. Repeat after its captured cause is fixed; command success is not rendering PASS. |
| Settings Developer options | FAIL | cryptfs_isConvertibleToFBE dereferences null fstab record, crashes vold; Settings times out and crashes. Bootstrap intentionally owns isolated /data, which is absent from fstab. |
| Settings search | Pending | Must exercise actual search input/results. |
| Wi-Fi driver/interface | PASS | Matched modules loaded; wlan0 exists. |
| Wi-Fi enable and scan | FAIL | Supplicant running at /data/misc/wifi/sockets/wlan0; framework connects to init's unconsumed /dev/socket/wpa_wlan0. ATTACH waits repeatedly, UI becomes slow. |
| Wi-Fi association/DHCP/DNS/HTTPS | Blocked | No IP/default route; user network connection needed after scan works. |
| Bluetooth controller/native enable | PARTIAL, then ON | Initial BLE_ON; normal IBluetoothManager.enable request reaches ON. Existing SD8777 packet transport retained, no shared radio power reset. |
| Bluetooth discovery/pairing/reconnect | Pending | ON alone is not proof; use native discovery and an owner peer. |
| Rear camera enumeration | PASS | CameraService exposes one rear HAL1 camera, orientation90, max1600x1200. |
| Camera app opening | FAIL | All required permissions granted; optional coarse location missing and prior permission dialog flag causes false critical-permission error. |
| Camera preview/JPEG/video | Blocked | Must exercise after permission flow; old startup native crashes remain. Prior Android13 USERPTR ION capture is a reference, not a Nougat pass. |

Prior sources reviewed: HARDWARE-BT-SD.md, LEGACY-NETWORK.md,
FUNCTIONAL-CHECKLIST.md, current Nougat wifi/control socket sources,
cryptfs/fs_mgr, Camera2 PermissionsActivity, device Bluetooth adapter/init,
and Nougat donor camera source. No source-disabled service/feature counts as fixed.

## Same-boot fixes and retest, 2026-11-14

These results use live replacements on the same kernel boot, not a newly flashed
image. Preserve that distinction when qualifying the packaged build.

| Function | Retest result | Evidence / limits |
|---|---|---|
| Developer options | PASS, automatic UI check | Guard missing fstab record in vold; declare existing USB accessory hardware so UsbManager starts. Page renders its controls and repeated cryptfs queries return promptly. |
| Settings search | PASS, automatic UI check | Entered bluetooth through the search control; Bluetooth and Bluetooth scanning results appear; selected Bluetooth result. Physical keyboard typing not qualified by injected input. |
| Wi-Fi scan and association | PASS | Global supplicant socket accepts IFNAME-prefixed commands; owner joined network and obtained DHCP lease. |
| Wi-Fi internet | PASS | T110 netd UID-rule attribute changed to match preserved kernel ABI; ping, DNS, certificate-verified HTTPS and ConnectivityService VALIDATED pass. Sleep reconnect remains pending. |
| Bluetooth toggle/discovery | PASS | Declare controller's supported LE feature so framework binds GATT and completes BLE_ON to ON. Names retrieved; normal off/on works. |
| Bluetooth pairing/file transfer | PASS | Gal's S23 bonded; owner confirmed receipt of t110-bluetooth-test.txt. OPP provider status200, 45/45 bytes. Bond retained through toggle. |
| Bluetooth internet sharing/audio/HID | NOT QUALIFIED | PAN connect/disconnect observed; file transfer is a separate confirmed result. Audio and input profiles need their own tests. |
| Camera app | PASS, automatic | Required camera permissions no longer treated as missing solely because optional location is denied. |
| Camera preview | PASS | Actual preview callback received; owner confirmed the live preview visibly changes and looks correct. |
| Still photograph | PASS, automatic | Two 1600x1200 JPEGs saved, including after force-stop/reopen; both fully decoded on host. Same cameraserver PID13436 survived both. |
| Camera video | UNTESTED | Still image success does not qualify video recording. |

Camera fixes: restore the stock ION allocation contract in both MemoryHeapBase
constructors without changing class layout; retain preview window until HAL detach
returns; give /dev/uio0 camera group access (0660, media owner preserved). The
encoder had exited with code255 after EACCES, rather than producing a JPEG.
Native allocator probe covers cached/uncached allocation, fd lifetime, ashmem and
fd-leak checks. Firmware/driver replacement was unnecessary for this encoder fault.

Raw logs, network identifiers and captured photos remain local/private.
Temporary USB stay-awake original value0 must be restored when testing finishes.

## Packaged candidate

Build and actual-image checks passed; 176 critical files extracted from ext4 match
the build outputs. Boot packaging checks the camera encoder permission in the
ramdisk. This candidate has not been flashed or boot-qualified yet.

- boot.img: 16777216 bytes, SHA256 55df8314699da4ae5b1736100bb798029d023aaf38a4202efb811b6725d8beaf
- system.raw.img: 1594884096 bytes, SHA256 37896dd65fac195e3d7c9291f0ee411a52ae6ab2011ac61eb3114d687e9bd00a
- Native build path: /root/t110-lineage14/artifacts/lineage14-first-build
- Installed physical base remains system611bc2d2 / boot0e226023; live replacements apply this pass's fixes until reboot. No additional full boot was performed.
