// Present shareable Vivante client targets without the stock in-process EGL HWC.
#define LOG_TAG "T110Framebuffer"
#include "T110Framebuffer.h"
#include <initializer_list>
#include "T110Scanout.h"
#include <hardware/gralloc.h>
#include <log/log.h>
#include <cerrno>
#include <cstdio>
#include <fcntl.h>
#include <mutex>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <unistd.h>

namespace {
// SM-T110's PXA ION ABI differs from modern ion_fd_data. The five 32-bit
// fields and command number come from this kernel's linux/pxa_ion.h.
struct IonCacheRegion {
    int32_t fd;
    uint32_t handle, offset, length, direction;
};
static_assert(sizeof(IonCacheRegion) == 20);
constexpr unsigned long kIonSync = _IOWR('I', 7, IonCacheRegion);
static_assert(kIonSync == 0xc0144907);
struct Device {
    framebuffer_device_t fb{}; // First member, as required by the HAL ABI.
    const gralloc_module_t* gralloc = nullptr;
    int fd = -1;
    void* pixels = MAP_FAILED;
    fb_fix_screeninfo fixed{};
    fb_var_screeninfo mode{};
    uint64_t frames = 0;
    int lastError = 0;
    bool blanked = false;
    std::mutex mutex;
    ~Device() {
        if (pixels != MAP_FAILED) munmap(pixels, fixed.smem_len);
        if (fd >= 0) ::close(fd);
    }
};

int post(framebuffer_device_t* fb, buffer_handle_t buffer) {
    auto* d = reinterpret_cast<Device*>(fb);
    std::lock_guard<std::mutex> guard(d->mutex);
    auto fail = [&](int error) {
        if (d->lastError != error) ALOGE("T110 scanout failed: %d", error);
        d->lastError = error;
        return error;
    };
    // Exact stock gralloc ABI, derived from gc_gralloc_alloc/register/lock.
    // Only ION-backed, linear RGBA/RGBX allocations requested by our libui
    // client-target path are accepted. Never dereference a transported pointer.
    if (!buffer || buffer->version != sizeof(native_handle_t) ||
        buffer->numFds != 2 || buffer->numInts != 34) return fail(-EINVAL);
    const auto* words = reinterpret_cast<const uint32_t*>(buffer);
    if (!t110::validPortraitAllocation(words)) return fail(-EINVAL);

    void* source = nullptr;
    int error = d->gralloc->lock(d->gralloc, buffer, GRALLOC_USAGE_SW_READ_OFTEN,
                                 0, 0, t110::kLogicalWidth, t110::kLogicalHeight, &source);
    if (error) return fail(error);
    // gc_gralloc_lock only waits on the legacy GPU signal; its cache flush is
    // in unlock, AFTER a CPU reader has already consumed the old cache lines.
    // Invalidate the shared allocation before reading completed GPU writes.
    IonCacheRegion region{static_cast<int32_t>(words[3]), 0, 0, words[7], 2};
    if (ioctl(static_cast<int>(words[4]), kIonSync, &region) < 0) {
        const int syncError = -errno;
        d->gralloc->unlock(d->gralloc, buffer);
        return fail(syncError);
    }
    // Two pages suffice; choose the page that is not currently scanned out.
    const uint32_t page = d->mode.yoffset == 0 ? d->mode.yres : 0;
    bool copied = t110::copyPortraitFrame(d->pixels, d->fixed.smem_len, d->fixed, d->mode,
                                  page, source, words[7], words[16]);
    int unlockError = d->gralloc->unlock(d->gralloc, buffer);
    if (!copied) return fail(-EINVAL);
    if (unlockError) return fail(unlockError);
    __sync_synchronize();
    fb_var_screeninfo next = d->mode;
    next.yoffset = page;
    next.activate = FB_ACTIVATE_VBL;
    if (ioctl(d->fd, FBIOPAN_DISPLAY, &next) < 0) return fail(-errno);
    d->mode = next;
    ++d->frames;
    d->lastError = 0;
    if (d->frames == 1) ALOGI("T110 first client frame copied and panned to fb0");
    return 0;
}
int enableScreen(framebuffer_device_t* fb, int enable) {
    auto* d = reinterpret_cast<Device*>(fb);
    std::lock_guard<std::mutex> guard(d->mutex);
    if (enable != 0 && enable != 1) return -EINVAL;
    // FBIOBLANK takes the blank level directly, not a pointer. This is the
    // checked PXA fb driver's runtime-PM blank/unblank entrypoint.
    const int level = enable ? FB_BLANK_UNBLANK : FB_BLANK_POWERDOWN;
    if (ioctl(d->fd, FBIOBLANK, level) < 0) {
        const int error = -errno;
        ALOGE("T110 framebuffer power transition failed: enable=%d error=%d", enable, error);
        return error;
    }
    d->blanked = !enable;
    ALOGI("T110 framebuffer power: %s", enable ? "on" : "off");
    return 0;
}
int closeDevice(hw_device_t* device) {
    delete reinterpret_cast<Device*>(device);
    return 0;
}
void dump(framebuffer_device_t* fb, char* text, int size) {
    auto* d = reinterpret_cast<Device*>(fb);
    std::lock_guard<std::mutex> guard(d->mutex);
    if (size > 0) snprintf(text, size, "T110 direct fb0 scanout: frames=%llu yoffset=%u error=%d blanked=%d\n",
                          static_cast<unsigned long long>(d->frames), d->mode.yoffset, d->lastError,
                          static_cast<int>(d->blanked));
}
} // namespace

