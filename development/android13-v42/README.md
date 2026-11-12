# SM-T110 Android13 preservation and Nougat source audit

Development checkpoint, not a stable ROM or flashable release. Installed Android13
v42/BOOT48 has unresolved graphics, responsiveness and physical wake failures.
See LINEAGE14-GPU-AND-SLEEP-AUDIT.md for the source audit and hardware gates before
building a complete Android7.1 product. No Nougat boot/runtime PASS is claimed.

This branch retains canonical bring-up source, operator scripts, numbered patches,
the pinned Android13 manifest and exact repo-managed source diffs. Device serial,
eMMC CID and MAC addresses were replaced in the PUBLIC copy. Adapt the device
identity checks before using operator scripts; do not flash another device.

Private original source, logs, stock firmware, Google binaries and current/rollback
images belong in the owner's unpublished draft backup, not this public tree.
The root inherited device product is not silently replaced by this WIP checkpoint.
Do not use the old Android13 build steps as completed Nougat build instructions.

Upstream review: https://review.lineageos.org/c/LineageOS/android_build_soong/+/513083
