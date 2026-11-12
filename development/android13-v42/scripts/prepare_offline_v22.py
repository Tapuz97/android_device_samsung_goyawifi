"""Apply device-only rendering fixes and archive reproducible patches. No device access."""
from pathlib import Path
import subprocess

project=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
root=Path('/root/t110-build/lineage20')
repo=root/'frameworks/native'
path=repo/'libs/renderengine/gl/GLESRenderEngine.cpp'
s=path.read_text()
marker='T110 resolved GLES frame before handoff'
if marker not in s:
    anchor='    base::unique_fd drawFence = flush();\n'
    assert s.count(anchor)==1
    s=s.replace(anchor, '''    // This legacy driver has no native fences. Detaching the EGLImage-backed
    // FBO can enqueue the tile-to-linear resolve, so complete it BEFORE the
    // client target is published to the CPU framebuffer presenter.
    static const bool legacyT110 = property_get_bool("ro.t110.legacy_gpu", false);
    if (legacyT110) {
        fbo.reset();
        glFinish();
        const GLenum error = glGetError();
        if (error != GL_NO_ERROR) {
            ALOGE("T110 GLES resolve failed: %#x", error);
            resultPromise->set_value({INVALID_OPERATION, base::unique_fd()});
            return;
        }
        static bool logged = false;
        if (!logged) {
            ALOGI("T110 resolved GLES frame before handoff");
            logged = true;
        }
        mLastDrawFence = nullptr;
        mPriorResourcesCleaned = false;
        resultPromise->set_value({NO_ERROR, base::unique_fd()});
        return;
    }

'''+anchor)
    path.write_text(s)
patch=subprocess.check_output(['git','diff','--','libs/renderengine/gl/GLESRenderEngine.cpp'],cwd=repo)
assert marker.encode() in patch
(project/'patches/0037-renderengine-t110-resolve-before-handoff.patch').write_bytes(patch)

repo=root/'hardware/interfaces'
target=repo/'graphics/composer/2.1/default/T110Framebuffer.cpp'
target.write_bytes((project/'work/T110Framebuffer.cpp').read_bytes())
# Cumulative composer patch replaces 0033, including its newly-added files.
files=['graphics/composer/2.1/default/'+name for name in
       ['Android.bp','service.cpp','T110Framebuffer.cpp','T110Framebuffer.h','T110Scanout.h']]
parts=[]
for f in files:
    if subprocess.run(['git','cat-file','-e','HEAD:'+f],cwd=repo,capture_output=True).returncode==0:
        parts.append(subprocess.check_output(['git','diff','HEAD','--',f],cwd=repo))
    else:
        data=subprocess.run(['git','diff','--no-index','--','/dev/null',f],cwd=repo,stdout=subprocess.PIPE).stdout
        parts.append(data)
patch=b''.join(parts)
assert b'PXA ION read synchronization enabled' in patch
(project/'patches/0036-composer-t110-synchronized-scanout.patch').write_bytes(patch)
print('V22 rendering source prepared; hardware outcome unverified')
