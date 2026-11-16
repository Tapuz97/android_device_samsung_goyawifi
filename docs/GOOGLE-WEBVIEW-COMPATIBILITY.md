# Google sign-in drawing on the GC1000

Status: source compiled; full platform image and offline gates passed. The
software-layer change still needs a real sign-in rendering check before PASS.

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
