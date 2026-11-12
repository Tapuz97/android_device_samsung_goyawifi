#include "T110EglWindow.h"
#include "T110WindowSlots.h"
#include <GLES2/gl2.h>
#include <hardware/gralloc.h>
#include <log/log.h>
#include <sync/sync.h>
#include <system/window.h>
#include <ui/ANativeObjectBase.h>
#include <unistd.h>
#include <array>
#include <cerrno>
#include <cstdarg>

namespace android::renderengine::gl {
namespace {
class TargetWindow final : public ANativeObjectBase<ANativeWindow, TargetWindow, RefBase> {
public:
    explicit TargetWindow(const sp<GraphicBuffer>& target) {
        mBuffers[0] = target;
        std::fill(std::begin(oem), std::end(oem), 0);
        const_cast<int&>(minSwapInterval) = 0;
        const_cast<int&>(maxSwapInterval) = 1;
        const_cast<float&>(xdpi) = const_cast<float&>(ydpi) = 160;
        setSwapInterval = [](ANativeWindow*, int n) { return n >= 0 && n <= 1 ? 0 : -EINVAL; };
        query = queryHook;
        perform = performHook;
        dequeueBuffer = dequeueHook;
        queueBuffer = queueHook;
        cancelBuffer = cancelHook;
        dequeueBuffer_DEPRECATED = [](ANativeWindow* w, ANativeWindowBuffer** b) {
            int fence = -1;
            return dequeueHook(w, b, &fence); // This window never returns an acquire fence.
        };
        lockBuffer_DEPRECATED = [](ANativeWindow* w, ANativeWindowBuffer* b) {
            auto* self = getSelf(w);
            int slot = self->find(b);
            return slot >= 0 && self->mSlots.dequeued(slot) ? 0 : -EINVAL;
        };
        queueBuffer_DEPRECATED = [](ANativeWindow* w, ANativeWindowBuffer* b) {
            return queueHook(w, b, -1);
        };
        cancelBuffer_DEPRECATED = [](ANativeWindow* w, ANativeWindowBuffer* b) {
            return cancelHook(w, b, -1);
        };
    }
    bool published() const { return mSlots.published(); }
private:
    ~TargetWindow() override = default;
    // Access is serialized by the rendering thread; EGL objects cannot be used
    // concurrently. Strong references outlive all EGL dequeue/queue callbacks.
    std::array<sp<GraphicBuffer>, T110WindowSlots::kCount> mBuffers;
    T110WindowSlots mSlots;
    bool mConnected = false;
    int find(ANativeWindowBuffer* b) const {
        for (size_t i = 0; i != mBuffers.size(); ++i) {
            if (mBuffers[i] && mBuffers[i]->getNativeBuffer() == b) return i;
        }
        return -1;
    }
    static int consumeFence(int fence) {
        if (fence < 0) return 0;
        // Consume ownership even on failure; never publish an unsignalled frame.
        int ret = sync_wait(fence, 3000) < 0 ? -errno : 0;
        close(fence);
        return ret;
    }
    static int dequeueHook(ANativeWindow* w, ANativeWindowBuffer** buffer, int* fence) {
        if (!buffer || !fence) return -EINVAL;
        *buffer = nullptr;
        *fence = -1;
        auto* self = getSelf(w);
        const int slot = self->mSlots.dequeue();
        if (slot < 0) return -EWOULDBLOCK;
        if (!self->mBuffers[slot]) {
            const auto& target = self->mBuffers[0];
            self->mBuffers[slot] = sp<GraphicBuffer>::make(
                    target->getWidth(), target->getHeight(), target->getPixelFormat(), 1,
                    target->getUsage(), "T110 EGL swap spare");
            if (self->mBuffers[slot]->initCheck() != NO_ERROR) {
                self->mBuffers[slot].clear();
                self->mSlots.cancel(slot);
                return -ENOMEM;
            }
        }
        *buffer = self->mBuffers[slot]->getNativeBuffer();
        return 0;
    }
    static int queueHook(ANativeWindow* w, ANativeWindowBuffer* buffer, int fence) {
        int ret = consumeFence(fence);
        if (ret) return ret;
        auto* self = getSelf(w);
        const int slot = self->find(buffer);
        return slot >= 0 && self->mSlots.queue(slot) ? 0 : -EINVAL;
    }
    static int cancelHook(ANativeWindow* w, ANativeWindowBuffer* buffer, int fence) {
        int ret = consumeFence(fence);
        auto* self = getSelf(w);
        const int slot = self->find(buffer);
        if (slot < 0 || !self->mSlots.cancel(slot)) return -EINVAL;
        return ret;
    }
    static int queryHook(const ANativeWindow* w, int what, int* value) {
        if (!value) return -EINVAL;
        const auto* self = getSelf(w);
        const auto& target = self->mBuffers[0];
        switch (what) {
            case NATIVE_WINDOW_WIDTH:
            case NATIVE_WINDOW_DEFAULT_WIDTH: *value = target->getWidth(); break;
            case NATIVE_WINDOW_HEIGHT:
            case NATIVE_WINDOW_DEFAULT_HEIGHT: *value = target->getHeight(); break;
            case NATIVE_WINDOW_FORMAT: *value = target->getPixelFormat(); break;
            case NATIVE_WINDOW_CONCRETE_TYPE: *value = NATIVE_WINDOW_SURFACE; break;
            case NATIVE_WINDOW_MIN_UNDEQUEUED_BUFFERS: *value = 1; break;
            case NATIVE_WINDOW_MAX_BUFFER_COUNT: *value = T110WindowSlots::kCount; break;
            case NATIVE_WINDOW_IS_VALID:
            case NATIVE_WINDOW_LAYER_COUNT: *value = 1; break;
            case NATIVE_WINDOW_TRANSFORM_HINT:
            case NATIVE_WINDOW_STICKY_TRANSFORM:
            case NATIVE_WINDOW_BUFFER_AGE:
            case NATIVE_WINDOW_QUEUES_TO_WINDOW_COMPOSER:
            case NATIVE_WINDOW_CONSUMER_USAGE_BITS:
            case NATIVE_WINDOW_CONSUMER_RUNNING_BEHIND:
            case NATIVE_WINDOW_CONSUMER_IS_PROTECTED:
            case NATIVE_WINDOW_DEFAULT_DATASPACE:
            case NATIVE_WINDOW_DATASPACE: *value = 0; break;
            default: return -EINVAL;
        }
        return 0;
    }
    int dimensions(int width, int height) const {
        return (width == 0 && height == 0) ||
                (width == static_cast<int>(mBuffers[0]->getWidth()) &&
                 height == static_cast<int>(mBuffers[0]->getHeight())) ? 0 : -EINVAL;
    }
    int format(int value) const {
        return value == 0 || value == mBuffers[0]->getPixelFormat() ? 0 : -EINVAL;
    }
    int usage(uint64_t value) const {
        // Imported targets cannot be reallocated. Refuse requests that their
        // producer allocation cannot meet, instead of silently changing ABI.
        constexpr uint64_t required = GRALLOC_USAGE_PROTECTED | GRALLOC_USAGE_HW_RENDER |
                GRALLOC_USAGE_HW_TEXTURE | GRALLOC_USAGE_HW_FB;
        return (value & required & ~mBuffers[0]->getUsage()) == 0 ? 0 : -EINVAL;
    }
    static int performHook(ANativeWindow* w, int operation, ...) {
        auto* self = getSelf(w);
        va_list args;
        va_start(args, operation);
        int ret = 0;
        switch (operation) {
            case NATIVE_WINDOW_API_CONNECT: {
                const int api = va_arg(args, int);
                if (api != NATIVE_WINDOW_API_EGL || self->mConnected) ret = -EINVAL;
                else self->mConnected = true;
                break;
            }
            case NATIVE_WINDOW_API_DISCONNECT:
                if (va_arg(args, int) != NATIVE_WINDOW_API_EGL) ret = -EINVAL;
                else self->mConnected = false;
                break;
            case NATIVE_WINDOW_CONNECT:
            case NATIVE_WINDOW_DISCONNECT: break; // Obsolete pre-API-connect hooks.
            case NATIVE_WINDOW_SET_USAGE:
                ret = self->usage(static_cast<uint32_t>(va_arg(args, int))); break;
            case NATIVE_WINDOW_SET_USAGE64: ret = self->usage(va_arg(args, uint64_t)); break;
            case NATIVE_WINDOW_SET_BUFFER_COUNT: {
                const int count = va_arg(args, int);
                ret = self->mSlots.configure(count == 0 ? T110WindowSlots::kCount : count)
                        ? 0 : -EINVAL;
                break;
            }
            case NATIVE_WINDOW_GET_CONSUMER_USAGE64: {
                auto* usage = va_arg(args, uint64_t*);
                if (usage) *usage = 0;
                else ret = -EINVAL;
                break;
            }
            case NATIVE_WINDOW_SET_BUFFERS_GEOMETRY:
            case NATIVE_WINDOW_SET_BUFFERS_DIMENSIONS:
            case NATIVE_WINDOW_SET_BUFFERS_USER_DIMENSIONS: {
                const int width = va_arg(args, int);
                const int height = va_arg(args, int);
                ret = self->dimensions(width, height);
                if (operation == NATIVE_WINDOW_SET_BUFFERS_GEOMETRY) {
                    int f = self->format(va_arg(args, int));
                    if (!ret) ret = f;
                }
                break;
            }
            case NATIVE_WINDOW_SET_BUFFERS_FORMAT: ret = self->format(va_arg(args, int)); break;
            case NATIVE_WINDOW_SET_BUFFERS_TRANSFORM:
            case NATIVE_WINDOW_SET_BUFFERS_STICKY_TRANSFORM:
                ret = va_arg(args, int) == 0 ? 0 : -EINVAL; break;
            // These metadata are not used by the CPU framebuffer consumer.
            case NATIVE_WINDOW_SET_BUFFERS_TIMESTAMP:
            case NATIVE_WINDOW_SET_BUFFERS_DATASPACE:
            case NATIVE_WINDOW_SET_SURFACE_DAMAGE: break;
            default: ret = -EINVAL; break;
        }
        va_end(args);
        if (ret) ALOGE("T110 EGL window rejected operation %d: %d", operation, ret);
        return ret;
    }
};
} // namespace

struct T110EglWindow::Impl {
    Impl(EGLDisplay d, EGLContext c, EGLSurface s) : display(d), context(c), stub(s) {}
    EGLDisplay display;
    EGLContext context;
    EGLSurface stub;
    EGLSurface surface = EGL_NO_SURFACE;
    sp<TargetWindow> window;
    status_t result = NO_INIT;
    bool current = false;
    bool finished = false;
    ~Impl() {
        if (current) {
            glFinish();
            eglMakeCurrent(display, stub, stub, context);
        }
        if (surface != EGL_NO_SURFACE) eglDestroySurface(display, surface);
        // EGL has released its window/buffer references before our last refs go.
    }
};

T110EglWindow::T110EglWindow(EGLDisplay display, EGLConfig config, EGLContext context,
                            EGLSurface stub, const sp<GraphicBuffer>& target)
      : mImpl(new Impl(display, context, stub)) {
    auto& p = *mImpl;
    if (!target || target->initCheck() != NO_ERROR || target->getLayerCount() != 1 ||
        (target->getUsage() & GRALLOC_USAGE_PROTECTED) ||
        (target->getPixelFormat() != HAL_PIXEL_FORMAT_RGBA_8888 &&
         target->getPixelFormat() != HAL_PIXEL_FORMAT_RGBX_8888)) {
        p.result = BAD_VALUE;
        return;
    }
    // A window must use a real config compatible with the existing context.
    if (!config) {
        p.result = BAD_VALUE;
        return;
    }
    p.window = sp<TargetWindow>::make(target);
    const EGLint attrs[] = {EGL_NONE};
    p.surface = eglCreateWindowSurface(display, config, p.window.get(), attrs);
    if (p.surface == EGL_NO_SURFACE ||
        !eglMakeCurrent(display, p.surface, p.surface, context)) {
        ALOGE("T110 EGL window creation/bind failed: %#x", eglGetError());
        p.result = INVALID_OPERATION;
        return;
    }
    p.current = true;
    glBindFramebuffer(GL_FRAMEBUFFER, 0);
    p.result = glGetError() == GL_NO_ERROR ? NO_ERROR : INVALID_OPERATION;
}

T110EglWindow::~T110EglWindow() = default;
status_t T110EglWindow::status() const { return mImpl->result; }
status_t T110EglWindow::finish() {
    auto& p = *mImpl;
    if (p.result != NO_ERROR || p.finished) return INVALID_OPERATION;
    glFinish();
    if (glGetError() != GL_NO_ERROR) return p.result = INVALID_OPERATION;
    // The window swap is the driver's legacy resolve and queue operation. An
    // FBO unbind alone does not provide this contract on the stock Vivante blob.
    if (!eglSwapBuffers(p.display, p.surface)) {
        ALOGE("T110 EGL window swap failed: %#x", eglGetError());
        return p.result = INVALID_OPERATION;
    }
    glFinish();
    if (glGetError() != GL_NO_ERROR || !p.window->published()) {
        ALOGE("T110 EGL swap did not publish the requested client target");
        return p.result = INVALID_OPERATION;
    }
    if (!eglMakeCurrent(p.display, p.stub, p.stub, p.context)) {
        ALOGE("T110 EGL failed to restore renderer context: %#x", eglGetError());
        return p.result = INVALID_OPERATION;
    }
    p.current = false;
    p.finished = true;
    static bool logged = false;
    if (!logged) {
        ALOGI("T110 EGL window swap published the exact client target");
        logged = true;
    }
    return NO_ERROR;
}
} // namespace android::renderengine::gl
