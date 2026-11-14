# LineageOS17.1 / Android10 handoff

Keep Lineage14.1 source `ceebd0c9a6c3298765757522f88d75d0bd47b4eb` and the exact installed pair as rollback.
No Android10 build has been started; no claim its GPU/HAL integration works yet.
StatiXOS gauguin binaries target Xiaomi Snapdragon/Adreno hardware, not the T110.

## Carry forward, do not rediscover

- Boot: matched kernel/module ABI; initramfs archive-end correction; custom stage
  owns loop-system/isolated-data mounts and execs init second stage. Preserve daemon
  symlinks to real init, SELinux init label and recovery_done handoff.
- GPU: stock Vivante EGL native-window contract, dequeue/buffer-count rules,
  preserved allocator layout and actual dma-buf lifetime; qualify real frames and
  hardware acceleration rather than a successful software-rendered boot.
- Camera: stock ION heap mask4/cached flags3/export fd; both MemoryHeapBase
  constructors; preserve object ABI and old Vector vtables/constants. Retain
  preview window until HAL detach returns; /dev/uio0 media:camera0660 for JPEG.
- Wi-Fi: global wpa control socket accepts IFNAME commands; kernel3.4 UID rule
  attribute FRA_UID_RANGE20, not conflicting19. Test DNS and HTTPS, not association alone.
- Bluetooth: packet transport /dev/mbtchar0, SD8777 init and LE feature/GATT binding;
  pairing/OPP does not establish A2DP/SCO/PAN/HID.
- Audio: stock44100Hz policy, ALSA data/plugins and libacm dependency closure;
  exact libacm->libcrypto linker shim; AP/GSSP clock controls and ownership;
  short legacy stream callback proxy, local HiFi routing and STREAM_IN_ACTIVE
  lifecycle. Preserve normal Bluetooth policy. Recorder handles save failure,
  actual PCM bytes and mono WAV byte rate; see latest media report.
- Input: native physical/onscreen navigation choice, key policy, rotation and
  readable200dpi. Do not guess LED registers; backend remains unproven.
- Power: preserve actual kernel suspend and BT532 resume path. One successful
  unplugged cycle is a baseline, not exhaustive validation.
- Performance: no continuous snapshots/serial/screen streaming during timings;
  bounded logs only. Keep memory/JIT/zram findings and confirm for Android10.

## Android10 investigation order

1. Compare framework/libc/linker/HAL/binder requirements against this kernel and
   vendor ABI. Identify needed legacy wrappers and kernel backports before a full sync/build.
2. Prove a hardware-accelerated window path; do not regress to software rendering.
3. Port preserved compatibility changes with exact upstream pins and isolated tests.
4. Build a separate candidate; keep14.1 images/data/source unmodified.
5. Re-run full physical functionality tests. Bring forward evidence, not PASS labels.

Local-only raw logs/photos/audio/identifiers stay local. Use sanitized conclusions
for public source and release text. Never publish Jack credentials or platform keys.
