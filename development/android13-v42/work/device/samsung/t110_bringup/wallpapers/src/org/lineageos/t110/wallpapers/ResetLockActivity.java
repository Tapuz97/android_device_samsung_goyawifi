package org.lineageos.t110.wallpapers;

/** Private recovery action for a separate static lock image retained by Android. */
public final class ResetLockActivity extends android.app.Activity {
    @Override public void onCreate(android.os.Bundle state) {
        super.onCreate(state);
        try {
            android.app.WallpaperManager.getInstance(this).clear(android.app.WallpaperManager.FLAG_LOCK);
            android.util.Log.i("T110Wallpapers", "Separate lock wallpaper cleared");
        } catch (java.io.IOException ex) {
            android.util.Log.e("T110Wallpapers", "Lock wallpaper reset failed", ex);
        } finally { finish(); }
    }
}
