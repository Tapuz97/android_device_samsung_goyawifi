/* Copyright 2026. Licensed under the Apache License, Version 2.0. */
package org.lineageos.t110.wallpapers;

import android.app.Activity;
import android.app.WallpaperManager;
import android.os.Bundle;
import android.content.ComponentName;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.RectF;
import android.util.DisplayMetrics;
import android.util.Log;
import android.view.View;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;
import java.io.InputStream;
import java.io.FileOutputStream;

/** Static CPU-prepared wallpapers for the legacy display stack. No background service. */
public final class WallpaperActivity extends Activity {
    private final String[] files = {"ascension_teal_dark", "ascension_blaze", "ascension_ice",
            "ascension_mist", "ascension_shade", "ascension_sunset", "ascension_teal_light"};
    private final String[] names = {"Teal", "Sunset", "Ice", "Mist", "Shade", "Coral", "Sea"};
    private TextView status;
    private boolean applying;
    private final java.util.concurrent.ExecutorService thumbnails =
            java.util.concurrent.Executors.newSingleThreadExecutor();
    private int dp(int value) { return Math.round(value * getResources().getDisplayMetrics().density); }

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        ScrollView scroll = new ScrollView(this);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(16), dp(20), dp(16), dp(20));
        scroll.addView(root);
        TextView title = new TextView(this);
        title.setText("Wallpapers"); title.setTextSize(28);
        root.addView(title);
        status = new TextView(this);
        status.setText("Choose a background for your home and lock screens");
        status.setPadding(0, dp(10), 0, dp(18)); root.addView(status);
        LinearLayout row = null;
        for (int i = 0; i < files.length; i++) {
            if (i % 3 == 0) { row = new LinearLayout(this); root.addView(row); }
            LinearLayout cell = new LinearLayout(this); cell.setOrientation(LinearLayout.VERTICAL);
            LinearLayout.LayoutParams cellParams = new LinearLayout.LayoutParams(0, -2, 1);
            cellParams.setMargins(dp(4), dp(4), dp(4), dp(12)); row.addView(cell, cellParams);
            ImageView image = new ImageView(this);
            image.setScaleType(ImageView.ScaleType.CENTER_CROP);
            image.setContentDescription(names[i]);
            cell.addView(image, new LinearLayout.LayoutParams(-1, dp(155)));
            final String imageFile = files[i];
            thumbnails.execute(() -> {
                try (InputStream input = getAssets().open(imageFile + ".jpg")) {
                    BitmapFactory.Options opts = new BitmapFactory.Options();
                    opts.inSampleSize = 4; opts.inPreferredConfig = Bitmap.Config.ARGB_8888;
                    Bitmap thumbnail = BitmapFactory.decodeStream(input, null, opts);
                    runOnUiThread(() -> {
                        if (!isDestroyed()) image.setImageBitmap(thumbnail);
                        else if (thumbnail != null) thumbnail.recycle();
                    });
                } catch (Exception ex) { Log.e("T110Wallpapers", "Thumbnail", ex); }
            });
            TextView label = new TextView(this); label.setText(names[i]); label.setTextSize(16);
            label.setPadding(0, dp(5), 0, 0); cell.addView(label);
            final int index = i; cell.setOnClickListener(v -> apply(index));
            cell.setFocusable(true); cell.setContentDescription(names[i] + " wallpaper");
        }
        setContentView(scroll);
    }

    @Override public void onDestroy() {
        thumbnails.shutdownNow();
        super.onDestroy();
    }

    private void apply(int index) {
        if (applying) return;
        applying = true; status.setText("Applying " + names[index] + "…");
        DisplayMetrics real = new DisplayMetrics();
        getWindowManager().getDefaultDisplay().getRealMetrics(real);
        final int width = real.widthPixels, height = real.heightPixels;
        new Thread(() -> {
            Bitmap source = null, output = null;
            try (InputStream input = getAssets().open(files[index] + ".jpg")) {
                BitmapFactory.Options opts = new BitmapFactory.Options();
                opts.inPreferredConfig = Bitmap.Config.ARGB_8888;
                source = BitmapFactory.decodeStream(input, null, opts);
                if (source == null) throw new IllegalStateException("Image unavailable");
                output = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888);
                float scale = Math.max((float) width/source.getWidth(), (float) height/source.getHeight());
                float left = (width-source.getWidth()*scale)/2;
                float top = (height-source.getHeight()*scale)/2;
                Canvas canvas = new Canvas(output);
                canvas.drawBitmap(source, null, new RectF(left, top,
                        left+source.getWidth()*scale, top+source.getHeight()*scale),
                        new Paint(Paint.FILTER_BITMAP_FLAG));
                WallpaperManager manager = WallpaperManager.getInstance(this);
                manager.suggestDesiredDimensions(width, height);
                try (FileOutputStream file = openFileOutput("current.png", MODE_PRIVATE)) {
                    if (!output.compress(Bitmap.CompressFormat.PNG, 100, file))
                        throw new IllegalStateException("Could not save wallpaper");
                }
                getSharedPreferences("wallpaper", MODE_PRIVATE).edit()
                        .putString("selection", files[index]+System.currentTimeMillis()).commit();
                WallpaperManager.class.getMethod("setWallpaperComponent", ComponentName.class)
                        .invoke(manager, new ComponentName(this, StaticWallpaperService.class));
                // Remove a separate static lock image so the selected wallpaper serves both.
                manager.clear(WallpaperManager.FLAG_LOCK);
                Log.i("T110Wallpapers", "Applied " + names[index] + " " + width + "x" + height);
                runOnUiThread(() -> { applying = false;
                    status.setText(names[index] + " applied");
                    Toast.makeText(this, "Wallpaper applied", Toast.LENGTH_SHORT).show();
                });
            } catch (Exception | OutOfMemoryError ex) {
                Log.e("T110Wallpapers", "Apply failed", ex);
                runOnUiThread(() -> { applying = false; status.setText("Could not apply wallpaper. Try again."); });
            } finally {
                if (source != null) source.recycle();
                if (output != null) output.recycle();
            }
        }, "ApplyWallpaper").start();
    }
}
