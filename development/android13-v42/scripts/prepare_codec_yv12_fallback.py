"""Adapt only Codec2's known YV12 path to the measured API0.1 mapper."""
from pathlib import Path
import difflib,hashlib,json,sys
p=Path(sys.argv[1]);t=Path(sys.argv[2]);root=t/'frameworks/av';f=root/'media/codec2/vndk/C2AllocatorGralloc.cpp'
header=(p/'work/device/samsung/t110_bringup/graphics/T110Yv12Layout.h').read_text();h=f.parent/'T110Yv12Layout.h'
before=f.read_text()
if '#include "T110Yv12Layout.h"' in before:
    assert h.read_text()==header;print('CODEC_YV12_ALREADY_APPLIED');raise SystemExit(0)
after=before.replace('#include <mutex>\n','#include <mutex>\n#include <android-base/properties.h>\n#include "T110Yv12Layout.h"\n',1)
old='''            status_t err = GraphicBufferMapper::get().lockYCbCr(
                    const_cast<native_handle_t*>(mBuffer), grallocUsage, rect, &ycbcrLayout);
            if (err) {
                ALOGE("failed transaction: lockYCbCr (err=%d)", err);
'''
new='''            status_t err = GraphicBufferMapper::get().lockYCbCr(
                    const_cast<native_handle_t*>(mBuffer), grallocUsage, rect, &ycbcrLayout);
            if (err && mFormat == static_cast<uint32_t>(PixelFormat4::YV12) &&
                    base::GetBoolProperty("ro.t110.legacy_gpu", false)) {
                // API0.1 has raw lock but no lock_ycbcr. C2 already owns the
                // full imported dimensions/stride; use Android's YV12 contract.
                t110_yv12_layout sizes;
                if (!t110_compute_yv12_layout(mWidth, mHeight, mStride, &sizes)) {
                    return C2_CORRUPTED;
                }
                void* pointer = nullptr;
                err = GraphicBufferMapper::get().lock(
                        const_cast<native_handle_t*>(mBuffer), grallocUsage, rect, &pointer);
                if (!err) {
                    if (!pointer) {
                        GraphicBufferMapper::get().unlock(mBuffer);
                        return C2_CORRUPTED;
                    }
                    ycbcrLayout = {};
                    ycbcrLayout.y = pointer;
                    ycbcrLayout.cr = static_cast<uint8_t*>(pointer) + sizes.y_size;
                    ycbcrLayout.cb = static_cast<uint8_t*>(ycbcrLayout.cr) + sizes.c_size;
                    ycbcrLayout.ystride = sizes.y_stride;
                    ycbcrLayout.cstride = sizes.c_stride;
                    ycbcrLayout.chroma_step = 1;
                }
            }
            if (err) {
                ALOGE("failed transaction: lockYCbCr (err=%d)", err);
'''
assert after.count(old)==1;after=after.replace(old,new)
diff=''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/media/codec2/vndk/C2AllocatorGralloc.cpp',tofile='b/media/codec2/vndk/C2AllocatorGralloc.cpp'))
diff+='diff --git a/media/codec2/vndk/T110Yv12Layout.h b/media/codec2/vndk/T110Yv12Layout.h\nnew file mode 100644\n'
diff+=''.join(difflib.unified_diff([],header.splitlines(True),fromfile='/dev/null',tofile='b/media/codec2/vndk/T110Yv12Layout.h'))
pf=p/'patches/0084-codec2-t110-standard-yv12-raw-lock.patch'
if pf.exists():assert pf.read_text()==diff
else:pf.write_text(diff)
f.write_text(after);h.write_text(header)
(p/'evidence/offline-v41/yv12-source.json').write_text(json.dumps({'patch':pf.name,'before_sha256':hashlib.sha256(before.encode()).hexdigest(),'after_sha256':hashlib.sha256(after.encode()).hexdigest(),'header_sha256':hashlib.sha256(header.encode()).hexdigest(),'scope':'T110 property AND YV12 AND failed native lockYCbCr only','format_source':'https://android.googlesource.com/platform/hardware/interfaces/+/refs/heads/main/graphics/common/1.0/types.hal','hardware_complete_decode_passed':False},indent=2)+'\n')
print('CODEC_YV12_RAW_LOCK_PREPARED')
