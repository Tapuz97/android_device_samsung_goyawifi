# Native Lineage icon artwork on the API25 backend

The working Trebuchet branch has no icon-pack manager. This change backports
official Lineage app artwork as ordinary PNG launcher resources inside the
existing applications. It does not replace Camera/Calendar/Gallery or any other
working application with a newer APK, and adds no icon-pack or renderer app.

Thirteen apps: AudioFX, Browser, Calculator, Calendar, Camera, Clock, Contacts,
Email, Files, Gallery, Music, Recorder and Settings. Artwork comes from the
official Lineage repositories (including newer successor apps where appropriate:
Aperture artwork for AOSP Camera2 and Glimpse artwork for Gallery2). Email keeps
the official repository's older artwork, with the same circular normalization.

The original adaptive layers are retained with Git blob IDs, SHA256 provenance,
source copyright notices and available licenses in icon-reference. Their vector
paths, gradients and clipping are converted to SVG at build time and rasterized
with CairoSVG into 48/72/96/144/192-pixel PNGs. A circular 72-unit crop of the
108-unit adaptive canvas gives a consistent native icon shape.

The runtime uses standard Android7 bitmap resources. Native application and
launcher-activity icon references select the new PNG resource IDs; old internal
icon resources remain available. Existing labels, component names, permissions,
application code, widgets and user data are retained.

The older AAPT1 compiler DOES NOT compile XML files under mipmap: an initial
bitmap-XML alias experiment was rejected by actual-package validation and never
installed. Do not restore those aliases. The final approach selects ordinary PNG
resources directly from the application manifests.

verify_native_icons.py checks the APKs extracted from the actual filesystem
image, all 65 density images against source pixels, the compiled manifest icon
ID and the resolved launcher-activity icon paths. The general filesystem,
hardware-library/graphics and app-preservation gates must also pass.

The installer backs up current data, keeps the previous image locally/online
and the original rollback on the tablet. It invalidates only app_icons.db and
its SQLite sidecars while Android is stopped; launcher.db is hash-checked before
and after, preserving Home layouts. Never clear all Trebuchet user data.

Native drawer changes are already physically confirmed: swipe-up opens,
swipe-down closes from the top, and the alphabet footer is absent. The icon image
passed every offline gate and runtime screen inspection. The owner confirmed
that the new icons look correct. Installed raw image SHA256:
fe204df8498ce7dac3e18cc66ae80a9a78c9be12790506dc30df5fee2e66a9c3.
