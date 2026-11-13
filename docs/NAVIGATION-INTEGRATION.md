# T110 native navigation integration - 2026-11-13

Status: SOURCE_INTEGRATED_OFFLINE_CHECKED. Full ROM compile and physical tests
remain the parent build's responsibility; no tablet action occurred here.

## Physical navigation and touch navigation

The product preserves the actual input maps: gpio-keys emits HOME102,
VOLUME_DOWN114 and VOLUME_UP115; sec_touchscreen emits APP_SWITCH139 and BACK158.
The kernel, touchscreen firmware and event production were not replaced or
disabled by this software change. Framework config now declares actual hardware
key mask83 (Home/Back/Recents/volume) and wake mask1 (Home).

LineageOS's existing Buttons setting and CMSettings.Global.DEV_FORCE_SHOW_NAVBAR
remain the user-facing mode control. A default-off product capability makes
that standard option available even without a separate kernel key-disable node.
When the T110 enables the touch navbar, PhoneWindowManager filters only board
Home/Back/Recents/Menu key events from gpio-keys/sec_touchscreen, before wake,
shortcut and application dispatch. It consumes both press and release events.
It does not disable the shared touchscreen input device, Power, volume, external
keyboard navigation, injected keys or virtual navigation-bar events.

The policy is gated by the product resource plus the existing navbar setting;
other products retain their previous behavior. Setting persistence, user-switch
observation and on-screen bar creation continue through the existing framework.

## Independent button lighting controls

Existing CMParts ButtonBacklightBrightness controls were extended, rather than
introducing an app or a second brightness-setting system. For products declaring
independent button lighting and real variable brightness, the native dialog shows
both the checkbox and slider. Off disables/mutes the slider but preserves its
last nonzero level; turning it on restores that level. Confirmed changes use the
existing secure BUTTON_BRIGHTNESS and timeout settings, with a dialog preference
remembering the selected level while off. Cancel does not commit a new level;
dialog recreation preserves both enabled state and the selected level.

Touch-navigation mode no longer disables this preference or forces light output
to zero when the product opts into independent control. PowerManager caches the
capability with its existing configuration; no new polling/writer was added.
Existing binary-only devices retain the checkbox-only dialog; other devices
retain their normal controls. Screen-off, timeout and power policy still govern
when a configured light is lit.

The actual T110 LED backend remains unestablished in this build. Its product
config_buttonBrightnessSettingDefault is explicitly0, keeping unsupported LED
controls hidden. No variable-brightness capability or physical LED operation is
claimed. The stock HAL's generic fallback paths and binary on/off setter do not
prove a populated dimmable T110 backlight. Enable controls only after proving a
real hardware control and implementing its lights HAL/backend.

## Source files

- frameworks/base/core/res/res/values/config.xml and symbols.xml: default-off
  config_useFrameworkNavigationKeyDisabler/config_independentButtonBacklight.
- frameworks/base/services/core/java/com/android/server/policy/PhoneWindowManager.java:
  cached product capability and early board-key filter.
- frameworks/base/services/core/java/com/android/server/policy/PhysicalNavigationKeyPolicy.java:
  board-device/key selection preserving virtual/injected/other key events.
- frameworks/base/services/core/java/com/android/server/power/PowerManagerService.java:
  independent lighting configuration, preserving normal behavior by default.
- packages/apps/CMParts/src/org/cyanogenmod/cmparts/input/ButtonSettings.java:
  standard native mode control and independent backlight availability.
- packages/apps/CMParts/src/org/cyanogenmod/cmparts/input/ButtonBacklightBrightness.java
  and res/layout/button_backlight.xml: native checkbox+slider and saved-level behavior.
- device/samsung/goyawifi/overlay/frameworks/base/core/res/res/values/config.xml:
  actual key masks, native framework mode capability and unadvertised LED support.

## Checks performed

scripts/verify_navigation.py host-compiles the actual new Java filter with Java8
against the platform's known key-code constants, then exercises20,808 combinations
of board/external/null device names, virtual and real device IDs, injected/virtual
flags and key codes0..288. All cases passed, including explicit preservation of
Power/volume and synthetic navigation. XML capability values, vertical layout
for the combined native controls, and policy placement before wake handling also
passed. git diff --check passed for frameworks/base and CMParts.

The native dialog/framework require the complete Android build for actual Java
type/resource compilation. Physical mode switching, wake/touch, and any eventual
LED output must still be checked on the tablet. Host filter tests do not prove
hardware behavior, event delivery or visible Android UI rendering.
