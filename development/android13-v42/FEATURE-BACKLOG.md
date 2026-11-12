# Owner-requested features after functional qualification

Added 2026-11-10 while the functional v28 build is in progress. These requests
extend the existing task; they do not replace the camera/radio/audio/startup fixes
or the functional-first order. Preserve the native Lineage settings and features.

## Double-tap-to-wake, if genuinely supported

Investigate the fitted Zinitix BT532 firmware/controller wake-gesture protocol.
Current goya driver sets cap->gesture_support=0; the field is otherwise unused.
Its sleep paths disable IRQ and power the controller off (bt532_ts_early_suspend
and bt532_ts_suspend). There is no current wake-gesture implementation or IRQ-wake
path. This establishes that it is not currently implemented, not that the silicon
can never support it. Do not expose a nonfunctional setting.

Use native Lineage/Android gesture settings once real kernel/controller support
exists. Qualification must include screen-off, unplugged suspend and double-tap
wake; success while USB prevents suspend is insufficient. Keep the tested touch,
hardware-navigation and shared-I2C fixes intact. Capability investigation remains
open; no claim that DT2W works yet.

## Recents: native Clear all plus icon before text

The pinned Trebuchet already implements "Clear all":
- quickstep/res/layout/overview_clear_all_button.xml
- quickstep/res/values/strings.xml:recents_clear_all
- quickstep/src/com/android/quickstep/views/RecentsView.java:
  updateClearAllFunction and dismissAllTasks.

Use the standard existing label/action and verify its visibility/reachability on
the tablet before altering layout. Add a matching icon before the text, using
start-relative placement for correct language direction. Preserve accessibility,
theme tint and native task dismissal. The same native button becomes "Back" in
filtered Recents, so update the icon for that state too rather than leaving a
misleading clear/delete icon. No duplicate close-all implementation is needed.
