# Posting checklist and attachment map

Prepared, **not posted to XDA**. GitHub assets are in a draft release. Publish
that draft before pasting the post: the final asset URLs in XDA-POST.md become
public only when the draft is published. This is an experimental engineering
release with no independent second-device clean-install qualification.

Use XDA-TITLE.txt as the title. Paste XDA-POST.md into a Markdown-capable editor
or XDA-POST-BBCODE.txt into XenForo's BBCode mode. Check preview and links.

## Public attachments / GitHub release assets

- Google-free ROM ZIP in PUBLIC.
- Google build-kit ZIP in PUBLIC (scripts, hash manifests and our resource-only
  overlay; no Google APK payload).
- Guide-and-tools ZIP in PUBLIC.
- SHA256SUMS-PUBLIC.txt, TEST-STATUS.md and the source-branch link.

Large ROMs should be linked to the versioned GitHub assets from the XDA post.
Keep the download filenames unchanged so the checksum and post URLs match.

## Keep local

The complete Google-enabled ROM and retained TWRP/Odin/driver toolkit are in
LOCAL-ONLY. The public post supplies original recovery/Odin/driver/GApps links.
Do not accidentally upload LOCAL-ONLY, private Google/account logs, userdata,
device identifiers, Wi-Fi files or the development-only installers.

## Status that must remain explicit

- Same modernized interface and colour fix in both editions; no return to the
  original old icons/UI.
- Google sign-in/Play Store success is owner-reported; no specific app name was
  supplied. Do not invent one or call all functional tests complete.
- Bluetooth audio/accessories/GPS and other unqualified rows remain unqualified.
- BootAnimation native exit fault and the unfinished account-page Skip position
  are disclosed. App root and OTA are not advertised as working.
- The public manual install procedure requires matching SM-T110 geometry and
  userdata container layout. Neither ROM archive is a TWRP/Odin flashable ZIP.

The development tablet remains on its working Google edition. This preparation
does not flash, reset, root or capture that tablet again.
