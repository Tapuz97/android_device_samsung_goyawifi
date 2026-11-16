# T110 Google setup resource overlay

Resource-only Android7 trusted vendor overlay, no launcher, code, permission or
account handler. Install the checked signed APK at /system/vendor/overlay/
T110SetupLayout.apk as part of the optional Google edition. Never install it as
a normal user app: PackageManager scans this trusted path before target APKs.

The development build helper records the current local paths and pinned Google
SetupWizard input SHA. Supply the original upstream input locally; it is not
redistributed in this source tree. Run aapt with the matching framework-res.apk
and the original target APK as resource include files, sign our overlay using
the ROM platform key and check idmap against the original target. Google APK
signing is not changed. See docs/DISPLAY-COLOR-AND-GOOGLE-SETUP.md.
