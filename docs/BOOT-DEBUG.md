# First Nougat boot investigation

The first installed pair returned directly to TWRP. Generic ADB reboot, explicit
system reboot and TWRP's System action all returned to recovery. Android7 startup
has not been confirmed. Saved last_kmsg shows only the older recovery kernel;
this does not establish whether the normal kernel failed before logging or the
bootloader retained recovery selection. Hardware keys report RELEASE.

Offline comparison found and fixed two definite bootstrap issues:

- The rewritten block lookup lacked the working loader's bounded eMMC readiness
  wait. Restored100 attempts at100ms, immediate success when already ready.
  Five actual-helper fault-injection cases passed ASan/UBSan.
- Standard Nougat /cache is a symlink to /data/cache. The bootstrap requires a
  real /cache mountpoint and rejects symlinks. The packager now creates it and
  asserts every bootstrap mount target is a real directory.

Other changes: load permissive bring-up mode before policy, keep the exact known
header command line, place the matched GPU module on the verified system rather
than duplicating it in ramdisk, and record only a handful of bootstrap checkpoints
after physical userdata mounts. No periodic snapshots or live display feed.
Ramdisk compressed size fell from2461568 to about1490817 bytes. This is a footprint
improvement, not proof of a particular bootloader size limit. Candidate2 still
returned to recovery before writing its userdata checkpoint. The cache-layout
fix is now installed; a physical cold start is pending.

Current boot SHA256 b2de57cb6a7f71eaf97c08fff05b3a6e3a6a4d8a0f7739188806cb206d7cdef6.
Current system SHA25689ef3277c6e059019fbd752c27c57136319c87c65199f7027feb7d7964d527ea.
Both have been verified on the tablet (system during candidate2 install; boot
by full partition read-back). Recovery hash stayed unchanged. Android13 system
backup remains on C and old data/support files remain on the tablet.

The boot-only cache correction reuses the already verified system. Re-running
legacy filesystem normalization changes e2fsck timestamps, so the packager now
accepts an explicitly hash-verified clean raw system for boot-only corrections.
Its actual164 critical/vendor files were rechecked against the final build.
No extra full system transfer was needed for the cache correction.
