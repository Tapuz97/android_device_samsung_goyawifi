// T110 CPU scanout: bounds-checked RGBA/RGBX to the measured fbdev layout.
#pragma once
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <initializer_list>
#include <linux/fb.h>
#include "T110ScanoutNeon.h"

namespace t110 {
inline bool validFramebuffer(const fb_fix_screeninfo& f, const fb_var_screeninfo& v) {
    if (v.xres != 1024 || v.yres != 600 || v.bits_per_pixel != 32 ||
        v.xoffset != 0 || v.xres_virtual < v.xres || v.yres_virtual < 1200 ||
        f.type != FB_TYPE_PACKED_PIXELS || f.visual != FB_VISUAL_TRUECOLOR ||
        f.line_length < v.xres * 4 || f.line_length % 4 ||
        !f.ypanstep || v.yres % f.ypanstep ||
        uint64_t(f.line_length) * v.yres_virtual > f.smem_len) return false;
    uint32_t mask = 0;
    for (auto c : {v.red, v.green, v.blue, v.transp}) {
        if (c.length == 0) continue;
        if (c.length != 8 || c.offset > 24 || c.msb_right) return false;
        uint32_t m = 255u << c.offset;
        if (mask & m) return false;
        mask |= m;
    }
    return v.red.length == 8 && v.green.length == 8 && v.blue.length == 8;
}

inline bool copyFrame(void* destination, size_t destinationBytes,
                      const fb_fix_screeninfo& f, const fb_var_screeninfo& v,
                      uint32_t pageY, const void* source, size_t sourceBytes,
                      uint32_t sourceStridePixels) {
    if (!destination || !source || !validFramebuffer(f, v) ||
        pageY % v.yres || uint64_t(pageY) + v.yres > v.yres_virtual ||
        sourceStridePixels < v.xres ||
        uint64_t(sourceStridePixels) * 4 * v.yres > sourceBytes ||
        uint64_t(f.line_length) * (pageY + v.yres) > destinationBytes) return false;
    auto* dst = static_cast<uint8_t*>(destination) + size_t(pageY) * f.line_length;
    const auto* src = static_cast<const uint8_t*>(source);
    const uint32_t alpha = v.transp.length ? (255u << v.transp.offset) : 0;
    for (uint32_t y = 0; y < v.yres; ++y) {
        for (uint32_t x = 0; x < v.xres; ++x) {
            const auto* pixel = src + x * 4;
            uint32_t packed = (uint32_t(pixel[0]) << v.red.offset) |
                              (uint32_t(pixel[1]) << v.green.offset) |
                              (uint32_t(pixel[2]) << v.blue.offset) | alpha;
            memcpy(dst + x * 4, &packed, sizeof(packed));
        }
        src += size_t(sourceStridePixels) * 4;
        dst += f.line_length;
    }
    return true;
}
// Android renders natural portrait. The PXA panel is wired 270 degrees
// from it: logical (x,y) maps to native (y,599-x). Rotate once here,
// after EGL has resolved the complete frame; keep fbdev in its native mode.
// Called only after validating native_handle's version, FD and integer counts.
// These legacy fields hold PADDED allocation dimensions (608 for width600),
// not the logical GraphicBuffer dimensions advertised to Android.
inline bool validPortraitAllocation(const uint32_t* words) {
    return words && words[5] == 0x03141592 && (words[6] & 2) && !(words[6] & 1) &&
           (words[29] & 0x80000000u) && (words[12] == 1 || words[12] == 2) &&
           words[13] >= kLogicalWidth && words[14] >= kLogicalHeight &&
           words[16] >= kLogicalWidth && words[17] >= kLogicalHeight &&
           uint64_t(words[16]) * 4 * kLogicalHeight <= words[7];
}

template <bool enableNeon = true>
inline bool copyPortraitFrame(void* destination, size_t destinationBytes,
                              const fb_fix_screeninfo& f, const fb_var_screeninfo& v,
                              uint32_t pageY, const void* source, size_t sourceBytes,
                              uint32_t sourceStridePixels) {
    if (!destination || !source || !validFramebuffer(f, v) ||
        pageY % v.yres || uint64_t(pageY) + v.yres > v.yres_virtual ||
        sourceStridePixels < kLogicalWidth ||
        uint64_t(sourceStridePixels) * 4 * kLogicalHeight > sourceBytes ||
        uint64_t(f.line_length) * (uint64_t(pageY) + v.yres) > destinationBytes) return false;
    auto* dst = static_cast<uint8_t*>(destination) + size_t(pageY) * f.line_length;
    const auto* src = static_cast<const uint8_t*>(source);
    const uint32_t alpha = v.transp.length ? (255u << v.transp.offset) : 0;
#if defined(__ARM_NEON) && __BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__
    if (enableNeon && v.green.offset == 8 && (!v.transp.length || v.transp.offset == 24)) {
        const size_t stride = size_t(sourceStridePixels) * 4;
        if (v.red.offset == 16 && v.blue.offset == 0) {
            transposeScanout<true>(dst, f.line_length, src, stride, alpha);
            return true;
        }
        if (v.red.offset == 0 && v.blue.offset == 16) {
            transposeScanout<false>(dst, f.line_length, src, stride, alpha);
            return true;
        }
    }
#endif
    // Small tiles keep both transposed source rows and destination rows hot.
    constexpr uint32_t tile = 32;
    for (uint32_t by = 0; by < v.yres; by += tile) {
        const uint32_t ey = by + tile < v.yres ? by + tile : v.yres;
        for (uint32_t bx = 0; bx < v.xres; bx += tile) {
            const uint32_t ex = bx + tile < v.xres ? bx + tile : v.xres;
            for (uint32_t y = by; y < ey; ++y) {
                auto* row = dst + size_t(y) * f.line_length;
                for (uint32_t x = bx; x < ex; ++x) {
                    const auto* pixel = src + (size_t(x) * sourceStridePixels + kLogicalWidth - 1 - y) * 4;
                    const uint32_t packed = (uint32_t(pixel[0]) << v.red.offset) |
                                            (uint32_t(pixel[1]) << v.green.offset) |
                                            (uint32_t(pixel[2]) << v.blue.offset) | alpha;
                    memcpy(row + size_t(x) * 4, &packed, sizeof(packed));
                }
            }
        }
    }
    return true;
}
} // namespace t110
