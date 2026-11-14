# SM-T110 LineageOS 14.1 — engineering release preparation

Android 7.1.2, ARM32, goyawifi only. Unofficial community work, not an official
LineageOS or Samsung release. Prepared 2026-11-14 from source `ceebd0c9a6c3298765757522f88d75d0bd47b4eb`.

This is an archive/engineering package, **not a TWRP-flashable ZIP or a novice-ready
release**. The image pair has run on one SM-T110. Its system lives in a file on
userdata; the tested tablet's physical SYSTEM partition has read faults. That
hardware fault is specific to the test unit, not a claim about all T110 tablets.

- [XDA title and post](docs/XDA-POST.md)
- [Short social post](docs/SOCIAL-POST.md)
- [Installation and recovery](docs/INSTALLATION.md)
- [Measured feature status](docs/STATUS.md)
- [Downloads, GApps and redistribution](docs/DOWNLOADS.md)
- [Source and credits](docs/SOURCE-AND-CREDITS.md)
- [Release checklist](docs/RELEASE-CHECKLIST.md)
- [Android 10 carryover](docs/LINEAGE17-HANDOFF.md)
- `manifest.json` and `SHA256SUMS.txt`: exact artifact identities
- `tools/verify_package.py`: read-only payload hash/decompression verification

Binary archives are attached to a **draft** GitHub release, tag `t110-lineage14.1-engineering-20261114`. Repository
collaborators can access the draft; it is not an anonymous public download yet.
This branch holds the source and publication materials. The earlier private
Android 13 backup release remains unpublished and unchanged.

No Google apps, normal-app root installer or personal userdata is included in the
ROM. SELinux is permissive; Android userdata is unencrypted. Do not claim current
security maintenance, production hardening, OTA support or full hardware support.

Payload organization locally: `payload/` contains the installed ROM pair (system
compressed with gzip); `third-party/` contains recovered Odin/TWRP files and
their provenance inventory. Public source Git never contains these large assets.
Third-party binaries are archived privately in the draft, not rehosted publicly.
