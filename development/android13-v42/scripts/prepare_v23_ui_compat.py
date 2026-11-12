"""Prepare the combined widget-service and window-rendering compatibility fix."""
from pathlib import Path
import json
import subprocess

p = Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
t = Path('/root/t110-build/lineage20')
repo = t/'frameworks/base'
name = 'core/java/android/view/ViewRootImpl.java'
file = repo/name
old = file.read_text()
needle = '''        // Don't enable hardware acceleration when the application is in compatibility mode
        if (mTranslator != null) return;
'''
addition = '''        // The T110's stock EGL driver corrupts normal HWUI window frames and can
        // abort in swapBuffers. Use the existing software View/Canvas path for
        // this engineering device, as already validated by its setup activity.
        // SurfaceView, direct GLES clients and SurfaceFlinger remain separate.
        // Keep this opt-in under the existing exported device compatibility flag.
        if (SystemProperties.getBoolean("ro.t110.legacy_gpu", false)) {
            if (mAttachInfo.mThreadedRenderer != null) {
                mAttachInfo.mThreadedRenderer.destroy();
                mAttachInfo.mThreadedRenderer = null;
            }
            Log.i(mTag, "T110 window rendering: software Canvas for " + attrs.getTitle());
            return;
        }

'''
assert old.count(needle) == 1
if 'T110 window rendering: software Canvas' not in old:
    file.write_text(old.replace(needle, addition+needle))
patch = p/'patches/0058-framework-t110-software-window-rendering.patch'
patch.write_bytes(subprocess.check_output(['git','diff','--',name],cwd=repo))
subprocess.run(['git','apply','--reverse','--check',str(patch)],cwd=repo,check=True)
product = p/'work/device/samsung/t110_bringup/t110_system.mk'
s = product.read_text()
if 'android.software.app_widgets.xml' not in s:
    s += '''
# Trebuchet requires the framework widget service. Without this declaration,
# SystemServer omits it and the launcher loader repeatedly crashes.
PRODUCT_COPY_FILES += \\
    frameworks/native/data/etc/android.software.app_widgets.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/android.software.app_widgets.xml \\
    frameworks/native/data/etc/android.hardware.touchscreen.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/android.hardware.touchscreen.xml
'''
product.write_text(s)
build = p/'scripts/build_system_image.sh'
s = build.read_text()
item = "'frameworks/base:0058-framework-t110-software-window-rendering.patch'"
if item not in s:
    needle = "'packages/apps/SetupWizard:0057-setupwizard-configurable-canvas-rendering.patch'"
    assert s.count(needle) == 1
    s = s.replace(needle, needle+' '+item)
build.write_text(s)
e = p/'evidence/offline-v33'
e.mkdir(parents=True,exist_ok=True)
(e/'source-change.json').write_text(json.dumps(dict(
    status='SOURCE_PREPARED_NOT_BUILT',
    base_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip(),
    fixes=['Start AppWidgetService using its canonical feature declaration',
           'Use software Canvas for T110 ViewRoot windows; direct GLES remains unchanged',
           'Declare confirmed basic touchscreen capability'],
    limitations=['This is a UI compatibility fallback, not a repaired accelerated HWUI driver',
                 'Hardware-only app content and performance still need runtime validation'],
    navigation_buttons='Deferred until graphics/startup work, per user request'
),indent=2)+'\n')
print('V23_COMBINED_UI_SOURCE_PREPARED')
