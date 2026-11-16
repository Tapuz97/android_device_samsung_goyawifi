# Rollback

Keep each system image, its matching KERNEL image, its own Android data profile
and their verified hashes together. Recovery must remain accessible throughout.

1. Enter TWRP and reconnect USB. Verify the same model/partition mapping, mounted
   ext4 userdata and that the loop system is not active.
2. Restore the previous verified system container as the regular file
   `/data/local/tmp/t110-lineage14-system.raw`. Verify its size and SHA256 before
   activating the previous boot. Preserve the failed container/data if useful.
3. Restore the corresponding saved KERNEL to its checked partition p10; hash
   the full partition afterward. Restore the corresponding isolated Android
   data directory, not an incompatible profile from another edition/version.
4. Keep recovery unchanged. Use the established recovery_done handoff for this
   ROM's wrapped boot image.

To return to stock, use **your own** matching stock boot/firmware and a
model-specific stock procedure. The custom installer layout leaves physical
SYSTEM untouched, but an unreadable stock SYSTEM cannot be repaired by restoring
stock boot. Do not assume another region/model's firmware, PIT or EFS is safe.
No full-stock firmware package is provided here or claimed tested by this guide.

Do not format userdata as a troubleshooting shortcut; doing so destroys the
system container and its isolated data. Use a verified host backup if internal
storage space is too limited to hold both versions. Never remove the sole
working rollback copy to make room.
