# Current Nougat candidate

Android7.1.2 / LineageOS14.1 has built successfully. Sixteen actual ARM32 graphics
layout assertions,42 selected vendor ELF dependency closures and141 driver-input
hash checks pass. The clean final ext4 copy has164 critical/vendor files extracted
and compared to the installed build. The GPU module is also hash-matched.

The first boot attempts returned to recovery; Android7 startup is NOT confirmed.
See docs/BOOT-DEBUG.md. A missing storage-readiness wait and the standard cache
symlink conflict were corrected. The current boot is installed and awaiting a
physical cold start. These offline results do not establish working hardware.

This is permissive/userdebug, without Google apps. GPS integration and the actual
button LED backend remain pending. Standard Lineage settings/keyboard/launcher/
wallpapers remain; only native physical navigation needs product customization.

- boot.img: 16777216 bytes; SHA256 b2de57cb6a7f71eaf97c08fff05b3a6e3a6a4d8a0f7739188806cb206d7cdef6
- system.raw.img: 1594884096 bytes; SHA256 89ef3277c6e059019fbd752c27c57136319c87c65199f7027feb7d7964d527ea
