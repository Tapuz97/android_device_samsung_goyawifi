# Display colours and Google setup, 2026-11-16

The owner compared the physical panel with a test card. Google blue (66,133,244)
appeared orange. The screenshot had the correct logical RGB values. Raw scanout
bytes decoded using FBIOGET_VSCREENINFO confirmed a red/blue disagreement.

## Native fix, accelerated path retained

1. On T110, RenderEngine chooses an EGL config whose native visual matches the
   framebuffer HAL (BGRA8888, value5). The legacy driver advertises that visual.
2. In eglCreateWindowSurface, preserve that config's native visual rather than
   inferring RGBA solely from its channel widths. Both have 8-bit RGBA channels.
   This second step is essential: config selection alone left allocations RGBA.

Both changes are guarded by T110_MRVL_LEGACY. No theme recolouring, per-frame
CPU copy, shader swap, kernel rebuild or recurring ioctl is involved. The old
HWUI one-pixel readback flush and native screenshot compatibility are retained.

ARM32 libsurfaceflinger/libEGL builds and DT_NEEDED checks passed. Loading both
libraries changed actual framebuffer allocations from format1 to format5.
Read-only scanout samples then matched the logical RED, GREEN, BLUE and GOOGLE
BLUE values. The owner explicitly confirmed all four physical colours match.
One-time register/FBIOPUT trials were overwritten by later frame posts and are
not part of the fix. A matching default-format field alone is insufficient:
check actual acquired buffers and the physical panel.

## Accounts capability declaration

The product omitted device_admin. Opening Add account called the native policy
service, which returned null when the feature was absent; Settings then crashed
while traversing it. Declare the standard implemented core capabilities in
configs/t110-core-features.xml. After the feature registration/runtime restart,
Add account opened successfully. Do not claim successful Google authentication
or Play Store installation from this fix alone.

## Google setup footer

modern-ui/google-setup-overlay contains a resource-only trusted vendor overlay.
It moves the existing SIM-page Skip button to the bottom-right, retaining target
resource IDs, the original activity and its click handler. The original Google
APK and signatures remain intact. AAPT compilation and the device's idmap
mapping passed. Installed layout and the remaining Google setup steps still
require verification; do not equate one relocated button with every skip path.

Google APKs, private logs and account/network data are not included in source.
Build corrected images from the preserved modernized base; never write this
tablet's faulty physical SYSTEM. Current runtime trial mounts are not a durable
installation. Working accepted images remain unchanged for rollback.
