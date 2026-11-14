# Owner-requested UI, Google apps and XDA release

Recorded2026-11-14. Active OS: LineageOS14.1 / Android7.1.2, ARM32, SM-T110.

The owner explicitly requested actual publication to XDA after the nicer UI is
finished, with the required Odin, correct T110 TWRP and ROM files. The owner also
requested a Google-apps-enabled edition. This replaces the earlier draft-only
release intent. It does not authorize publishing the current engineering draft
before the UI and release candidates are ready. No XDA post has been submitted.

## Ordered deliverables

1. Finish the native14.1 UI improvements and verify the working hardware,
   navigation and Power preference remain intact.
2. Prepare and qualify a Google-apps-enabled edition, preserving a Google-free
   working baseline. Start with the smallest suitable Google-services set:
   Play Store, Play services and required account/framework components. Retain
   native Lineage applications/features rather than replacing them by default.
3. Test actual Google sign-in, a Play Store download/install, updates where
   compatible, reboot persistence and memory/responsiveness on this tablet.
   Do not imply that every current Google app supports Android7.1.
4. Qualify the final installation and rollback instructions, matching recovery,
   boot/system pair and host tools. This device uses a userdata-backed system
   file; an ordinary GApps installer must not write the faulty physical SYSTEM.
5. Update the existing XDA title/post, screenshots, credits, feature/limitations
   table, instructions, checksums and exact downloadable files for the final UI
   and Google-apps candidates. Retain the separate app-root qualification request.
6. Publish the final files and actual XDA post under the owner's account when
   the preceding work is complete. This conditional authorization is already
   given; do not repeatedly ask for publication approval. If account sign-in is
   actually needed then, request that access at that point.

## Google apps compatibility and public delivery

Lineage's official legacy table maps14.1/Android7.1 to Open GApps. The initial
candidate is ARM32 /7.1 /pico; its exact version and suitability still require
verification. MindTheGapps10/13 packages are not substitutes for this OS.

The user wants a Google-enabled edition, not an untested link in the guide.
Provide a tested Google-enabled installation for the owner. Investigate upstream
source-integrated/own-build packaging for a public edition and check the actual
component distribution terms before deciding its downloadable form. The Open
GApps project explicitly forbids re-mirroring its official prebuilt packages;
it separately describes making one's own builds under the applicable licenses.
Do not treat an open-source installer as a blanket license to redistribute every
Google APK. If using an upstream prebuilt, link the exact upstream download and
provide a tested loop-aware installation flow rather than re-uploading that ZIP.
Public bundling rights and actual Google integration are not qualified yet.

Primary sources verified2026-11-14:

- https://lineageos.github.io/lineage_wiki/gapps/old/
- https://github.com/opengapps/opengapps
- https://github.com/opengapps/aosp_build
- https://opengapps.org/blog/post/2016/03/18/the-no-mirror-policy/

## XDA file set

- Final UI ROM and matching boot, with versioned SHA256 checksums and sources.
- Google-apps edition or its tested upstream-package installation option, with
  precise OS/architecture/version and a clear statement of the delivered form.
- Correct SM-T110 TWRP and provenance. Exclude the old diagnostic recovery.
- Verified Odin tool/version and accompanying required files; retain upstream
  download references and check its distribution terms before public attachment.
- Required USB driver/ADB references and a complete install/rollback guide.
- Source/kernel links, credits, notices and truthful tested/untested status.

Use XDA attachments where permitted and suitable, with complete versioned release
download links for large payloads or files that should remain upstream. Verify
that a reader can actually download every required file. The current private
engineering toolkit is not automatically cleared for public redistribution.
Never upload personal userdata, Google credentials, private keys or raw private
debug logs. Existing release/docs files and branch-root POST.md are the starting
drafts; rewrite them around the final release rather than posting them unchanged.
