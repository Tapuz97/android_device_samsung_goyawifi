"""Apply the reproduced T110 software notification clip fix and export its patch."""
from pathlib import Path
import difflib,subprocess
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
repo=Path('/root/t110-build/lineage20/frameworks/base')
relative='packages/SystemUI/src/com/android/systemui/statusbar/notification/row/ExpandableView.java'
path=repo/relative
old=path.read_text()
needle='''            mClipRect.set(Integer.MIN_VALUE, top, Integer.MAX_VALUE, bottom);'''
replacement='''            if ("t110_bringup".equals(android.os.Build.DEVICE)) {
                // The raster Canvas can drop this row when an INT_MIN/MAX clip intersects
                // the shade's rounded path. Keep a full viewport of horizontal overflow
                // on each side for shadows, groups and swipe/expansion translations.
                android.util.DisplayMetrics metrics = getResources().getDisplayMetrics();
                int overflow = Math.max(getWidth(),
                        Math.max(metrics.widthPixels, metrics.heightPixels));
                overflow += (int) Math.ceil(Math.max(0f, mExtraWidthForClipping));
                mClipRect.set(-overflow, top, getWidth() + overflow, bottom);
            } else {
                mClipRect.set(Integer.MIN_VALUE, top, Integer.MAX_VALUE, bottom);
            }'''
patch=p/'patches/0076-systemui-t110-finite-notification-clips.patch'
if replacement not in old:
    assert old.count(needle)==1
    new=old.replace(needle,replacement)
    patch.write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),
                     fromfile='a/'+relative,tofile='b/'+relative)))
    subprocess.run(['git','-C',str(repo),'apply','--check',str(patch)],check=True)
    path.write_text(new)
assert replacement in path.read_text()
subprocess.run(['git','-C',str(repo),'apply','--reverse','--check',str(patch)],check=True)
print('T110_FINITE_NOTIFICATION_CLIP_PATCH_APPLIED')
