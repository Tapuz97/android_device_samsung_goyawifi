# Short title
Android 7.1.2 on the Galaxy Tab 3 Lite SM-T110: LineageOS 14.1 progress

# Post
Our old SM-T110 now boots LineageOS 14.1 with working touch, Wi-Fi internet,
camera preview/photos, Bluetooth file transfer and audible speaker playback.
We also captured microphone audio and confirmed one real sleep/wake cycle.

Still experimental: video performance/audio, Bluetooth audio and several other
hardware checks remain. This engineering build uses a userdata-based system image,
so it is not a regular flashable ROM ZIP. GApps and app root are not yet qualified.

We have organized the source, installation notes, checksums and honest test results:
https://github.com/Tapuz97/android_device_samsung_goyawifi/tree/release/lineage14.1-t110-20261114

The binary package is a draft while we qualify clean installation. Next we will
investigate Android10 compatibility while preserving the working Android7 baseline.
