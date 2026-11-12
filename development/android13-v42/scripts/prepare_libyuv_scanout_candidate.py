"""Prepare a libyuv-based transpose candidate without changing the build tree."""
from pathlib import Path
p=Path(__file__).resolve().parents[1];e=p/'evidence/offline-v39';e.mkdir(exist_ok=True)
old=(p/'work/T110Scanout.h').read_text()
new=old.replace('#include <linux/fb.h>','#include <linux/fb.h>\n#include <libyuv/rotate_argb.h>')
anchor='''    // Small tiles keep both transposed source rows and destination rows hot.
'''
fast='''    // Reuse Android's existing NEON-optimized transpose on the measured panel.
    if (v.red.offset == 16 && v.green.offset == 8 && v.blue.offset == 0 &&
            (v.transp.length == 0 || v.transp.offset == 24)) {
        if (libyuv::ARGBRotate(src, sourceStridePixels * 4, dst, f.line_length,
                kLogicalWidth, kLogicalHeight, libyuv::kRotate270) != 0) return false;
        // ARGBRotate preserves bytes. Apply the panel's channel order and the
        // same fixed alpha as the original presenter in contiguous output rows.
        for (uint32_t y = 0; y < v.yres; ++y) {
            auto* row = reinterpret_cast<uint32_t*>(dst + size_t(y) * f.line_length);
            for (uint32_t x = 0; x < v.xres; ++x) {
                const uint32_t pixel = row[x];
                row[x] = ((pixel & 0x00ff0000u) >> 16) | (pixel & 0x0000ff00u) |
                        ((pixel & 0x000000ffu) << 16) | alpha;
            }
        }
        return true;
    }
'''
assert old.count(anchor)==1
new=new.replace(anchor,fast+anchor)
(e/'T110Scanout-libyuv.h').write_bytes(new.encode())
print('LIBYUV_SCANOUT_CANDIDATE_PREPARED_NOT_APPLIED')
