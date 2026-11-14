from pathlib import Path
import subprocess
r=Path('/root/t110-android13-audit');p=r/'platform/frameworks/base'
f=p/'libs/hwui/renderthread/EglManager.cpp';s=f.read_text()
old='''    if (Properties::enablePartialUpdates) {'''
new='''    // The ANI7 window driver does not provide a reliable retained-pixel
    // contract to modern Skia. Redraw on the GPU rather than assuming an old
    // buffer contains valid pixels. This does not select software Canvas.
    if (Properties::enablePartialUpdates &&
            !property_get_bool("ro.t110.legacy_gpu", false)) {'''
if new not in s:
 assert s.count(old)==1;s=s.replace(old,new)
old='''EGLint EglManager::queryBufferAge(EGLSurface surface) {
    switch'''
new='''EGLint EglManager::queryBufferAge(EGLSurface surface) {
    // Age zero makes CanvasContext expand damage to the complete window.
    if (property_get_bool("ro.t110.legacy_gpu", false)) return 0;
    switch'''
if new not in s:
 assert old in s;s=s.replace(old,new)
old='''    EGLint rects[4];
    frame.map(screenDirty, rects);
    eglSwapBuffersWithDamageKHR(mEglDisplay, frame.mSurface, rects, screenDirty.isEmpty() ? 0 : 1);

    EGLint err = eglGetError();'''
new='''    EGLBoolean swapped = EGL_TRUE;
    if (legacyT110) {
        // Stock window queueing/resolve is the ordinary EGL swap contract.
        // Full GPU redraw above means no retained-pixel/damage hint is needed.
        swapped = eglSwapBuffers(mEglDisplay, frame.mSurface);
    } else {
        EGLint rects[4];
        frame.map(screenDirty, rects);
        eglSwapBuffersWithDamageKHR(mEglDisplay, frame.mSurface, rects, screenDirty.isEmpty() ? 0 : 1);
    }

    EGLint err = eglGetError();
    if (legacyT110 && swapped != EGL_TRUE && err == EGL_SUCCESS) {
        ALOGW("T110 legacy window swap returned false without an EGL error");
        return false;
    }'''
if new not in s:
 assert old in s;s=s.replace(old,new)
f.write_text(s)
f=p/'libs/hwui/pipeline/skia/SkiaOpenGLPipeline.cpp';s=f.read_text()
if '#include <cutils/properties.h>' not in s:s='#include <cutils/properties.h>\n'+s
old='''        const bool preserveBuffer = (swapBehavior != SwapBehavior::kSwap_discardBuffer);'''
new='''        const bool preserveBuffer = (swapBehavior != SwapBehavior::kSwap_discardBuffer) &&
                !property_get_bool("ro.t110.legacy_gpu", false);'''
if new not in s:
 assert old in s;s=s.replace(old,new)
f.write_text(s)
out=r/'device/development/android13-audit-20261114/patches/0003-hwui-t110-full-gpu-window-swap.patch'
out.write_bytes(subprocess.check_output(['git','-C',str(p),'diff','--binary','HEAD']))
subprocess.run(['git','-C',str(p),'diff','--check'],check=True)
subprocess.run(['git','-C',str(p),'apply','--cached','--check',str(out)],check=True)
print('Prepared device-scoped full-GPU-window redraw/swap patch; software fallback remains until image validation.')
