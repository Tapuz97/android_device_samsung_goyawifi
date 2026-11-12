/* Copyright 2026. Licensed under the Apache License, Version 2.0. */
package org.lineageos.t110.wallpapers;

import android.service.wallpaper.WallpaperService;
import android.content.SharedPreferences;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Rect;
import android.app.WallpaperColors;
import android.view.SurfaceHolder;
import android.util.Log;

/** A static image, posted only on image/surface/visibility changes. No animation loop. */
public final class StaticWallpaperService extends WallpaperService {
    @Override public Engine onCreateEngine() { return new StaticEngine(); }
    private final class StaticEngine extends Engine implements SharedPreferences.OnSharedPreferenceChangeListener {
        private Bitmap bitmap;
        private SharedPreferences preferences;
        @Override public void onCreate(SurfaceHolder holder) {
            super.onCreate(holder);
            setTouchEventsEnabled(false); setOffsetNotificationsEnabled(false);
            preferences = getSharedPreferences("wallpaper", MODE_PRIVATE);
            preferences.registerOnSharedPreferenceChangeListener(this);
            load();
        }
        private void load() {
            if (bitmap != null) bitmap.recycle();
            BitmapFactory.Options options = new BitmapFactory.Options();
            options.inPreferredConfig = Bitmap.Config.ARGB_8888;
            bitmap = BitmapFactory.decodeFile(new java.io.File(getFilesDir(), "current.png").getPath(), options);
            if (bitmap == null) {
                options.inSampleSize = 2;
                try (java.io.InputStream input = getAssets().open("ascension_ice.jpg")) {
                    bitmap = BitmapFactory.decodeStream(input, null, options);
                } catch (java.io.IOException ex) { Log.e("T110Wallpapers", "Default image", ex); }
            }
        }
        @Override public void onSharedPreferenceChanged(SharedPreferences prefs, String key) {
            load(); draw();
        }
        @Override public void onVisibilityChanged(boolean visible) { if (visible) draw(); }
        @Override public void onSurfaceChanged(SurfaceHolder holder, int format, int width, int height) { draw(); }
        @Override public void onSurfaceRedrawNeeded(SurfaceHolder holder) { draw(); }
        @Override public WallpaperColors onComputeColors() {
            return bitmap == null ? null : WallpaperColors.fromBitmap(bitmap);
        }
        private void draw() {
            SurfaceHolder holder = getSurfaceHolder();
            if (!holder.getSurface().isValid()) return;
            Canvas canvas = null;
            try {
                canvas = holder.lockCanvas();
                if (canvas != null) {
                    canvas.drawColor(Color.rgb(16, 24, 28));
                    if (bitmap != null) canvas.drawBitmap(bitmap, null,
                            new Rect(0, 0, canvas.getWidth(), canvas.getHeight()), new Paint(Paint.FILTER_BITMAP_FLAG));
                }
            } catch (RuntimeException ex) { Log.w("T110Wallpapers", "Surface not ready", ex); }
            finally { if (canvas != null) holder.unlockCanvasAndPost(canvas); }
        }
        @Override public void onDestroy() {
            preferences.unregisterOnSharedPreferenceChangeListener(this);
            if (bitmap != null) bitmap.recycle();
            super.onDestroy();
        }
    }
}
