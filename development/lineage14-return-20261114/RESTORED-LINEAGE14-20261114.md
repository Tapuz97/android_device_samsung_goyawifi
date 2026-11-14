# Restored working14.1 and returned to UI development

Owner decision on2026-11-14: stop the Android13 compatibility work, restore the
previous working LineageOS14.1 build, and improve its UI. Android13 remains backed
up, not an active build/test target. See [UI direction](LINEAGE14-UI-DIRECTION.md).

## Restored and verified

- Android7.1.2 / SDK25 reports boot completed. New boot ID:
  `77b5b670-acf7-41dd-a498-a49d9972b8af`.
- First completion observed64.1seconds after the host monitor started. This is
  an observation bound, not a precise startup benchmark.
- Owner confirmed the home screen and touch work again.
- Restored system SHA256:
  `01165196d103ecb5939bea6ec367497d956b606ac789178413169fc5f6cb95ea`.
- Restored KERNEL SHA256:
  `93aa73c2cd75efee0441513967a878eb9b92161109d326febc26a61a48b2b0f2`.
- Full decompressed system and KERNEL partition readbacks match the C: images.
- Recovery hash is unchanged:
  `f7f0bcf8a0cee4ecf265a2e1d75de028e97e9401c640e8cbc29d4b256d39452e`.
  Physical SYSTEM was never written. Normal exit used `recovery_done`.
- Original14.1 data was retained at `/data/local/tmp/t110-lineage14-data`; no
  fresh setup or app-data reset was required.
- Audio policy has a real primary output (handle13) after restoration. Audible
  speaker qualification from the earlier installed14.1 media build still stands;
  no new audible confirmation or complete hardware qualification was claimed here.

## Power-button correction

The owner reported that one Power press opened Camera. This repeats the earlier
14.1 shortcut issue documented in the media/suspend tests. Secure setting
`camera_double_tap_power_gesture_disabled` was unset on the restored profile and
is now1. The camera app was left with Home; the owner then confirmed a single
physical Power press turns the screen off. This persists in the user's14.1 data.
No hardware navigation key layout was changed. Raw bounce was not measured, so
do not claim the physical switch is defective based solely on this symptom.

## Preservation and evidence

The old13 tablet system file was compared to the intact C: image before freeing
its space. Android13 source, complete candidate pair, six-asset verified online
backup, private test evidence and its current isolated data directory are kept.
There was no further13 build or boot test.

Working14.1 artifacts and source remain at the original native C: paths, with
both prior image pairs freshly rehashed and source clean. Online14.1 release
444868203 is unchanged. Rollback restored the actual system file as well as
KERNEL; changing KERNEL alone would not have restored the removed tablet file.

Local records: `tests/lineage14-restored-20261114/restore-verification.json`,
`restored-boot-verification.json`, and `restore.log`. Boot crash-buffer capture
did contain one BootAnimation SIGSEGV; normal Home/Settings still ran and the
owner confirmed display/touch. Preserve that fact for the UI/startup audit;
do not report a completely clean crash buffer or silently remove the animation.
The first screencap was black despite subsequent physical confirmation, so it
is not a validated screenshot baseline for visual redesign.

Next: review native14.1 wallpapers, typography, icon sizing, Settings and Quick
Settings resources for a lighter Android13-inspired appearance. Preserve native
Lineage features, hardware/onscreen navigation choices and the corrected Power
preference. No new UI redesign has been installed by this restore.
