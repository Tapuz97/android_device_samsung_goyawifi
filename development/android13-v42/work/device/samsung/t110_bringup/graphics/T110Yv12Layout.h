// SPDX-License-Identifier: Apache-2.0
#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

struct t110_yv12_layout {
    size_t y_stride, c_stride, y_size, c_size, total_size;
};

/* Android YV12: even dimensions, 16-byte row alignment, then Cr and Cb. */
static inline bool t110_compute_yv12_layout(uint32_t width, uint32_t height,
        uint32_t stride, struct t110_yv12_layout* out) {
    if (!out || !width || !height || ((width | height) & 1) ||
            stride < width || (stride & 15)) return false;
    size_t y_stride = stride;
    size_t c_stride = ((size_t)stride / 2 + 15) & ~(size_t)15;
    if (height > SIZE_MAX / y_stride || height / 2 > SIZE_MAX / c_stride) return false;
    size_t y_size = y_stride * height;
    size_t c_size = c_stride * (height / 2);
    if (c_size > (SIZE_MAX - y_size) / 2) return false;
    out->y_stride = y_stride;
    out->c_stride = c_stride;
    out->y_size = y_size;
    out->c_size = c_size;
    out->total_size = y_size + c_size * 2;
    return true;
}
