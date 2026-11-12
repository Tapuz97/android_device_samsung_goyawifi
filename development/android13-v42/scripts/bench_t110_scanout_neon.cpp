// Compare complete scanout pages in memory. No pixels are written to fbdev.
#include "T110Scanout.h"
#include <chrono>
#include <cstdio>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <unistd.h>
#include <vector>

template <typename Convert>
static double measure(Convert convert) {
    const auto start = std::chrono::steady_clock::now();
    for (int n = 0; n < 24; ++n) convert();
    return std::chrono::duration<double, std::milli>(
            std::chrono::steady_clock::now() - start).count() / 24;
}

int main() {
    int fd = open("/dev/graphics/fb0", O_RDONLY | O_CLOEXEC);
    fb_fix_screeninfo fix{};
    fb_var_screeninfo var{};
    if (fd < 0 || ioctl(fd, FBIOGET_FSCREENINFO, &fix) ||
            ioctl(fd, FBIOGET_VSCREENINFO, &var) || !t110::validFramebuffer(fix, var)) {
        std::fputs("Could not read native framebuffer layout\n", stderr);
        if (fd >= 0) close(fd);
        return 1;
    }
    close(fd);
    std::printf("native red=%u green=%u blue=%u alpha=%u:%u stride=%u\n",
                var.red.offset, var.green.offset, var.blue.offset, var.transp.offset,
                var.transp.length, fix.line_length);
    const size_t bytes = size_t(fix.line_length) * var.yres;
    const uint32_t sourceStride = 608;
    std::vector<uint8_t> source(size_t(sourceStride) * t110::kLogicalHeight * 4);
    uint32_t seed = 1;
    for (auto& byte : source) {
        seed = seed * 1664525u + 1013904223u;
        byte = seed >> 24;
    }
    for (bool swap : {false, true}) {
        var.red.offset = swap ? 16 : 0;
        var.green.offset = 8;
        var.blue.offset = swap ? 0 : 16;
        for (unsigned alpha : {0u, 8u}) {
            var.transp = {24, alpha, 0};
            std::vector<uint8_t> baseline(bytes * 2 + 32, 0x5a);
            std::vector<uint8_t> neon = baseline;
            auto scalar = [&] {
                return t110::copyPortraitFrame<false>(baseline.data(), baseline.size(), fix, var,
                                               var.yres, source.data(), source.size(), sourceStride);
            };
            auto vectorized = [&] {
                return t110::copyPortraitFrame(neon.data(), neon.size(), fix, var, var.yres,
                                               source.data(), source.size(), sourceStride);
            };
            if (!scalar() || !vectorized()) return 2;
            if (baseline != neon) {
                std::fprintf(stderr, "Mismatch swap=%d alpha=%u\n", swap, alpha);
                return 3;
            }
            const double scalarMs = measure(scalar);
            const double neonMs = measure(vectorized);
            std::printf("swap=%d alpha=%u identical=1 scalar_ms=%.3f neon_ms=%.3f\n",
                        swap, alpha, scalarMs, neonMs);
        }
    }
}
