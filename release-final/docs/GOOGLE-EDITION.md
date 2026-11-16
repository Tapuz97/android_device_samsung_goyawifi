# Build the Google edition on your computer

The local complete Google-enabled ROM is kept for the maintainer. Public
attachments include a build kit rather than mirrored Google APKs, following
[OpenGApps' no-mirror policy](https://opengapps.org/blog/post/2016/03/18/the-no-mirror-policy/).

This release uses **OpenGApps ARM / 7.1 / pico / 20220215**. Do not substitute
ARM64, Android10/13 GApps or an unrelated MindTheGapps package. Our actual tested
input, including original signatures, is pinned:

```text
open_gapps-arm-7.1-pico-20220215.zip
bytes: 190611834
SHA256: 8c26062b0a54b6b6433e9cce11d76a6a12c13cc8fc3dcaee5875af1662a4b74b
```

[Download the original ZIP](https://sourceforge.net/projects/opengapps/files/arm/20220215/open_gapps-arm-7.1-pico-20220215.zip/download).

Extract the Google build kit into a folder on Linux or Ubuntu under WSL. Keep
the whole kit together; it includes our resource-only setup overlay and the
expected native/Google payload hashes. Install the small host tools if absent:

```bash
sudo apt-get update
sudo apt-get install python3 lzip e2fsprogs
```

Allow about8GiB free temporary storage. No Android source checkout, emulator,
tablet connection or firmware write is needed for assembly. In the kit folder:

```bash
python3 make_google_edition.py \
  --rom /path/to/SM-T110-Lineage14.1-Modernized-20261116-without-Google-apps.zip \
  --gapps /path/to/open_gapps-arm-7.1-pico-20220215.zip \
  --output /path/to/SM-T110-Lineage14.1-Modernized-20261116-with-Google-apps.zip
```

The script refuses wrong inputs or existing output filenames. It verifies every
native file and symlink, all selected Google file hashes, filesystem integrity
and SELinux labels. It never modifies Google's APKs or replaces our launcher,
keyboard, WebView, icons or wallpapers. The optional overlay only moves the
original SIM-page Skip; it is not a separate launcher/workaround app.

The resulting archive is still a **computer transport archive**. Install it
using INSTALLATION.md, not TWRP's ZIP installer. Do not flash the upstream
OpenGApps ZIP directly: a generic GApps installer does not understand this
userdata-backed system layout.

Filesystem timestamps can change a locally generated raw-image checksum. The
builder writes its new checksum into manifest.json and a verification receipt;
all native/Google file contents must still match the pinned tested payload.
Use your generated manifest's checksum for on-device readback checks.

Choose the Google edition before initial setup. Switching editions on an
existing installation needs a separate clean isolated data profile; preserve
the previous profile rather than formatting all userdata. Setup/account
verification must be performed on the tablet by its owner. Do not provide
credentials to diagnostics or publish their screenshots/logs.
