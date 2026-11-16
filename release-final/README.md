# SM-T110 Modernized LineageOS 14.1 — 2026-11-16

Android 7.1.2 / API25 / ARM32, for **Samsung SM-T110 (goyawifi) only**.
Both editions keep our modernized native interface, icons, gestures, Settings,
navigation and wallpapers. Both include the permanent RGB/BGR colour fix.

This is an **experimental engineering release**, not an official LineageOS
release or a universal TWRP flashable ZIP. Read INSTALLATION.md before use.
The matching boot image uses a system container on userdata and never writes
physical SYSTEM. Formatting userdata after installation removes this ROM.

## Files

- `PUBLIC/SM-T110-Lineage14.1-Modernized-20261116-without-Google-apps.zip`
  — complete Google-free edition; extract on the computer.
- `PUBLIC/SM-T110-Lineage14.1-Modernized-20261116-Google-build-kit.zip`
  — build the Google edition locally using the exact official upstream ZIP.
- `PUBLIC/SM-T110-Modernized-20261116-Guide-and-tools.zip`
  — post, installation/rollback instructions, verifier and extraction helper.
- `LOCAL-ONLY/LOCAL-ONLY-SM-T110-Lineage14.1-Modernized-20261116-with-Google-apps.zip`
  — complete Google-enabled edition matching the tested installed image.
- `LOCAL-ONLY/third-party/` — retained, checked T110 TWRP and Odin3.13.1/USB-driver
  toolkit. Public post links the original upstream downloads.
- `docs/XDA-POST.md`, `docs/XDA-POST-BBCODE.txt`, `docs/XDA-TITLE.txt` — final post
  formats, ready to paste. `docs/UPLOAD-MAP.md` identifies the public attachments.

Run Python explicitly on Windows so `.py` file associations do not open VS Code:

```powershell
py -3 verify_modern_package.py PUBLIC\SM-T110-Lineage14.1-Modernized-20261116-without-Google-apps.zip
py -3 extract_rom.py PUBLIC\SM-T110-Lineage14.1-Modernized-20261116-without-Google-apps.zip extracted-rom
```

The Google build kit needs Linux/WSL, Python3, `lzip`, `e2fsprogs` and about8GiB
temporary disk space. It does not require an Android source checkout. See
docs/GOOGLE-EDITION.md. Do not flash the upstream GApps ZIP through TWRP for this
loop-image layout.

The owner reported Google sign-in and Play Store use working after confirming
clean buttons and correct colours. No app name or independent Play install
receipt was supplied; this is owner confirmation, not an automated full-suite
result. Remaining hardware checks and a native animation-exit fault are listed
in TEST-STATUS.md. A clean install on a second tablet remains unqualified.

Source: https://github.com/Tapuz97/android_device_samsung_goyawifi/tree/release/lineage14.1-modern-t110-20261116

This folder is release preparation. XDA has not been posted, and the GitHub
release remains a draft until publication. Keep personal logs and Google APK
payloads out of public attachments.
