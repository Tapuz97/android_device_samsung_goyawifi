// Device-only bridge from RenderEngine's target to the legacy EGL window API.
#pragma once
#include <EGL/egl.h>
#include <ui/GraphicBuffer.h>
#include <utils/Errors.h>
#include <memory>

namespace android::renderengine::gl {
class T110EglWindow {
public:
    T110EglWindow(EGLDisplay display, EGLConfig config, EGLContext context,
                  EGLSurface stub, const sp<GraphicBuffer>& target);
    ~T110EglWindow();
    status_t status() const;
    status_t finish();
private:
    struct Impl;
    std::unique_ptr<Impl> mImpl;
};
} // namespace android::renderengine::gl
