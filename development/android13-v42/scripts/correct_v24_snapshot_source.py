"""Apply snapshot conversion at its owned creation point, preserving final fields."""
from pathlib import Path
import subprocess
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
t=Path('/root/t110-build/lineage20')
old=p/'patches/0060-trebuchet-t110-software-task-snapshots.patch'
repo=t/'packages/apps/Trebuchet'
subprocess.run(['git','apply','--reverse','--check',str(old)],cwd=repo,check=True)
subprocess.run(['git','apply','--reverse',str(old)],cwd=repo,check=True)
repo=t/'frameworks/base'
name='packages/SystemUI/shared/src/com/android/systemui/shared/recents/model/ThumbnailData.java'
f=repo/name;s=f.read_text()
assert 'import android.os.Build;' not in s
s=s.replace('import android.hardware.HardwareBuffer;', 'import android.hardware.HardwareBuffer;\nimport android.os.Build;')
needle='''        if (thumbnail == null) {
            Point taskSize = snapshot.getTaskSize();'''
replacement='''        // This device's ViewRoot windows use software Canvas. Convert the
        // owned snapshot wrapper before publishing it to Recents consumers.
        if (thumbnail != null && "t110_bringup".equals(Build.DEVICE)
                && thumbnail.getConfig() == Bitmap.Config.HARDWARE) {
            Bitmap hardwareThumbnail = thumbnail;
            thumbnail = hardwareThumbnail.copy(ARGB_8888, false);
            hardwareThumbnail.recycle();
        }
        if (thumbnail == null) {
            Point taskSize = snapshot.getTaskSize();'''
assert needle in s;s=s.replace(needle,replacement);f.write_text(s)
new=p/'patches/0060-systemui-shared-t110-software-task-snapshots.patch'
new.write_bytes(subprocess.check_output(['git','diff','--',name],cwd=repo))
subprocess.run(['git','apply','--reverse','--check',str(new)],cwd=repo,check=True)
build=p/'scripts/build_system_image.sh';s=build.read_text()
s=s.replace('packages/apps/Trebuchet:0060-trebuchet-t110-software-task-snapshots.patch',
            'frameworks/base:0060-systemui-shared-t110-software-task-snapshots.patch')
build.write_text(s)
# Keep the superseded trial patch clearly out of the active patch set.
retired=p/'evidence/offline-v34/superseded-task-thumbnail-view.patch'
old.replace(retired)
print('SNAPSHOTS_CONVERTED_AT_CREATION; TREBUCHET_SOURCE_RESTORED')
