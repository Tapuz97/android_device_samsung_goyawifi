# First complete Nougat candidate

Built Android7.1.2 / LineageOS14.1 from the pinned cm-14.1 manifest. Two complete
build passes succeeded. Sixteen actual ARM32 graphics-layout assertions match
old and new headers. All42 selected vendor ELF dependency closures and141 input
hashes pass. The final raw ext4 image passes e2fsck after normalizing only the
legacy make_ext4fs inode-bitmap padding.163 files extracted from the actual image
match the installed build, including original drivers and core platform/apps.

The candidate has NOT booted on the tablet. It is userdebug/permissive, without
Google apps. GPS integration and the current-kernel button LED backend remain
pending. Native Buttons selection and independent backlight UI plumbing are
implemented, but the T110 LED capability remains hidden until a real backend is
established. Standard Lineage launcher, settings, keyboard and wallpapers remain.
This source branch is an experimental bring-up checkpoint, not an official ROM
release, upstream acceptance or a claim of working hardware.

- boot.img: 16777216 bytes; SHA256 6c66afa96acbe35a31eff324e9927e7465220ee0e6c33ecb5d62c4798bda1bfc
- system.raw.img: 1594884096 bytes; SHA256 8aa82ad2d3d7816f3ed76729d0292e69c7997764c6417a336757e69f9cad8a0b
