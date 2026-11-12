# T110 static wallpapers

Seven existing LineageOS Backgrounds images are offered in a small native picker.
The source artwork is copied unchanged from `LineageOS/android_packages_apps_Backgrounds`,
`res_1080p/drawable-nodpi/ascension_*.jpg`; retain the upstream LineageOS copyright
and Apache License 2.0 notices when redistributing. The Java sources are also Apache 2.0.

This device's normal wallpaper crop produced a completely black 813x1024 image from
a valid 894x1126 blue image. Supplying a CPU-prepared image avoided that corruption,
but the stock ImageWallpaper hardware Canvas path still displayed black. Therefore
this package both prepares a native-size software bitmap and uses a static CPU
WallpaperService. It posts frames on surface/visibility/selection changes, with no
animation timer. It uses about 2.4 MB for its current 600x1024 bitmap.

The picker is platform-signed to select its own wallpaper component through the
framework's component-selection permission; it does not modify framework data files
or require root at runtime. Clearing the separate lock wallpaper makes the selected
component serve both home and lock screens. Fresh installs use Ice from the assets.

`T110Wallpapers` is included in the device product, with the component chosen as its
default. The Windows SDK build helper creates a same-boot development APK from these
same sources; final ROM builds use Android.bp. Real artwork/runtime checks are recorded
under hardware-tests/20261109-settings-wallpaper and evidence/offline-v37/wallpapers.
