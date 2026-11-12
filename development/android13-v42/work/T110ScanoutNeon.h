// The T110 presents 32-bit pixels on a native landscape framebuffer.
#pragma once

#include <cstddef>
#include <cstdint>

namespace t110 {
constexpr uint32_t kLogicalWidth = 600;
constexpr uint32_t kLogicalHeight = 1024;
} // namespace t110

#if defined(__ARM_NEON) && __BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__
#include <arm_neon.h>

namespace t110 {
template <bool swapRedBlue>
inline uint8x16_t packScanoutPixels(uint32x4_t pixels, uint32x4_t alpha) {
    if (swapRedBlue) {
        const uint32x4_t red = vandq_u32(pixels, vdupq_n_u32(0xff));
        const uint32x4_t blue = vandq_u32(vshrq_n_u32(pixels, 16), vdupq_n_u32(0xff));
        pixels = vorrq_u32(vandq_u32(pixels, vdupq_n_u32(0xff00)),
                           vorrq_u32(vshlq_n_u32(red, 16), blue));
    } else {
        pixels = vandq_u32(pixels, vdupq_n_u32(0xffffff));
    }
    return vreinterpretq_u8_u32(vorrq_u32(pixels, alpha));
}

// The caller validates geometry and buffer lengths before entering this path.
template <bool swapRedBlue>
inline void transposeScanout(uint8_t* destination, size_t destinationStride,
                             const uint8_t* source, size_t sourceStride, uint32_t opaque) {
    constexpr uint32_t tile = 32;
    static_assert(kLogicalWidth % 4 == 0 && kLogicalHeight % tile == 0);
    const uint32x4_t alpha = vdupq_n_u32(opaque);
    for (uint32_t xTile = 0; xTile < kLogicalWidth; xTile += tile) {
        const uint32_t xEnd = xTile + tile < kLogicalWidth ? xTile + tile : kLogicalWidth;
        for (uint32_t yTile = 0; yTile < kLogicalHeight; yTile += tile) {
            for (uint32_t x = xTile; x < xEnd; x += 4) {
                uint8_t* firstRow = destination + (kLogicalWidth - 1 - x) * destinationStride;
                for (uint32_t y = yTile; y < yTile + tile; y += 4) {
                    const uint8_t* pixels = source + y * sourceStride + x * 4;
                    const uint32x4x2_t ab = vtrnq_u32(vreinterpretq_u32_u8(vld1q_u8(pixels)),
                            vreinterpretq_u32_u8(vld1q_u8(pixels + sourceStride)));
                    const uint32x4x2_t cd = vtrnq_u32(
                            vreinterpretq_u32_u8(vld1q_u8(pixels + 2 * sourceStride)),
                            vreinterpretq_u32_u8(vld1q_u8(pixels + 3 * sourceStride)));
                    const uint32x4_t col0 = vcombine_u32(vget_low_u32(ab.val[0]),
                                                          vget_low_u32(cd.val[0]));
                    const uint32x4_t col1 = vcombine_u32(vget_low_u32(ab.val[1]),
                                                          vget_low_u32(cd.val[1]));
                    const uint32x4_t col2 = vcombine_u32(vget_high_u32(ab.val[0]),
                                                          vget_high_u32(cd.val[0]));
                    const uint32x4_t col3 = vcombine_u32(vget_high_u32(ab.val[1]),
                                                          vget_high_u32(cd.val[1]));
                    uint8_t* output = firstRow + y * 4;
                    vst1q_u8(output, packScanoutPixels<swapRedBlue>(col0, alpha));
                    vst1q_u8(output - destinationStride, packScanoutPixels<swapRedBlue>(col1, alpha));
                    vst1q_u8(output - 2 * destinationStride, packScanoutPixels<swapRedBlue>(col2, alpha));
                    vst1q_u8(output - 3 * destinationStride, packScanoutPixels<swapRedBlue>(col3, alpha));
                }
            }
        }
    }
}
} // namespace t110
#endif
