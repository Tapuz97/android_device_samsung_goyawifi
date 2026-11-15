# Settings navigation and lock transition

Requested changes: one Gestures & Navigation category; Back instead of the old
hamburger; search inline at the right of the Settings title; fix the visible
rotation/jerk on a single Power press before locking.

The proven CMParts button page is the parent category. Its alias, catalog and
screen titles use Gestures & Navigation. All 45 original preference keys are
retained, including hardware/onscreen navigation and backlight controls. A native
link opens the existing Settings GestureSettings activity; that activity remains
enabled and searchable but no longer advertises a duplicate dashboard tile.
Its hardware capability filters and existing user choices are unchanged.

SettingsDrawerActivity keeps native category/package-update listeners and their
normal lifetime. Its obsolete drawer stays locked closed, and the legacy
showMenuIcon API now supplies the platform's auto-mirrored Material Back arrow.
SettingsActivity uses native Back handling for category/subpage stacks, showing
no Back on the root dashboard. CMParts alias entry points also enable Back.
Genuine overflow options remain available.

The dashboard's duplicate large search row is removed. The existing native
SearchView remains in the action bar with always|collapseActionView, rather than
ifRoom. Its index, query/results and keyboard path remain native.

Lock transition: this board uses ro.sf.hwrotation=270, while the legacy
ColorFade cooldown redraws a screenshot. This creates a plausible rotation flash
at sleep. The T110 overlay selects native MODE_FADE. That path now creates only
a compositor dim layer, skips screenshot/EGL/shader setup, and handles its
bufferless surface cleanup safely. The fade uses config_shortAnimTime, while
normal global animator settings are respected. Rotation settings, Power-key
policy, key maps, sleep/wake and the kernel are unchanged.

Reference for the newer compositor-only fade path:
https://github.com/aosp-mirror/platform_frameworks_base/blob/android-13.0.0_r1/services/core/java/com/android/server/display/ColorFade.java

Full-image checks, actual Settings/CMParts resources and compiled service
contents passed. The checker also verifies all 13 current app icons remain
correctly selected with 65 matching density images. Runtime checks must verify
the category/back/search flows and physical lock behavior before claiming them
hardware-qualified. No continuous logging/capture is required.
