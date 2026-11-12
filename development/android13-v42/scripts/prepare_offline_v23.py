"""Install and archive the window bridge and ART lock-scope fix. No device access."""
from pathlib import Path
import subprocess

project = Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
root = Path('/root/t110-build/lineage20')
repo = root / 'frameworks/native'
path = repo / 'libs/renderengine/gl/GLESRenderEngine.cpp'
s = path.read_text()
if '#include "T110EglWindow.h"' not in s:
    anchor = '#include "GLESRenderEngine.h"'
    assert s.count(anchor) == 1
    s = s.replace(anchor, anchor + '\n#include "T110EglWindow.h"')
    s = s.replace('if (!extensions.hasNoConfigContext()) {',
                  'if (!extensions.hasNoConfigContext() || property_get_bool("ro.t110.legacy_gpu", false)) {', 1)
    old = '''    glScissor(region.left, region.top, region.getWidth(), region.getHeight());'''
    assert s.count(old) == 1
    s = s.replace(old, '''    const int y = mT110WindowHeight ? mT110WindowHeight - region.bottom : region.top;
    glScissor(region.left, y, region.getWidth(), region.getHeight());''')
    anchor = '    validateOutputBufferUsage(buffer->getBuffer());\n'
    assert s.count(anchor) == 1
    s = s.replace(anchor, anchor + '''
    const bool legacyT110 = property_get_bool("ro.t110.legacy_gpu", false);
    mT110WindowHeight = 0;
    std::unique_ptr<T110EglWindow> legacyWindow;
    if (legacyT110) {
        if (isProtected() || std::any_of(layers.begin(), layers.end(), [](const auto& layer) {
                return layer.backgroundBlurRadius > 0;
            })) {
            resultPromise->set_value({INVALID_OPERATION, base::unique_fd()});
            return;
        }
        legacyWindow = std::make_unique<T110EglWindow>(mEGLDisplay, mEGLConfig, mEGLContext,
                                                       mStubSurface, buffer->getBuffer());
        if (legacyWindow->status() != NO_ERROR) {
            resultPromise->set_value({legacyWindow->status(), base::unique_fd()});
            return;
        }
        mT110WindowHeight = buffer->getBuffer()->getHeight();
    }
''')
    anchor = '    if (blurLayersSize == 0) {\n'
    assert s.count(anchor) == 1
    s = s.replace(anchor, '''    if (legacyWindow) {
        setViewportAndProjection(display.physicalDisplay, display.clip);
        // FBO targets use a top-row memory convention. An EGL window uses the
        // GL bottom-left convention; mirror projection and scissor together.
        mState.projectionMatrix = mat4(vec4(1, -1, 1, 1)) * mState.projectionMatrix;
        glViewport(display.physicalDisplay.left,
                   mT110WindowHeight - display.physicalDisplay.bottom, mVpWidth, mVpHeight);
    } else if (blurLayersSize == 0) {
''')
    start = s.index('    // This legacy driver has no native fences. Detaching the EGLImage-backed')
    end = s.index('    base::unique_fd drawFence = flush();', start)
    s = s[:start] + '''    if (legacyWindow) {
        const status_t result = legacyWindow->finish();
        legacyWindow.reset();
        mT110WindowHeight = 0;
        mLastDrawFence = nullptr;
        mPriorResourcesCleaned = false;
        resultPromise->set_value({result, base::unique_fd()});
        return;
    }

''' + s[end:]
    path.write_text(s)
s = path.read_text()
s = s.replace('mat4::scale(vec3(1, -1, 1))', 'mat4(vec4(1, -1, 1, 1))')
if s != path.read_text():
    path.write_text(s)
path = repo / 'libs/renderengine/gl/GLESRenderEngine.h'
s = path.read_text()
if 'mT110WindowHeight' not in s:
    s = s.replace('    friend class BindNativeBufferAsFramebuffer;',
                  '    friend class BindNativeBufferAsFramebuffer;\n    int mT110WindowHeight = 0;')
    path.write_text(s)
path = repo / 'libs/renderengine/Android.bp'
s = path.read_text()
if 'gl/T110EglWindow.cpp' not in s:
    s = s.replace('        "gl/GLESRenderEngine.cpp",',
                  '        "gl/GLESRenderEngine.cpp",\n        "gl/T110EglWindow.cpp",')
    path.write_text(s)
for name in ['T110EglWindow.cpp', 'T110EglWindow.h', 'T110WindowSlots.h']:
    (repo / 'libs/renderengine/gl' / name).write_bytes((project / 'work' / name).read_bytes())

files = ['libs/renderengine/Android.bp', 'libs/renderengine/gl/GLESRenderEngine.cpp',
         'libs/renderengine/gl/GLESRenderEngine.h'] + [
         'libs/renderengine/gl/' + n for n in ['T110EglWindow.cpp', 'T110EglWindow.h', 'T110WindowSlots.h']]
parts = []
for file in files:
    if subprocess.run(['git','cat-file','-e','HEAD:'+file],cwd=repo,capture_output=True).returncode == 0:
        parts.append(subprocess.check_output(['git','diff','HEAD','--',file],cwd=repo))
    else:
        parts.append(subprocess.run(['git','diff','--no-index','--','/dev/null',file],cwd=repo,
                                    stdout=subprocess.PIPE).stdout)
(project/'patches/0038-renderengine-t110-egl-window-bridge.patch').write_bytes(b''.join(parts))

repo = root / 'art'
path = repo / 'runtime/runtime.cc'
s = path.read_text()
old = '''    ScopedObjectAccess soa(Thread::Current());
    // Ensure we call FixupStaticTrampolines on all methods that are
    // initialized.
    class_linker_->MakeInitializedClassesVisiblyInitialized(soa.Self(), /*wait=*/ true);
    // Update native method JNI entrypoints.'''
new = '''    Thread* self = Thread::Current();
    // Class visibility may wait for another thread's checkpoint. Do not hold
    // the mutator lock while waiting: the callback needs mutator access and
    // Barrier::Increment correctly rejects waiting with this lock held.
    {
      ScopedThreadStateChange tsc(self, ThreadState::kWaitingForCheckPointsToRun);
      class_linker_->MakeInitializedClassesVisiblyInitialized(self, /*wait=*/ true);
    }
    ScopedObjectAccess soa(self);
    // Update native method JNI entrypoints.'''
if new not in s:
    assert s.count(old) == 1
    path.write_text(s.replace(old, new))
(project/'patches/0039-art-zygote-visibility-checkpoint-lock.patch').write_bytes(
    subprocess.check_output(['git','diff','HEAD','--','runtime/runtime.cc'],cwd=repo))
subprocess.run(['git','diff','--check'],cwd=repo,check=True)
print('V23 sources prepared; no hardware validation claimed')
