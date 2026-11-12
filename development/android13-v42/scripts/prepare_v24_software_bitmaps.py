"""Align launcher icons, cache decoding and recents with T110 software windows."""
from pathlib import Path
import subprocess
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
t=Path('/root/t110-build/lineage20')
repo=t/'frameworks/libs/systemui'
base=repo/'iconloaderlib/src/com/android/launcher3/icons'
f=base/'BitmapRenderer.java';s=f.read_text()
needle='    boolean USE_HARDWARE_BITMAP = Build.VERSION.SDK_INT >= Build.VERSION_CODES.P;'
replacement='''    // T110 engineering windows use software Canvas. Keep generated UI images
    // CPU-readable as well; a hardware Bitmap aborts drawing on that Canvas.
    // Build.DEVICE is public API, including for the SDK-only iconloader_base.
    boolean USE_HARDWARE_BITMAP = Build.VERSION.SDK_INT >= Build.VERSION_CODES.P
            && !"t110_bringup".equals(Build.DEVICE);'''
assert needle in s
s=s.replace(needle,replacement)
needle='''        if (Build.VERSION.SDK_INT >= VERSION_CODES.O && source.getConfig() == Config.HARDWARE) {
            return createHardwareBitmap'''
replacement='''        if (Build.VERSION.SDK_INT >= VERSION_CODES.O && source.getConfig() == Config.HARDWARE) {
            if (!USE_HARDWARE_BITMAP) {
                Bitmap readable = source.copy(Config.ARGB_8888, false);
                if (readable == null) {
                    throw new IllegalStateException("Cannot read hardware bitmap for software UI");
                }
                return Bitmap.createBitmap(readable, x, y, width, height);
            }
            return createHardwareBitmap'''
assert needle in s;s=s.replace(needle,replacement);f.write_text(s)
f=base/'cache/BaseIconCache.java';s=f.read_text()
needle='import com.android.launcher3.icons.BitmapInfo;'
assert needle in s
s=s.replace(needle,needle+'\nimport com.android.launcher3.icons.BitmapRenderer;')
s=s.replace('decodeOptions.inPreferredConfig = Config.HARDWARE;',
            'decodeOptions.inPreferredConfig = BitmapRenderer.USE_HARDWARE_BITMAP\n                        ? Config.HARDWARE : Config.ARGB_8888;')
needle='Bitmap hwMonoBitmap = monoBitmap.copy(Config.HARDWARE, false /*isMutable*/);'
assert needle in s
s=s.replace(needle,'''Bitmap hwMonoBitmap = BitmapRenderer.USE_HARDWARE_BITMAP
                        ? monoBitmap.copy(Config.HARDWARE, false /*isMutable*/) : null;''')
f.write_text(s)
names=['iconloaderlib/src/com/android/launcher3/icons/BitmapRenderer.java',
       'iconloaderlib/src/com/android/launcher3/icons/cache/BaseIconCache.java']
patch=p/'patches/0059-iconloader-t110-software-bitmaps.patch'
patch.write_bytes(subprocess.check_output(['git','diff','--']+names,cwd=repo))
subprocess.run(['git','apply','--reverse','--check',str(patch)],cwd=repo,check=True)
repo=t/'packages/apps/Trebuchet'
name='quickstep/src/com/android/quickstep/views/TaskThumbnailView.java'
f=repo/name;s=f.read_text()
needle='import com.android.launcher3.'
pos=s.index(needle)
s=s[:pos]+'import com.android.launcher3.icons.BitmapRenderer;\n'+s[pos:]
needle='''        mTask = task;
        boolean thumbnailWasNull = mThumbnailData == null;'''
replacement='''        mTask = task;
        // Snapshots arrive as hardware bitmaps even when this device's window
        // uses software Canvas. Convert once before constructing its shader.
        if (!BitmapRenderer.USE_HARDWARE_BITMAP && thumbnailData != null
                && thumbnailData.thumbnail != null
                && thumbnailData.thumbnail.getConfig() == Bitmap.Config.HARDWARE) {
            thumbnailData.thumbnail = thumbnailData.thumbnail.copy(Bitmap.Config.ARGB_8888, false);
        }
        boolean thumbnailWasNull = mThumbnailData == null;'''
assert needle in s;s=s.replace(needle,replacement);f.write_text(s)
patch=p/'patches/0060-trebuchet-t110-software-task-snapshots.patch'
patch.write_bytes(subprocess.check_output(['git','diff','--',name],cwd=repo))
subprocess.run(['git','apply','--reverse','--check',str(patch)],cwd=repo,check=True)
build=p/'scripts/build_system_image.sh';s=build.read_text()
needle="'frameworks/base:0058-framework-t110-software-window-rendering.patch'"
assert needle in s
s=s.replace(needle,needle+" 'frameworks/libs/systemui:0059-iconloader-t110-software-bitmaps.patch' 'packages/apps/Trebuchet:0060-trebuchet-t110-software-task-snapshots.patch'")
build.write_text(s)
(p/'evidence/offline-v34/launcher-candidate').mkdir(parents=True,exist_ok=True)
print('V24_SOFTWARE_BITMAP_COMPATIBILITY_PREPARED')
