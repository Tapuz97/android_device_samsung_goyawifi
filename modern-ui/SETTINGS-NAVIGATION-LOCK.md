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

Installed image raw SHA256:
eb9d8955ef8df81f04f424f2b3d0c4bc2d3451395ed36ca7648fd696212067f1.
Runtime checks passed for category Back, nested gestures Back, toolbar-only
search, navigation search results, MODE_FADE at screen-off and wake to Settings.
Physical Power-transition appearance is pending owner confirmation.

Settings uses device-protected storage: its index locale cache is under
/data/user_de/0/com.android.settings/shared_prefs/index.xml. Clearing only that
flag file refreshes renamed categories without dropping the search database or
saved queries. The Settings app was stopped and the database hash was verified
unchanged across flag deletion. The CE /data/data path is not the active index.

Screen captures must follow UIAutomator's settled hierarchy, rather than precede
it: a newly opened native category can otherwise yield the outgoing frame.
The known prior BootAnimation native SIGSEGV appeared in the startup snapshot;
it is separate from these Settings/lock changes. No Java crash occurred in the
bounded runtime tests. Temporary screen timeout was restored to 60000.
