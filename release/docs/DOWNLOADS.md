# Files, provenance and compatibility

## Our ROM

Download the engineering ROM archive and checksums from the draft release after
signing into the repository owner/collaborator account. It contains `boot.img`
and `system.raw.img.gz` with this guide and verifier. Do not select this archive
in Odin or TWRP Install: it is a transport archive, not an update package.

## Recovery and Odin

- Original SM-T110 recovery by gr8nole: https://androidfilehost.com/?fid=23329332407589909
- Developer's Odin 3.07 download: https://androidfilehost.com/?fid=23501681358545965
- Our retained Windows tool was Odin 3.13.1, recovered unchanged from our private
  development backup; the developer's linked 3.07 is a separate version.
- Samsung USB driver: https://developer.samsung.com/android-usb-driver
- Google platform-tools/ADB: https://developer.android.com/tools/releases/platform-tools
- Python: https://www.python.org/downloads/

The private toolkit archive includes retained Odin 3.13.1, its accompanying files,
and the original T110 TWRP tar.md5. The original recovery payload plus zero
padding matches the installed recovery partition; see RECOVERY-PROVENANCE.md.
The old stock-kernel diagnostic is excluded from the toolkit.
Do not flash T210/T111/T113/T116/gauguin recovery or firmware to an SM-T110.
Keep attribution and original licenses. This archive does not grant redistribution
rights for Samsung/Odin/vendor binaries. Public instructions link upstream.

## Google apps

Lineage's historical table maps 14.1/Android 7.1 to **Open GApps**:
https://lineageos.github.io/lineage_wiki/gapps/old/

Candidate selection: **ARM (32-bit), 7.1, pico**. Upstream archive example:
https://sourceforge.net/projects/opengapps/files/arm/20220215/open_gapps-arm-7.1-pico-20220215.zip/download
Project and selector: https://opengapps.org/

This is a candidate by architecture/OS version, NOT a tested installation on our
ROM. Our system is mounted from a read-only userdata file, so a generic recovery
GApps installer may target the wrong /system. Do not flash it using an ordinary
partition-ROM recipe. A loop-aware integration and fresh-data test are pending.
Open GApps explicitly prohibits public mirroring of its prebuilt packages; only
upstream links are included. No GApps bytes are uploaded to this release.

MindTheGapps ARM Android 10 belongs to the future Lineage17.1 project, not this
release. Our preserved MindTheGapps Android13 archive is likewise incompatible.

## Root

The image permits development root ADB. Normal-app root remains a separate task.
No untested SuperSU/Magisk/addonsu package is recommended or bundled. Standard
boot patchers must not be assumed to preserve our custom bootstrap.
