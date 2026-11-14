# Full build integration checkpoint

The five complete-project-deltas replace the corresponding original capsule
patches when restoring from the exact pinned upstream HEADs in projects.json.
They include the old source changes plus the phase1/2 graphics fixes and phase3
linker/policy changes. Do not apply them after the old patches, or apply the
earlier incremental patches again. All other capsule project deltas and original
untracked files remain prerequisites. After restoring the capsule, overwrite its
matching files with project-additions/ at the Android checkout root. These are
the actual current custom framebuffer/EGL sources, including changes to files
which upstream Git considers untracked and therefore excludes from git diff.
Their complete hashes are recorded in projects.json. Preserve other capsule
untracked files not represented here.

product/ contains changed source/configuration inputs for the original custom
product. Binary vendor inputs and the stock configuration payload are generated
locally by package_vendor_audio.py from the verified stock image; they are not
published here. Keep original module assets from the private restoration capsule.
The original graphics/radio/navigation source is preserved.

The loader diagnostic is real Android Bionic running under ARM QEMU, with no
hardware access. Its process temporarily sets target SDK22 to diagnose dependency
resolution before the new exact-libippsp textrel exception can be exercised in
production. It has no production namespace configuration; do not report that
diagnostic as a production audio-HAL or SELinux test. Full build results are
recorded separately after the build exits.

REA's pwntools ELF provider could not read this artifact on Windows (Linux x64
host required). ELF/dependency work used ordinary WSL readelf/patchelf tools and
the exact ALSA1.0.23 upstream source alongside real stock-binary loader checks.
No REA retained Evidence or successful native analysis is claimed.
