# SM-T110 navigation-button LED evidence - 2026-11-13

Status: PARTIALLY ANSWERED; no real LED backend or variable dimming established.
The owner reports working LEDs on stock. That report remains a hardware lead;
this source/binary audit does not disprove it. No tablet command, firmware/kernel
write, build interruption, GPIO/register write or lights-HAL change was made.

## Scope and method

Applied the reverse-engineering workflow to the exact restored ANI7 stock lights
ELF and original boot image, cross-checking the preserved kernel source/config.
No REA engine/CLI was available; the evidence below comes from ordinary ELF
parsing, readelf, ARM objdump, gzip inspection and source reads. No REA Evidence
IDs or runtime observations are claimed.

Original stock boot SHA256:
216d06a4a721a84ad578196b1a69e753c2b88d1b166446310f78765ab30a6be7.
Stock lights.mrvl.so SHA256:
0c6db0c14270dc76fbc9cfae1f8f0021a2688cb075cc87a81cda4e5f00eae0f1.
Kernel source checkpoint: Tapuz97/android_kernel_samsung_goya,
tag t110-android13-v42-20261112 /3eb98fe728aefa780638a1bb2f487e19ba6fadcb.

## Observed stock binary behavior

- ELF32 ARM shared object, stripped. Dynamic object BUTTON_FILE_PATHS is16 bytes
  at VA0x2e54. Mapping ELF program segments and decoding its four pointers yields:
  /sys/class/sec/sec_touchkey/brightness;
  /sys/class/leds/button-backlight/brightness;
  /sys/class/backlight/touchkey-led/brightness; NULL.
- HMI.methods points to0x3004; its open entry is Thumb0xad1 (code0xad0).
  The open function compares the strings backlight/keyboard/buttons and chooses
  each setter. The buttons branch selects Thumb0xc99 (code0xc98).
- Exported initialize_fds at Thumb0x11e5/code0x11e4 iterates candidate lists,
  calls open(path,O_RDWR), and stops on a nonnegative descriptor or NULL terminator.
  Thus strings in all three paths are alternatives, not proof any path exists.
- The actual buttons setter at0xc98 masks off alpha, converts any nonzero RGB
  value to integer1, and passes that value to the integer writer at0xbe0.
  Zero becomes0. This stock HAL implements binary on/off for button lighting;
  it does not send a0..255 dimming value. The LCD setter at0xd08 instead computes
  the usual weighted RGB brightness and is a distinct path.
- The original stock boot ramdisk's init.pxa988.rc lines62-63 explicitly chown/
  chmod /sys/class/sec/sec_touchkey/brightness. This is evidence of an intended
  board path, but chmod/chown do not create a missing kernel attribute.
  Generic init.rc/init_bsp.rc/init_charging.rc also mention LED-class alternatives.

## Observed preserved kernel source/config

- v42 defconfig enables CONFIG_MACH_GOYA, TOUCHSCREEN_BT532_TS, PM805/PM822,
  LED class and timer triggers. No actual CONFIG_LEDS_* device provider is enabled;
  the GPIO LED provider and TC360 touchkey driver are disabled.
- BT532 factory setup creates sec_touchkey (bt532_ts.c:3562), then installs
  touchkey_attr_group. Its complete attribute table (around3498-3520) contains
  threshold, sensitivity and raw-key readouts, with no brightness attribute or
  LED write callback. Broad source searches found the candidate brightness
  registrations in other controllers (TC360/MMS/MXT/Cypress), not active BT532.
- board-goya-input.c bt532 platform data supplies touch power, dimensions and
  orientation; it has no LED GPIO/brightness callback. The power regulator is
  shared touch power and must not be repurposed as an LED brightness control.
- board-goya.c's RT8547 code describes a camera strobe/torch (1000mA/100mA), and
  its provider is disabled. It is not evidence of a navigation LED circuit.
  PM822 source did not establish a separate key-light child/backend.

## Stock-vs-source gap and unknowns

The original stock zImage was decompressed from its gzip stream at offset16439,
producing8398916 bytes and banner Linux3.4.5-2751957, dated2014-09-23. No IKCONFIG
was recoverable. A bounded strings check found sec_touchkey but no alternate
button-backlight/touchkey-led class name. This does not substitute for recovering
all compiled registration code or observing sysfs. A difference between Samsung's
shipped kernel and released/preserved source is still possible.

Physical population, a currently usable sysfs endpoint, the original kernel's
actual LED config, and PWM/current-level dimming remain unverified. Do not infer
brightness capability from the generic HAL or enable undocumented PMIC/GPIOs.
Do not replace the known-good BT532 firmware to guess at illumination support.

## Integration recommendation

Retain the prior input/kernel/firmware fixes. Keep native LineageOS light settings
independent of hardware-navigation enablement. A HAL may support LIGHT_ID_BUTTONS
once an actual node/backend is established; unsupported writes should return an
error rather than pretending success. The stock path is binary-only at the HAL
level, so a genuine brightness slider additionally needs an observed multi-level
backend/max_brightness, or a separately validated hardware PWM/current driver.
Do not advertise adjustable brightness solely because a positive value lights it.

Safest next hardware evidence, at a later authorized stock comparison: read-only
inventory of /sys/class/sec/sec_touchkey, /sys/class/leds and /sys/class/backlight,
including candidate brightness/max_brightness values and symlink targets, then
an owner-observed lighting change through stock's existing controls. This task
has not initiated a stock flash or a new boot test.

## Retained native evidence

In /root/t110-lineage14/reference/stock-ani7:
lights-path-evidence.json, stock-ramdisk-led-evidence.json, stock-zImage,
stock-kernel.uncompressed and lights-disassembly.txt. The last file's default
ARM disassembly contains Thumb regions; use objdump -M force-thumb around
0xad0/0xc98/0x11e4 as above rather than interpreting those regions as ARM code.
