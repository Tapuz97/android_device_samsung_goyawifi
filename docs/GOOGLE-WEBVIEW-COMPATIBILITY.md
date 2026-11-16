# Google sign-in drawing on the GC1000

Status: full platform and Google images built, checked and installed. The
Google account page now draws cleanly; the owner confirmed "Clean buttons;
Next is blue" on the physical tablet. The owner subsequently reported Google sign-in and Play Store use working;
no specific installed app was named or independently recorded.

The physical RGB/BGR mismatch is a separate confirmed issue, now corrected by
matching the native visual through RenderEngine and libEGL. All four physical
test colours were confirmed, and the permanent image booted with BGRA buffers.
Nevertheless modern Google sign-in still corrupts rounded buttons/clipped areas.

## Standard drawing fallback

WebView.onAttachedToWindow selects View.LAYER_TYPE_SOFTWARE only when all match:
- Build.DEVICE is goyawifi;
- the context package is com.google.android.gms;
- the current process is com.google.android.gms.ui;
- persist.t110.suw_sw is true (default true for this compatibility condition).

Normal windows, native SystemUI/launcher/Settings and other apps remain GPU
accelerated. Google APKs, signatures, account callbacks, TLS checks, hosted HTML
and login credentials are not modified. A complete platform build regenerates
the paired boot classpath ART/OAT files and dependent app preoptimization.

## Rejected diagnostics

The three earlier WebView flags did not remove the artifacts. Adding
--disable-gpu / --disable-gpu-compositing made Google's UI process crash. Those
flags were immediately rolled back. They are NOT a valid drawing fallback.
Chromium logged the flags being read, so this was not an ignored file.

Frida17.23.2 native attachment worked, but its Java bridge7.0.13 timed out on the
Android7 UI process. That process was stopped, its error dialog restarted, and
the diagnostic server stopped. Do not repeat this unsupported live Java probe
or treat it as evidence that software drawing was exercised. Temporary tool
file deletion was blocked by automatic approval review; no deletion is claimed.

## Setup progress and Skip

Saved Wi-Fi automatically rejoined after reboot and certificate-checked HTTPS
returned204. Event logs showed Google OtaUpdateActivity / EarlyUpdate finish
and hand off to MinuteMaidActivity. This is not evidence that a ROM update was
downloaded/installed; the verified local system and unchanged boot remained.

The blank Google-hosted account page has its own Skip at bottom-left and Next
at bottom-right. The existing resource-only overlay changes the SIM page's
button, not this hosted page. Do NOT claim the requested account-page Skip
position has been fixed. Preserve this remaining UI requirement explicitly.

Authentication and Play Store app installation remain unqualified. Keep the
accepted modernized ROM available and never write the faulty physical SYSTEM.

## Installed-image verification

Google raw SHA256:
d0f6500e24f0807ca5660b3467c1db5baee3437dca50b003481268535b512028

Full boot and exact native-library/boot-framework readback passed. The runtime
logged the software-draw layer in the Google UI process. The compositor remains
Vivante GC1000 accelerated. Native icon/Settings/navigation/lock checks passed,
and original Google APKs remain intact. Experimental Chromium switches are
reverted. HTTPS connectivity returned204 after startup settled.

The SIM-page resource overlay was exercised: Skip bounds were x460..570,
y949..1009 on the 600x1024 logical display, and its original action advanced
setup. This does not relocate the hosted account page's separate Skip control.

A BootAnimation native exit SIGSEGV was recorded during this boot. The system
continued to the working Google form; a clean animation-exit result is not
claimed. This startup cleanup fault remains separate work. Normal app root,
Google sign-in/Play use are owner-reported working; the broader final-edition
functional suite remains incomplete.

Final release preparation: see release-final/docs/TEST-STATUS.md and UPLOAD-MAP.md. No additional tablet flash was performed.