framebuffer_device_t* openT110Framebuffer() {
    auto* d = new Device;
    const hw_module_t* module = nullptr;
    if (hw_get_module(GRALLOC_HARDWARE_MODULE_ID, &module)) { delete d; return nullptr; }
    d->gralloc = reinterpret_cast<const gralloc_module_t*>(module);
    d->fd = open("/dev/graphics/fb0", O_RDWR | O_CLOEXEC);
    if (d->fd < 0 || ioctl(d->fd, FBIOGET_FSCREENINFO, &d->fixed) < 0 ||
        ioctl(d->fd, FBIOGET_VSCREENINFO, &d->mode) < 0 ||
        !t110::validFramebuffer(d->fixed, d->mode)) {
        ALOGE("T110 framebuffer open/geometry check failed"); delete d; return nullptr;
    }
    d->pixels = mmap(nullptr, d->fixed.smem_len, PROT_READ | PROT_WRITE, MAP_SHARED, d->fd, 0);
    if (d->pixels == MAP_FAILED) { delete d; return nullptr; }
    d->fb.common.tag = HARDWARE_DEVICE_TAG;
    d->fb.common.version = 1;
    d->fb.common.module = const_cast<hw_module_t*>(module);
    d->fb.common.close = closeDevice;
    const_cast<uint32_t&>(d->fb.width) = t110::kLogicalWidth;
    const_cast<uint32_t&>(d->fb.height) = t110::kLogicalHeight;
    const_cast<int&>(d->fb.stride) = t110::kLogicalWidth;
    const_cast<int&>(d->fb.format) = HAL_PIXEL_FORMAT_RGBA_8888;
    const_cast<float&>(d->fb.xdpi) = 160.0f;
    const_cast<float&>(d->fb.ydpi) = 160.0f;
    const_cast<float&>(d->fb.fps) = 60.0f;
    const_cast<int&>(d->fb.minSwapInterval) = 1;
    const_cast<int&>(d->fb.maxSwapInterval) = 1;
    const_cast<int&>(d->fb.numFramebuffers) = 2;
    d->fb.post = post;
    d->fb.enableScreen = enableScreen;
    d->fb.dump = dump;
    ALOGI("T110 natural portrait presenter ready; final panel rotation=270; PXA ION sync enabled");
    return &d->fb;
}
